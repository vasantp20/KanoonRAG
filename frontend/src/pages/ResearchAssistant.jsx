import { useState, useEffect, useRef } from 'react';
import { caseService } from '../api/caseService';
import { queryService } from '../api/queryService';

function ResearchAssistant() {
  const [cases, setCases] = useState([]);
  const [isLoadingCases, setIsLoadingCases] = useState(false);
  const [tabs, setTabs] = useState([]);
  const [activeTabId, setActiveTabId] = useState(null);

  const handleNewLaunchpadTab = () => {
    const newId = Date.now().toString();
    setTabs(prev => [...prev, { id: newId, type: 'launchpad', title: 'New Tab' }]);
    setActiveTabId(newId);
  };

  useEffect(() => {
    let isMounted = true;
    const fetchCases = async () => {
      try {
        const data = await caseService.getAllCases();
        if (isMounted) setCases(data);
      } catch (err) {
        console.error("Failed to fetch cases:", err);
      } finally {
        if (isMounted) setIsLoadingCases(false);
      }
    };
    setIsLoadingCases(true);
    fetchCases();
    return () => { isMounted = false; };
  }, []);

  useEffect(() => {
    if (tabs.length === 0) {
      handleNewLaunchpadTab();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tabs.length]);

  const handleCaseSelect = async (caseItem) => {
    const newId = Date.now().toString();
    setTabs(prev => [...prev, { 
      id: newId, 
      type: 'chat', 
      title: `[Case] ${caseItem.case_type || 'Case'}`, 
      caseId: caseItem.id,
      caseName: caseItem.court_name || 'Legal Case',
      messages: [],
      isAiLoading: true
    }]);
    setActiveTabId(newId);

    try {
      const hist = await queryService.getCaseHistory(caseItem.id);
      const newMessages = [];
      hist.forEach(item => {
        newMessages.push({ role: 'user', content: item.query_text, timestamp: new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) });
        if (item.response_text) {
          newMessages.push({ role: 'ai', content: item.response_text, sources: item.sources_used || [], timestamp: new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) });
        }
      });
      setTabs(prev => prev.map(t => {
        if (t.id === newId) {
          return { ...t, messages: newMessages, isAiLoading: false };
        }
        return t;
      }));
    } catch (err) {
      console.error("Failed to load case history", err);
      setTabs(prev => prev.map(t => {
        if (t.id === newId) {
          return { ...t, isAiLoading: false };
        }
        return t;
      }));
    }
  };

  const closeTab = (e, id) => {
    e.stopPropagation();
    const newTabs = tabs.filter(t => t.id !== id);
    setTabs(newTabs);
    if (activeTabId === id && newTabs.length > 0) {
      setActiveTabId(newTabs[newTabs.length - 1].id);
    }
  };

  const handleSendMessage = async (tabId, messageText) => {
    if (!messageText.trim()) return;

    setTabs(prev => prev.map(t => {
      if (t.id === tabId) {
        return {
          ...t,
          messages: [...t.messages, { role: 'user', content: messageText, timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }]
        };
      }
      return t;
    }));

    // Find the caseId
    const tab = tabs.find(t => t.id === tabId);
    const caseId = tab ? tab.caseId : null;

    try {
      // Add a temporary loading message
      setTabs(prev => prev.map(t => {
        if (t.id === tabId) {
          return {
            ...t,
            isAiLoading: true
          };
        }
        return t;
      }));

      const res = await queryService.sendQuery(messageText, caseId);
      
      setTabs(prev => prev.map(t => {
        if (t.id === tabId) {
          return {
            ...t,
            isAiLoading: false,
            messages: [...t.messages, { role: 'ai', content: res.answer, sources: res.sources }]
          };
        }
        return t;
      }));
    } catch (error) {
      console.error(error);
      setTabs(prev => prev.map(t => {
        if (t.id === tabId) {
          return {
            ...t,
            isAiLoading: false,
            messages: [...t.messages, { role: 'error', content: 'An error occurred while fetching the response.' }]
          };
        }
        return t;
      }));
    }
  };

  const activeTab = tabs.find(t => t.id === activeTabId);

  return (
    <div className="flex flex-col w-full h-full bg-background relative">
      {/* Tabbed Workspace Bar */}
      <div className="flex items-center bg-surface-container-lowest px-4 gap-1 border-b border-outline-variant/30 shrink-0 h-12 z-40">
        {tabs.map((tab) => (
          <div 
            key={tab.id}
            onClick={() => setActiveTabId(tab.id)}
            className={`flex items-center px-4 h-full font-medium text-sm gap-2 cursor-pointer transition-colors group ${activeTabId === tab.id ? 'bg-surface-container-high border-t-2 border-primary text-primary font-semibold' : 'text-on-surface-variant hover:bg-surface-variant/20'}`}>
            <span className="material-symbols-outlined text-[18px]">
              {tab.type === 'launchpad' ? 'tab' : 'gavel'}
            </span>
            {tab.title}
            <span 
              onClick={(e) => closeTab(e, tab.id)}
              className={`material-symbols-outlined text-[16px] ml-1 rounded-full hover:bg-outline-variant/30 ${activeTabId === tab.id ? 'text-on-surface-variant hover:text-white' : 'opacity-0 group-hover:opacity-100'}`}>close</span>
          </div>
        ))}
        <button onClick={handleNewLaunchpadTab} className="p-2 text-on-surface-variant hover:text-primary hover:bg-surface-variant/20 transition-all rounded-full ml-2">
          <span className="material-symbols-outlined">add</span>
        </button>
        <div className="ml-auto flex items-center gap-2 pr-2">
          <button className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-on-surface-variant border border-outline-variant rounded hover:bg-surface-variant/30 transition-all">
            <span className="material-symbols-outlined text-[14px]">vertical_split</span>
            Split View
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab?.type === 'launchpad' && (
          <LaunchpadView cases={cases} onCaseSelect={handleCaseSelect} isLoading={isLoadingCases} />
        )}
        {activeTab?.type === 'chat' && (
          <ChatView tab={activeTab} onSendMessage={(msg) => handleSendMessage(activeTab.id, msg)} />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------
// Launchpad View (Ported from Stitch Design)
// ---------------------------------------------------------
function LaunchpadView({ cases, onCaseSelect, isLoading }) {
  return (
    <div className="w-full h-full overflow-y-auto custom-scrollbar p-12">
      <div className="max-w-6xl mx-auto">
        <div className="mb-12">
          <h2 className="font-display-lg text-[40px] font-bold text-on-surface mb-2">Good Morning, Counselor.</h2>
          <p className="font-body-lg text-lg text-on-surface-variant">Your intellectual chambers are ready. What shall we investigate today?</p>
        </div>

        {/* Central Search Hub */}
        <section className="mb-16">
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 to-primary-container/20 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
            <div className="relative bg-surface-container/65 backdrop-blur-[20px] border border-outline-variant/30 rounded-2xl p-6 shadow-2xl flex items-center gap-4">
              <span className="material-symbols-outlined text-primary text-3xl">search</span>
              <input 
                className="flex-1 bg-transparent border-none text-2xl font-headline-md placeholder:text-outline/40 focus:ring-0 outline-none text-on-surface" 
                placeholder="Search for a case or legal topic..." 
                type="text" 
              />
              <button className="bg-primary text-on-primary font-bold px-8 py-3 rounded-xl flex items-center gap-2 hover:bg-primary-fixed transition-all">
                <span>Analyze</span>
                <span className="material-symbols-outlined text-[20px]">bolt</span>
              </button>
            </div>
          </div>
          <div className="flex items-center justify-center gap-8 mt-6">
            <button className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors font-semibold text-sm">
              <span className="material-symbols-outlined text-[18px]">verified_user</span> Case Law
            </button>
            <button className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors font-semibold text-sm">
              <span className="material-symbols-outlined text-[18px]">gavel</span> Statutes
            </button>
            <button className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors font-semibold text-sm">
              <span className="material-symbols-outlined text-[18px]">menu_book</span> Legal Theory
            </button>
            <button className="flex items-center gap-2 text-on-surface-variant hover:text-primary transition-colors font-semibold text-sm">
              <span className="material-symbols-outlined text-[18px]">travel_explore</span> Jurisdictions
            </button>
          </div>
        </section>

        {/* Recent Cases Section */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-headline-md text-xl font-bold flex items-center gap-2 text-on-surface">
              <span className="material-symbols-outlined text-primary">history</span>
              Recent Cases
            </h3>
            <a className="text-primary text-sm font-bold hover:underline cursor-pointer">View All Research</a>
          </div>
          
          {isLoading ? (
            <div className="text-on-surface-variant">Loading cases...</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {cases.length === 0 ? (
                <div className="text-on-surface-variant col-span-4">No cases found. Create one to get started.</div>
              ) : (
                cases.map(caseItem => (
                  <div 
                    key={caseItem.id}
                    onClick={() => onCaseSelect(caseItem)}
                    className="bg-surface-container rounded-xl p-4 border border-outline-variant/30 hover:border-primary/40 transition-all cursor-pointer group"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <span className="text-[10px] px-2 py-0.5 bg-outline/20 text-on-surface-variant rounded">
                        {caseItem.created_at ? new Date(caseItem.created_at).toLocaleDateString() : 'Just now'}
                      </span>
                      <span className="material-symbols-outlined text-on-surface-variant text-sm group-hover:text-primary">star</span>
                    </div>
                    <h5 className="font-bold text-base mb-1 truncate text-on-surface">{caseItem.case_type}</h5>
                    <p className="text-sm text-outline italic mb-4 truncate">{caseItem.court_name || 'N/A'}</p>
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-primary"></div>
                      <span className="text-[11px] font-semibold text-on-surface-variant uppercase tracking-wider">{caseItem.status}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------
// Chat View
// ---------------------------------------------------------
function ChatView({ tab, onSendMessage }) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const handleSend = () => {
    onSendMessage(inputValue);
    setInputValue('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [tab.messages, tab.isAiLoading]);

  // Extract unique sources for the sidebar from AI messages
  const allSources = [];
  tab.messages.forEach(msg => {
    if (msg.role === 'ai' && msg.sources) {
      msg.sources.forEach(src => {
        if (!allSources.find(s => s.kanoon_doc_id === src.kanoon_doc_id)) {
          allSources.push(src);
        }
      });
    }
  });

  return (
    <div className="flex w-full h-full">
      {/* Chat Area */}
      <section className="flex-1 flex flex-col relative bg-background overflow-hidden border-r border-outline-variant/20">
        {/* Case Context Banner */}
        <div className="flex items-center justify-between px-6 py-2 bg-surface-container-low border-b border-outline-variant/30 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs font-medium text-on-surface-variant uppercase tracking-widest">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
              Active Context
            </div>
            <div className="h-4 w-[1px] bg-outline-variant"></div>
            <p className="font-bold text-on-surface">{tab.title}</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8 pb-20">
          {tab.messages.length === 0 && (
            <div className="text-center text-on-surface-variant mt-20">
              <span className="material-symbols-outlined text-4xl mb-4 text-primary">chat_bubble</span>
              <p>Ask a legal question about this case.</p>
            </div>
          )}

          {tab.messages.map((msg, idx) => (
            <div key={idx}>
              {msg.role === 'user' ? (
                <div className="flex gap-4 max-w-4xl mx-auto justify-end">
                  <div className="space-y-2 max-w-[80%]">
                    <div className="bg-surface-container-high border border-outline-variant/30 p-4 rounded-xl">
                      <p className="font-body-md text-on-surface">{msg.content}</p>
                    </div>
                    <p className="text-[10px] text-on-surface-variant text-right font-semibold">SENT {msg.timestamp}</p>
                  </div>
                  <div className="w-8 h-8 rounded bg-primary-container flex items-center justify-center text-on-primary font-bold text-xs shrink-0">JD</div>
                </div>
              ) : msg.role === 'ai' ? (
                <div className="flex gap-4 max-w-4xl mx-auto">
                  <div className="w-8 h-8 rounded bg-primary-container/20 flex items-center justify-center border border-primary/30 shrink-0">
                    <span className="material-symbols-outlined text-primary text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                  </div>
                  <div className="space-y-4 flex-1">
                    <div className="bg-surface-container-high/65 backdrop-blur-[20px] border border-outline-variant/30 p-5 rounded-xl shadow-lg">
                      <p className="font-body-md text-on-surface leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-outline-variant/20 flex flex-wrap gap-2">
                          {msg.sources.map((src, i) => (
                            <div key={i} className="flex items-center gap-1.5 px-2.5 py-1 bg-primary/10 border border-primary/20 rounded text-[11px] text-primary font-bold cursor-pointer hover:bg-primary/20 transition-all">
                              <span className="material-symbols-outlined text-[14px]">description</span>
                              {src.title || src.citation || src.filename}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex gap-4 max-w-4xl mx-auto">
                   <div className="text-error bg-error-container text-on-error-container p-4 rounded-xl text-sm">
                     {msg.content}
                   </div>
                </div>
              )}
            </div>
          ))}

          {tab.isAiLoading && (
            <div className="flex gap-4 max-w-4xl mx-auto">
              <div className="w-8 h-8 rounded bg-primary-container/20 flex items-center justify-center border border-primary/30 shrink-0">
                <span className="material-symbols-outlined text-primary text-[20px] animate-spin">sync</span>
              </div>
              <div className="bg-surface-container-high/65 backdrop-blur-[20px] border border-outline-variant/30 p-4 rounded-xl">
                <p className="text-on-surface-variant text-sm animate-pulse">Analyzing corpus...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 bg-surface-container-lowest border-t border-outline-variant/20 shrink-0 absolute bottom-0 left-0 right-0">
          <div className="max-w-4xl mx-auto relative">
            <textarea 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={tab.isAiLoading}
              className="w-full bg-surface-container border border-outline-variant/40 rounded-xl px-4 py-3 font-body-md focus:ring-1 focus:ring-primary focus:border-primary outline-none resize-none pr-14 custom-scrollbar text-on-surface" 
              placeholder="Ask a legal question or request document analysis..." 
              rows="2"
            ></textarea>
            <div className="absolute right-3 bottom-3 flex items-center gap-2">
              <button className="p-2 text-on-surface-variant hover:text-primary transition-colors">
                <span className="material-symbols-outlined">attach_file</span>
              </button>
              <button 
                onClick={handleSend}
                disabled={tab.isAiLoading || !inputValue.trim()}
                className="p-2 bg-primary text-on-primary rounded-lg active:scale-95 transition-transform disabled:opacity-50 disabled:cursor-not-allowed">
                <span className="material-symbols-outlined">send</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Research Insights Side Panel */}
      <aside className="w-[360px] bg-surface-container-lowest overflow-y-auto custom-scrollbar flex flex-col shrink-0">
        <div className="p-5 border-b border-outline-variant/20 flex items-center justify-between shrink-0">
          <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">insights</span>
            Research Insights
          </h2>
          <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-bold">BETA</span>
        </div>
        <div className="p-5 space-y-8 flex-1">
          {/* Key Fact Extraction (Static placeholder) */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[11px] font-bold text-on-surface-variant uppercase tracking-widest">Case Context</h3>
            </div>
            <div className="space-y-3">
              <div className="p-3 bg-surface-container rounded-lg border-l-2 border-primary/40">
                <p className="text-[11px] text-on-surface-variant font-bold mb-1">CASE NAME</p>
                <p className="text-[13px] text-on-surface">{tab.caseName}</p>
              </div>
            </div>
          </section>

          {/* Relevant Citations */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[11px] font-bold text-on-surface-variant uppercase tracking-widest">Relevant Citations</h3>
              <span className="text-[10px] text-on-surface-variant">{allSources.length} Found</span>
            </div>
            <div className="space-y-2">
              {allSources.length === 0 ? (
                <p className="text-sm text-on-surface-variant italic">No citations retrieved yet.</p>
              ) : (
                allSources.map((src, idx) => (
                  <div key={idx} className="p-3 bg-surface-container-high/65 backdrop-blur-[20px] rounded border border-outline-variant/30 hover:border-primary/50 transition-all cursor-pointer">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-[12px] font-bold text-primary truncate max-w-[80%]">{src.citation || src.kanoon_doc_id || 'Document'}</span>
                      <span className="material-symbols-outlined text-[14px] text-on-surface-variant">open_in_new</span>
                    </div>
                    <p className="text-[13px] font-semibold text-on-surface mb-1 truncate">{src.title}</p>
                    <p className="text-[11px] text-on-surface-variant line-clamp-2">{src.snippet}</p>
                  </div>
                ))
              )}
            </div>
          </section>
        </div>
      </aside>
    </div>
  );
}

export default ResearchAssistant;

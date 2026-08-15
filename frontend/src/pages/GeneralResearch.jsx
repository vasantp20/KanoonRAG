import { useState, useRef, useEffect } from 'react';
import { queryService } from '../api/queryService';

export default function GeneralResearch() {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState([]);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const [history, setHistory] = useState([]);
  const [sessionId, setSessionId] = useState(crypto.randomUUID());

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const sessions = await queryService.getSessions();
      setHistory(sessions);
    } catch (err) {
      console.error("Failed to load sessions", err);
    }
  };

  const loadSessionHistory = async (sid) => {
    try {
      setSessionId(sid);
      const hist = await queryService.getSessionHistory(sid);
      const newMessages = [];
      hist.forEach(item => {
        newMessages.push({ role: 'user', content: item.query_text, timestamp: new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) });
        if (item.response_text) {
          newMessages.push({ role: 'ai', content: item.response_text, sources: item.sources_used || [], timestamp: new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) });
        }
      });
      setMessages(newMessages);
    } catch (err) {
      console.error("Failed to load session history", err);
    }
  };

  const startNewChat = () => {
    setSessionId(crypto.randomUUID());
    setMessages([]);
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage = inputValue;
    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMessage, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
    ]);
    setInputValue('');
    setIsAiLoading(true);

    try {
      // Send query without a caseId for general research, but with sessionId
      const res = await queryService.sendQuery(userMessage, null, sessionId);
      if (res.session_id && res.session_id !== sessionId) {
         setSessionId(res.session_id);
      }
      loadSessions(); // refresh history list
      
      setMessages(prev => [
        ...prev,
        { role: 'ai', content: res.answer, sources: res.sources, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
      ]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [
        ...prev,
        { role: 'error', content: 'An error occurred while fetching the response.', timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
      ]);
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAiLoading]);

  return (
    <div className="flex-1 flex flex-row h-full overflow-hidden relative">
      {/* CHAT HISTORY SIDEBAR */}
      <aside className="w-80 h-full bg-surface-container-low border-r border-outline-variant flex flex-col">
        <div className="px-6 mb-6 mt-6 flex justify-between items-center shrink-0">
          <h2 className="font-label-md text-on-surface-variant tracking-widest uppercase">History</h2>
          <button className="text-on-surface-variant hover:text-primary transition-all">
            <span className="material-symbols-outlined text-[18px]">filter_list</span>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto custom-scrollbar px-3 space-y-2">
          {history.map(item => (
            <div key={item.session_id} onClick={() => loadSessionHistory(item.session_id)} className={`group p-3 rounded-lg hover:bg-surface-container-highest border cursor-pointer transition-all ${sessionId === item.session_id ? 'border-primary bg-primary/5' : 'border-transparent'}`}>
              <div className="flex justify-between items-start mb-1">
                <span className="font-title-md text-on-surface text-sm line-clamp-1">{item.title}</span>
                <span className="text-[10px] font-label-sm text-on-surface-variant">{item.time}</span>
              </div>
              <p className="text-[12px] text-on-surface-variant line-clamp-1 mb-2">{item.desc}</p>
              <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="text-on-surface-variant hover:text-error transition-colors"><span className="material-symbols-outlined text-[16px]">delete</span></button>
                <button className="text-on-surface-variant hover:text-primary transition-colors"><span className="material-symbols-outlined text-[16px]">archive</span></button>
              </div>
            </div>
          ))}
        </div>
      </aside>

      {/* MAIN CHAT AREA */}
      <main className="flex-1 h-full flex flex-col bg-surface relative overflow-hidden">
        {/* Header Section */}
        <div className="px-edge_margin py-4 flex items-center justify-between z-10 border-b border-outline-variant/30 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-2 h-8 bg-primary rounded-full"></div>
            <h2 className="font-headline-lg text-headline-lg text-on-surface">General Research</h2>
          </div>
          <button onClick={startNewChat} className="flex items-center gap-2 bg-primary text-on-primary px-5 py-2.5 rounded-full font-title-md hover:brightness-110 active:scale-95 transition-all shadow-lg shadow-primary/10">
            <span className="material-symbols-outlined">add</span>
            New Chat
          </button>
        </div>

        {/* Chat Content Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-edge_margin py-10 z-10">
          <div className="max-w-4xl mx-auto space-y-8">
            {messages.length === 0 && !isAiLoading && (
              <div className="text-center text-on-surface-variant mt-20">
                <span className="material-symbols-outlined text-4xl mb-4 text-primary">psychology</span>
                <p>Ask a general legal question to explore KanoonRAG's global knowledge base.</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx}>
                {msg.role === 'user' ? (
                  <div className="flex flex-col items-end animate-in fade-in slide-in-from-right-4 duration-500">
                    <div className="bg-surface-container-high border border-outline-variant p-5 rounded-2xl rounded-tr-none max-w-[85%] shadow-sm">
                      <p className="font-body-lg text-on-surface">{msg.content}</p>
                    </div>
                    <span className="font-label-sm text-on-surface-variant mt-2 px-2">{msg.timestamp}</span>
                  </div>
                ) : msg.role === 'ai' ? (
                  <div className="flex flex-col items-start animate-in fade-in slide-in-from-left-4 duration-700">
                    <div className="bg-surface-container-low/65 backdrop-blur-[20px] border border-outline-variant/40 p-6 rounded-2xl rounded-tl-none max-w-[90%] shadow-xl relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
                          <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                        </div>
                        <span className="font-title-md text-primary">KanoonRAG Assistant</span>
                      </div>
                      <div className="space-y-4 font-body-md text-on-surface-variant leading-relaxed whitespace-pre-wrap">
                        {msg.content}
                      </div>

                      {msg.sources && msg.sources.length > 0 && (
                        <div className="bg-surface-container-lowest/50 p-4 rounded-lg border border-outline-variant/30 mt-6">
                          <h4 className="font-label-md text-primary mb-2 flex items-center gap-2">
                            <span className="material-symbols-outlined text-[14px]">menu_book</span> CITATIONS
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[12px]">
                            {msg.sources.map((src, i) => (
                              <a key={i} className="flex items-center gap-2 p-2 rounded bg-surface hover:bg-primary/10 transition-colors border border-transparent hover:border-primary/20 cursor-pointer">
                                <span className="material-symbols-outlined text-primary text-[14px]">link</span>
                                <span className="truncate">{src.citation || src.title || src.kanoon_doc_id || 'Document'}</span>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex gap-4 mt-6 pt-4 border-t border-outline-variant/20">
                        <button className="flex items-center gap-1 text-on-surface-variant hover:text-primary transition-all font-label-md">
                          <span className="material-symbols-outlined text-[18px]">content_copy</span> Copy
                        </button>
                        <button className="flex items-center gap-1 text-on-surface-variant hover:text-primary transition-all font-label-md">
                          <span className="material-symbols-outlined text-[18px]">thumb_up</span>
                        </button>
                        <button className="flex items-center gap-1 text-on-surface-variant hover:text-primary transition-all font-label-md">
                          <span className="material-symbols-outlined text-[18px]">refresh</span> Regenerate
                        </button>
                      </div>
                    </div>
                    <span className="font-label-sm text-on-surface-variant mt-2 px-2">Assistant • {msg.timestamp}</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-start">
                    <div className="bg-error-container text-on-error-container p-4 rounded-xl text-sm">
                      {msg.content}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {isAiLoading && (
              <div className="flex flex-col items-start animate-in fade-in slide-in-from-left-4 duration-700">
                <div className="bg-surface-container-low/65 backdrop-blur-[20px] border border-outline-variant/40 p-6 rounded-2xl rounded-tl-none max-w-[90%] shadow-xl relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-on-primary">
                      <span className="material-symbols-outlined text-[18px] animate-spin" style={{ fontVariationSettings: "'FILL' 1" }}>sync</span>
                    </div>
                    <span className="font-title-md text-primary animate-pulse">Researching corpus...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="px-edge_margin pb-10 pt-4 z-10 shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="bg-surface-container-low/65 backdrop-blur-[20px] border border-outline-variant/30 p-2 rounded-2xl shadow-2xl relative transition-all focus-within:ring-2 focus-within:ring-primary/40 focus-within:border-primary">
              <div className="flex items-end gap-2 px-2 py-2">
                <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-lg hover:bg-primary/10">
                  <span className="material-symbols-outlined">attach_file</span>
                </button>
                <textarea 
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isAiLoading}
                  className="flex-1 bg-transparent border-none focus:ring-0 text-on-surface font-body-lg placeholder:text-on-surface-variant/50 py-2 resize-none custom-scrollbar max-h-40 outline-none" 
                  placeholder="Ask about statutes, case laws, or legal analysis..." 
                  rows="1"
                ></textarea>
                <button 
                  onClick={handleSend}
                  disabled={isAiLoading || !inputValue.trim()}
                  className="bg-primary text-on-primary h-11 px-6 rounded-xl font-title-md flex items-center gap-2 hover:brightness-110 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                  <span>Analyze</span>
                  <span className="material-symbols-outlined">bolt</span>
                </button>
              </div>
              <div className="flex gap-4 px-4 pb-2">
                <div className="flex items-center gap-1 text-[10px] text-on-surface-variant font-label-md">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                  AI Engine: V4-Legal-Elite
                </div>
                <div className="flex items-center gap-1 text-[10px] text-on-surface-variant font-label-md">
                  <span className="material-symbols-outlined text-[12px]">verified_user</span>
                  256-bit Encrypted
                </div>
              </div>
            </div>
            <p className="text-center mt-3 text-[11px] text-on-surface-variant/40">
              KanoonRAG may produce inaccuracies. Always cross-reference with official legal gazettes.
            </p>
          </div>
        </div>
      </main>

      {/* Right Side Panel (Context Info) */}
      <aside className="w-[300px] bg-surface-container-low border-l border-outline-variant px-6 hidden xl:flex flex-col py-6 shrink-0 overflow-y-auto custom-scrollbar">
        <h3 className="font-label-md text-on-surface-variant tracking-widest uppercase mb-6">General Context</h3>
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-surface-container-highest/50 border border-outline-variant/30">
            <h4 className="font-title-md text-primary text-sm mb-2">Subject Entities</h4>
            <div className="flex flex-wrap gap-2">
              <span className="px-2 py-1 rounded bg-primary/10 text-primary text-[10px] border border-primary/20">IT Act 2024</span>
              <span className="px-2 py-1 rounded bg-primary/10 text-primary text-[10px] border border-primary/20">Intermediary Liability</span>
              <span className="px-2 py-1 rounded bg-primary/10 text-primary text-[10px] border border-primary/20">Data Privacy</span>
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="font-label-md text-on-surface-variant uppercase text-[10px]">Suggested Inquiries</h4>
            <button 
              onClick={() => setInputValue("Compare Section 79 before and after 2024 amendment")}
              className="w-full text-left p-3 rounded-lg bg-surface hover:bg-surface-container-highest border border-outline-variant/20 transition-colors group">
              <p className="text-xs text-on-surface group-hover:text-primary">"Compare Section 79 before and after 2024 amendment"</p>
            </button>
            <button 
              onClick={() => setInputValue("List penalties for non-compliance for SMEs")}
              className="w-full text-left p-3 rounded-lg bg-surface hover:bg-surface-container-highest border border-outline-variant/20 transition-colors group">
              <p className="text-xs text-on-surface group-hover:text-primary">"List penalties for non-compliance for SMEs"</p>
            </button>
            <button 
              onClick={() => setInputValue("Draft a summary of safe harbor changes")}
              className="w-full text-left p-3 rounded-lg bg-surface hover:bg-surface-container-highest border border-outline-variant/20 transition-colors group">
              <p className="text-xs text-on-surface group-hover:text-primary">"Draft a summary of safe harbor changes"</p>
            </button>
          </div>

          <div className="mt-8">
            <img 
              className="w-full h-40 object-cover rounded-xl border border-outline-variant/40 grayscale hover:grayscale-0 transition-all duration-700 cursor-pointer" 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCBGfmAXQNcLJeVSNFZ9DoxEt-Zj6SJGaC1fgB8XQ9zdiz3MOC_p1YDhxj_u-990Xen4hfqZAFWLXULeO0dzYBOPibjtDrgGnpYUazhwShHh9LLEOiRWmPPsg5rMtZV8FkMQnm1NK4BnWg8Ougb0tvk1-0-pg0Gmx0uhYzxcP4lCO8yEJ-YexyS9Rqjff5K41XDvaL8K0OSWn_Zp7Lr-GVMI9ljXpGieuSshfHkeC4cHG0gB7n-rNYV" 
              alt="Decorative conceptual art"
            />
            <p className="text-[10px] text-on-surface-variant/60 mt-2 italic">Automated Document Indexing active for 'IT_Laws_Master'</p>
          </div>
        </div>
      </aside>
    </div>
  );
}

import { useState, useRef, useEffect } from 'react';
import { queryService } from '../api/queryService';

export default function GeneralResearch() {
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState([]);
  const [loadingSessionId, setLoadingSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const [history, setHistory] = useState([]);
  const [sessionId, setSessionId] = useState(crypto.randomUUID());
  const isAiLoading = loadingSessionId === sessionId;

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
    const currentSession = sessionId;
    setLoadingSessionId(currentSession);
    
    if (messages.length === 0) {
      setHistory(prev => [
        {
          session_id: currentSession,
          title: userMessage.length > 30 ? userMessage.substring(0, 30) + '...' : userMessage,
          desc: userMessage,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        },
        ...prev
      ]);
    }

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
      setLoadingSessionId(prev => prev === currentSession ? null : prev);
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
    <div className="w-screen h-screen flex flex-row overflow-hidden relative">
      {/* CHAT HISTORY SIDEBAR */}
      <aside className="w-80 h-full bg-surface-container-low border-r border-outline-variant flex flex-col z-50">
        <div className="px-6 py-6 mb-2 flex items-center gap-3">
          <img src="/logo.jpg" alt="KanoonRAG Logo" className="w-12 h-12 rounded-lg shadow-sm shrink-0" />
          <div className="flex flex-col items-start min-w-0">
            <p className="font-bold text-primary leading-tight truncate w-full">KanoonRAG</p>
            <span className="text-[10px] text-on-surface-variant uppercase tracking-widest mt-0.5 font-medium truncate w-full">Legal Intelligence</span>
          </div>
        </div>
        
        <div className="px-6 mb-4 mt-2">
          <button onClick={startNewChat} className="w-full py-3 bg-primary text-on-primary font-bold rounded-lg flex items-center justify-center gap-2 active:scale-95 transition-transform">
            <span className="material-symbols-outlined">add_circle</span>
            New Chat
          </button>
        </div>

        <div className="px-6 mb-4 mt-4 flex justify-between items-center shrink-0">
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

        {/* Chat Content Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-edge_margin py-10 z-10">
          <div className="max-w-4xl mx-auto space-y-8">
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
        <div className={`px-edge_margin z-10 shrink-0 w-full transition-all duration-500 ease-in-out ${messages.length === 0 && !isAiLoading ? 'absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2' : 'pb-10 pt-4'}`}>
          <div className="max-w-4xl mx-auto">
            {messages.length === 0 && !isAiLoading && (
              <div className="text-center text-on-surface-variant mb-8 animate-in fade-in duration-700">
                <span className="material-symbols-outlined text-5xl mb-4 text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                <h2 className="font-headline-md text-on-surface mb-2">How can I help you today?</h2>
                <p className="font-body-lg">Ask a general legal question to explore KanoonRAG's global knowledge base.</p>
              </div>
            )}
            <div className="bg-surface-container-low/65 backdrop-blur-[20px] border border-outline-variant/30 p-2 rounded-2xl shadow-2xl relative transition-all focus-within:ring-2 focus-within:ring-primary/40 focus-within:border-primary">

              <div className="flex items-end gap-2 px-2 py-2">
                <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-lg hover:bg-primary/10">
                  <span className="material-symbols-outlined">attach_file</span>
                </button>
                <textarea 
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isAiLoading}
                  className="flex-1 bg-transparent border-none focus:ring-0 text-on-surface font-body-lg placeholder:text-on-surface-variant/50 py-2 resize-none custom-scrollbar max-h-[200px] outline-none" 
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

            </div>
            <div className="flex items-center justify-center gap-1.5 mt-4 text-[12px] text-on-surface-variant/70">
              <span className="material-symbols-outlined text-[14px] text-orange-400/80">warning</span>
              <p>KanoonRAG may produce inaccuracies. Always cross-reference with official legal gazettes.</p>
            </div>
          </div>
        </div>
      </main>

      {/* Right Side Panel (Suggested Prompts) */}
      {messages.length === 0 && !isAiLoading && (
        <aside className="w-[300px] bg-surface-container-lowest/50 border-l border-outline-variant px-6 hidden xl:flex flex-col py-6 shrink-0 overflow-y-auto custom-scrollbar">
          <h3 className="font-label-md text-on-surface-variant tracking-widest uppercase mb-6">Suggested Prompts</h3>
          
          <div className="space-y-4">
            {[
              { title: "Shalu Ojha vs Prashant Ojha", prompt: "What was the final outcome of the dispute between Shalu Ojha and Prashant Ojha regarding the rate of maintenance, and what were the directions given by the Supreme Court of India?" },
              { title: "Maintenance in Civil Appeal 5369", prompt: "What was the final amount of maintenance awarded to the respondent-wife in the Supreme Court of India's judgment in Civil Appeal No. 5369 of 2017?" },
              { title: "State of Rajasthan vs. Teg Bahadur", prompt: "In the case of State of Rajasthan vs. Teg Bahadur & Ors., what were the key arguments presented by the counsel for the appellant and the respondents-accused regarding the reliability of evidence and the application of Section 113-B of the Evidence Act?" },
              { title: "Jurisdiction for Cruelty", prompt: "Can a woman who has been forced to leave her matrimonial home due to acts of cruelty initiate legal proceedings in the jurisdiction of the courts where she has taken shelter with her parents or other family members?" },
              { title: "Pramod Kumar Bajaj Retirement", prompt: "What is the basis for the appellant's threefold challenge to the impugned judgment regarding his compulsory retirement in the case of Captain Pramod Kumar Bajaj vs Union of India and Another?" },
              { title: "Custody Dispute Considerations", prompt: "In a custody dispute between the father and the remarried mother, what are the key considerations for the welfare of the child according to Indian law?" },
              { title: "Ingredients for Section 304B IPC", prompt: "In the context of the criminal case against Prem Kanwar, what are the essential ingredients that must be proven to attract Section 304B of the Indian Penal Code?" },
              { title: "Vivek Singh vs. Romani Singh", prompt: "In the case of Vivek Singh vs. Romani Singh, what were the considerations made by the court in deciding the custody of the minor daughter, Saesha Singh, and what was the final decision?" }
            ].map((item, index) => (
              <button 
                key={index}
                onClick={() => setInputValue(item.prompt)}
                className="w-full text-left p-3 rounded-xl bg-surface hover:bg-primary/5 border border-outline-variant/30 hover:border-primary/40 transition-all group shadow-sm"
              >
                <h4 className="font-title-sm text-on-surface group-hover:text-primary mb-1">{item.title}</h4>
                <p className="text-[10px] text-on-surface-variant line-clamp-2">{item.prompt}</p>
              </button>
            ))}
          </div>
        </aside>
      )}
    </div>
  );
}

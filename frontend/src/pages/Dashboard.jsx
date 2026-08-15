import React, { useState, useEffect } from 'react';
import { caseService } from '../api/caseService';
import { clientService } from '../api/clientService';
import { documentService } from '../api/documentService';
import { queryService } from '../api/queryService';

const FEATURE_FLAGS = {
  ENABLE_ADVANCED_METRICS: false,
  ENABLE_INTELLIGENCE_BRIEF: false,
  ENABLE_PERFORMANCE_QUOTA: false
};

const Dashboard = () => {
  const [cases, setCases] = useState([]);
  const [clients, setClients] = useState({});
  const [documents, setDocuments] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [casesRes, clientsRes, docsRes, sessionsRes] = await Promise.all([
          caseService.getAllCases(),
          clientService.getAllClients(),
          documentService.getAllDocuments(),
          queryService.getSessions()
        ]);

        setCases(casesRes || []);
        
        // Map clients by ID for easy lookup
        const clientMap = {};
        if (clientsRes) {
          clientsRes.forEach(client => {
            clientMap[client.id] = client;
          });
        }
        setClients(clientMap);
        setDocuments(docsRes || []);
        setSessions(sessionsRes || []);
      } catch (error) {
        console.error('Failed to fetch dashboard data', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const activeCases = cases.filter(c => c.status === 'active' || c.status === 'active');

  return (
    <div className="flex-1 w-full h-full overflow-y-auto px-edge_margin pt-8 pb-12 relative custom-scrollbar">
      {/* Subtle Ambient Glow */}
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none -z-10"></div>
      
      {/* Welcome Section */}
      <div className="flex justify-between items-end mb-stack_lg">
        <div>
          <h2 className="font-headline-lg text-headline-lg mb-1">Morning, Adv. Sharma</h2>
          <p className="font-body-md text-body-md text-on-surface-variant">Your legal intelligence brief is ready for the day's proceedings.</p>
        </div>
        <div className="flex gap-stack_sm">
          <div className="px-4 py-2 bg-surface-container-high border border-outline-variant rounded-lg flex items-center gap-2">
            <span className="material-symbols-outlined text-primary scale-75">calendar_today</span>
            <span className="font-label-md text-label-md">{new Date().toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}</span>
          </div>
        </div>
      </div>

      {/* High-Level Metrics Bento */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-gutter mb-stack_lg">
        <div className="bg-surface-container border border-outline-variant p-stack_md rounded-xl group hover:border-primary/50 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <span className="material-symbols-outlined">balance</span>
            </div>
            <span className="font-label-sm text-label-sm text-primary">Live Data</span>
          </div>
          <p className="font-label-md text-label-md text-on-surface-variant uppercase mb-1">Active Cases</p>
          <h3 className="font-display-lg text-display-lg leading-none">{isLoading ? '-' : activeCases.length}</h3>
        </div>
        
        {FEATURE_FLAGS.ENABLE_ADVANCED_METRICS && (
          <div className="bg-surface-container border border-outline-variant p-stack_md rounded-xl group hover:border-primary/50 transition-colors">
            <div className="flex justify-between items-start mb-4">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                <span className="material-symbols-outlined">gavel</span>
              </div>
              <span className="font-label-sm text-label-sm text-error">Action Required</span>
            </div>
            <p className="font-label-md text-label-md text-on-surface-variant uppercase mb-1">Pending Rulings</p>
            <h3 className="font-display-lg text-display-lg leading-none">04</h3>
          </div>
        )}

        <div className="bg-surface-container border border-outline-variant p-stack_md rounded-xl group hover:border-primary/50 transition-colors">
          <div className="flex justify-between items-start mb-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <span className="material-symbols-outlined">description</span>
            </div>
            <span className="font-label-sm text-label-sm text-on-surface-variant">Syncing...</span>
          </div>
          <p className="font-label-md text-label-md text-on-surface-variant uppercase mb-1">AI Drafts Generated</p>
          <h3 className="font-display-lg text-display-lg leading-none">{isLoading ? '-' : documents.length}</h3>
        </div>

        {FEATURE_FLAGS.ENABLE_ADVANCED_METRICS && (
          <div className="bg-surface-container border border-outline-variant p-stack_md rounded-xl group hover:border-primary/50 transition-colors">
            <div className="flex justify-between items-start mb-4">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                <span className="material-symbols-outlined">history_edu</span>
              </div>
              <span className="font-label-sm text-label-sm text-primary">98% Match</span>
            </div>
            <p className="font-label-md text-label-md text-on-surface-variant uppercase mb-1">Citation Accuracy</p>
            <h3 className="font-display-lg text-display-lg leading-none">High</h3>
          </div>
        )}
      </div>

      {/* Middle Section: Brief & Featured Research */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter mb-stack_lg">
        {/* Intelligence Brief (Glassmorphic) */}
        {FEATURE_FLAGS.ENABLE_INTELLIGENCE_BRIEF && (
          <div className="lg:col-span-8 bg-surface-container-high/65 backdrop-blur-[20px] border border-outline-variant p-stack_lg rounded-2xl relative overflow-hidden shadow-[0_8px_32px_0_rgba(0,0,0,0.37)]">
            <div className="absolute top-0 right-0 p-4">
              <span className="px-3 py-1 bg-primary/20 text-primary border border-primary/30 rounded-full font-label-sm text-label-sm animate-pulse">AI REAL-TIME</span>
            </div>
            <div className="flex items-center gap-3 mb-6">
              <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
              <h3 className="font-headline-md text-headline-md">Intelligence Brief</h3>
            </div>
            <div className="space-y-4">
              <div className="p-stack_md bg-surface-container-low/50 border-l-2 border-primary rounded-r-lg">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-title-md text-title-md text-primary">Draft Alert: Writ Petition #2049</h4>
                  <span className="font-label-sm text-label-sm text-on-surface-variant">2 mins ago</span>
                </div>
                <p className="font-body-md text-body-md text-on-surface-variant mb-3">AI has detected a conflict in the citation of <span className="text-on-surface font-semibold">State of Maharashtra v. Roy (2018)</span> based on yesterday's Supreme Court amendment.</p>
                <div className="flex gap-3">
                  <button className="bg-primary text-on-primary px-4 py-1.5 rounded font-label-md text-label-md hover:brightness-110 transition-all">Review Correction</button>
                  <button className="text-on-surface-variant border border-outline-variant px-4 py-1.5 rounded font-label-md text-label-md hover:bg-surface-variant/20 transition-all">Dismiss</button>
                </div>
              </div>
              
              <div className="p-stack_md bg-surface-container-low/50 border-l-2 border-outline-variant rounded-r-lg">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-title-md text-title-md">Summary Ready: Mehta Real Estate</h4>
                  <span className="font-label-sm text-label-sm text-on-surface-variant">1 hour ago</span>
                </div>
                <p className="font-body-md text-body-md text-on-surface-variant">Comprehensive analysis of 450 pages of evidence completed. Probability of dismissal identified at 74%.</p>
              </div>
            </div>
          </div>
        )}

        {/* Side Actions / Quick Insights */}
        <div className={`lg:col-span-${FEATURE_FLAGS.ENABLE_INTELLIGENCE_BRIEF ? '4' : '12'} flex flex-col gap-gutter`}>
          <div className="bg-surface-container border border-outline-variant p-stack_md rounded-xl flex-1">
            <h4 className="font-label-md text-label-md text-on-surface-variant uppercase mb-4 tracking-widest">Active Research Sessions</h4>
            <div className="space-y-4">
              {isLoading ? (
                <p className="text-on-surface-variant text-sm">Loading sessions...</p>
              ) : sessions.length === 0 ? (
                <p className="text-on-surface-variant text-sm">No recent research sessions.</p>
              ) : (
                sessions.slice(0, 3).map(session => (
                  <div key={session.session_id} className="flex items-center justify-between group">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <div>
                        <p className="font-title-md text-title-md leading-none mb-1 group-hover:text-primary transition-colors cursor-pointer">{session.title}</p>
                        <p className="font-label-sm text-label-sm text-on-surface-variant">{session.time}</p>
                      </div>
                    </div>
                    <span className="material-symbols-outlined text-on-surface-variant scale-75 cursor-pointer hover:text-primary">open_in_new</span>
                  </div>
                ))
              )}
            </div>
          </div>
          
          {FEATURE_FLAGS.ENABLE_PERFORMANCE_QUOTA && (
            <div className="bg-primary/10 border border-primary/20 p-stack_md rounded-xl relative overflow-hidden">
              <div className="relative z-10">
                <p className="font-label-md text-label-md text-primary font-bold mb-1">PERFORMANCE QUOTA</p>
                <h4 className="font-headline-md text-headline-md mb-2">92% Billable</h4>
                <div className="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden">
                  <div className="bg-primary h-full w-[92%]"></div>
                </div>
              </div>
              <span className="material-symbols-outlined absolute -bottom-2 -right-2 text-primary opacity-10 text-7xl select-none">trending_up</span>
            </div>
          )}
        </div>
      </div>

      {/* Client Directory Table */}
      <div className="bg-surface-container border border-outline-variant rounded-2xl overflow-hidden mb-12">
        <div className="p-edge_margin flex justify-between items-center border-b border-outline-variant bg-surface-container-high/50">
          <div>
            <h3 className="font-headline-md text-headline-md">Client Directory</h3>
            <p className="font-body-md text-body-md text-on-surface-variant">Manage your priority clients and ongoing litigation status.</p>
          </div>
          <div className="flex gap-3">
            <button className="bg-surface-container-highest border border-outline-variant px-4 py-2 rounded-lg font-label-md text-label-md flex items-center gap-2 hover:bg-surface-variant transition-colors">
              <span className="material-symbols-outlined text-sm">filter_list</span>
              Filter
            </button>
            <button className="bg-surface-container-highest border border-outline-variant px-4 py-2 rounded-lg font-label-md text-label-md flex items-center gap-2 hover:bg-surface-variant transition-colors">
              <span className="material-symbols-outlined text-sm">download</span>
              Export
            </button>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-outline-variant/50">
                <th className="px-edge_margin py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Client Name</th>
                <th className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Case Reference</th>
                <th className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider">Last Activity</th>
                <th className="px-edge_margin py-4 font-label-md text-label-md text-on-surface-variant uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30">
              {isLoading ? (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-on-surface-variant">Loading cases...</td>
                </tr>
              ) : cases.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-on-surface-variant">No cases found.</td>
                </tr>
              ) : (
                cases.map((c) => {
                  const client = clients[c.client_id];
                  const initials = client ? client.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : '??';
                  return (
                    <tr key={c.id} className="hover:bg-primary/5 transition-colors group">
                      <td className="px-edge_margin py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded bg-surface-container-highest flex items-center justify-center font-bold text-primary">{initials}</div>
                          <div>
                            <p className="font-title-md text-title-md">{client ? client.name : 'Unknown Client'}</p>
                            <p className="font-label-sm text-label-sm text-on-surface-variant">{c.opposing_party_name ? `vs ${c.opposing_party_name}` : ''}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-body-md text-body-md">{c.case_type}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded border font-label-sm text-label-sm ${c.status === 'active' ? 'bg-primary/20 text-primary border-primary/30' : 'bg-on-surface-variant/10 text-on-surface-variant border-outline-variant/30'}`}>
                          {c.status.charAt(0).toUpperCase() + c.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-body-md text-body-md text-on-surface-variant">
                        {new Date(c.created_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'})}
                      </td>
                      <td className="px-edge_margin py-4 text-right">
                        <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button className="p-2 hover:bg-surface-variant/40 rounded transition-colors" title="View Case">
                            <span className="material-symbols-outlined text-on-surface-variant">visibility</span>
                          </button>
                          <button className="p-2 hover:bg-surface-variant/40 rounded transition-colors" title="Chat Assistant">
                            <span className="material-symbols-outlined text-primary">chat_bubble</span>
                          </button>
                          <button className="p-2 hover:bg-surface-variant/40 rounded transition-colors">
                            <span className="material-symbols-outlined text-on-surface-variant">more_vert</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t border-outline-variant flex justify-center">
          <button className="text-primary font-label-md text-label-md hover:underline">View All {cases.length} Cases</button>
        </div>
      </div>

      {/* FAB for Fast Research */}
      <button className="fixed bottom-8 right-8 w-14 h-14 bg-primary text-on-primary rounded-full shadow-[0_10px_25px_-5px_rgba(230,193,129,0.3)] flex items-center justify-center group hover:scale-110 active:scale-95 transition-all z-50">
        <span className="material-symbols-outlined text-3xl group-hover:rotate-12 transition-transform">auto_awesome</span>
        <div className="absolute right-full mr-4 bg-surface-container border border-outline-variant px-4 py-2 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 translate-x-4 group-hover:translate-x-0 transition-all pointer-events-none">
          <span className="font-label-md text-label-md">Instant Research Prompt</span>
        </div>
      </button>

    </div>
  );
};

export default Dashboard;

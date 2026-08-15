import React, { useState, useEffect } from 'react';
import { caseService } from '../api/caseService';
import { documentService } from '../api/documentService';

function Drafting() {
  const [cases, setCases] = useState([]);
  const [recentDrafts, setRecentDrafts] = useState([]);
  
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [docType, setDocType] = useState('legal_notice');
  const [instructions, setInstructions] = useState('');
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentDraft, setCurrentDraft] = useState(null);
  
  useEffect(() => {
    fetchCases();
    fetchRecentDrafts();
  }, []);
  
  const fetchCases = async () => {
    try {
      const response = await caseService.getAllCases();
      setCases(response);
      if (response && response.length > 0) {
        setSelectedCaseId(response[0].id.toString());
      }
    } catch (error) {
      console.error('Failed to fetch cases', error);
    }
  };
  
  const fetchRecentDrafts = async () => {
    try {
      const response = await documentService.getAllDocuments();
      // Sort by latest first
      const sorted = response.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setRecentDrafts(sorted);
    } catch (error) {
      console.error('Failed to fetch recent drafts', error);
    }
  };
  
  const handleGenerate = async () => {
    if (!selectedCaseId) {
      alert("Please select a case.");
      return;
    }
    
    setIsGenerating(true);
    setCurrentDraft(null);
    try {
      const response = await documentService.generateDocument(parseInt(selectedCaseId), docType, instructions);
      setCurrentDraft(response);
      fetchRecentDrafts(); // Refresh the list
    } catch (error) {
      console.error('Generation failed', error);
      alert('Failed to generate document. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };
  
  const handleDownload = async (docId) => {
    try {
      const { blob, filename } = await documentService.downloadDocument(docId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed', error);
      alert('Failed to download document.');
    }
  };

  const docTypeLabels = {
    'case_brief': 'Case Brief',
    'legal_notice': 'Legal Notice',
    'case_analysis': 'Case Analysis'
  };

  return (
    <div className="flex-grow p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 h-full overflow-hidden">
      {/* Left Panel: AI Drafting Interface */}
      <section className="lg:col-span-8 flex flex-col space-y-stack_md h-full">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-headline-lg text-headline-lg text-primary">Document Generation</h2>
        </div>
        {/* Configuration Card */}
        <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6 flex flex-col space-y-4 shrink-0 shadow-lg">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Select Case Context</label>
              <select 
                className="w-full bg-surface-dim border border-outline-variant rounded-lg px-4 py-2 text-on-surface focus:ring-1 focus:ring-primary focus:border-primary outline-none transition-all appearance-none cursor-pointer"
                value={selectedCaseId}
                onChange={(e) => setSelectedCaseId(e.target.value)}
              >
                {cases.map((c) => (
                  <option key={c.id} value={c.id.toString()}>
                    {c.opposing_party_name ? `vs ${c.opposing_party_name}` : `Case #${c.id}`} ({c.case_type})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Document Type</label>
              <select 
                className="w-full bg-surface-dim border border-outline-variant rounded-lg px-4 py-2 text-on-surface focus:ring-1 focus:ring-primary focus:border-primary outline-none transition-all appearance-none cursor-pointer"
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
              >
                <option value="legal_notice">Legal Notice</option>
                <option value="case_brief">Case Brief</option>
                <option value="case_analysis">Case Analysis</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block font-label-md text-label-md text-on-surface-variant mb-1">Drafting Instructions</label>
            <textarea 
              className="w-full h-24 bg-surface-dim border border-outline-variant rounded-lg p-4 text-on-surface focus:ring-1 focus:ring-primary focus:border-primary outline-none transition-all resize-none" 
              placeholder="Describe context or specific clauses required. E.g., 'Draft a termination notice citing breach of confidentiality under section 4.'"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
            ></textarea>
          </div>
          <div className="flex justify-end pt-2">
            <button 
              className="bg-primary-fixed-dim hover:bg-primary-fixed text-on-primary px-6 py-2.5 rounded-lg font-title-md text-title-md flex items-center transition-all active:scale-95 shadow-md shadow-primary-container/10 disabled:opacity-50"
              onClick={handleGenerate}
              disabled={isGenerating || cases.length === 0}
            >
              <span className="material-symbols-outlined mr-2" style={{ fontVariationSettings: "'FILL' 1" }}>
                {isGenerating ? 'hourglass_empty' : 'auto_awesome'}
              </span>
              {isGenerating ? 'Generating...' : 'Generate Document'}
            </button>
          </div>
        </div>
        
        {/* Output Card */}
        <div className="bg-surface-container border border-outline-variant rounded-xl flex-grow flex flex-col overflow-hidden shadow-lg relative">
          {/* Glassmorphic header for output */}
          <div className="bg-glass-bg backdrop-blur-md border-b border-outline-variant p-4 flex justify-between items-center z-10">
            <div className="flex items-center space-x-2">
              <span className="material-symbols-outlined text-primary text-[20px]">description</span>
              <h3 className="font-title-md text-title-md text-on-surface">
                {currentDraft ? `Draft: ${docTypeLabels[currentDraft.doc_type] || 'Document'}` : 'Output Preview'}
              </h3>
            </div>
            <div className="flex space-x-2">
              <button 
                className="px-4 py-1.5 border border-outline-gold text-primary rounded-lg font-label-md hover:bg-surface-variant transition-colors flex items-center disabled:opacity-50"
                disabled={!currentDraft}
              >
                <span className="material-symbols-outlined mr-1 text-[16px]">edit</span> Edit
              </button>
              <button 
                className="px-4 py-1.5 bg-primary-container/10 border border-primary text-primary rounded-lg font-label-md hover:bg-primary-container/20 transition-colors flex items-center disabled:opacity-50"
                disabled={!currentDraft}
                onClick={() => handleDownload(currentDraft.id)}
              >
                <span className="material-symbols-outlined mr-1 text-[16px]">download</span> Download
              </button>
            </div>
          </div>
          
          {/* Rich Text Area Placeholder */}
          <div className="flex-grow p-6 overflow-y-auto font-citation-serif text-citation-serif text-on-surface-variant leading-relaxed custom-scrollbar bg-surface-container-lowest/50">
            {isGenerating ? (
              <div className="flex items-center justify-center h-full text-on-surface-variant opacity-75">
                <span className="material-symbols-outlined animate-spin mr-2">progress_activity</span>
                Generating document...
              </div>
            ) : currentDraft ? (
              <div className="text-on-surface">
                <p className="mb-4 text-primary">✓ Document successfully generated.</p>
                <p>The document is ready for download as a DOCX file.</p>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-on-surface-variant opacity-50">
                <p>Fill out the configuration and click Generate to create a document.</p>
              </div>
            )}
          </div>
        </div>
      </section>
      
      {/* Right Panel: Past Documents */}
      <aside className="lg:col-span-4 h-full flex flex-col bg-surface-container-low rounded-xl border border-outline-variant overflow-hidden shadow-lg">
        <div className="p-4 border-b border-outline-variant bg-surface-dim">
          <h3 className="font-headline-md text-headline-md text-primary">Recent Drafts</h3>
        </div>
        <div className="flex-grow overflow-y-auto custom-scrollbar p-2 space-y-2">
          {recentDrafts.length === 0 && (
            <p className="text-on-surface-variant text-center mt-4">No recent drafts.</p>
          )}
          {recentDrafts.map((draft) => (
            <div 
              key={draft.id} 
              className="p-4 rounded-lg bg-surface-container hover:bg-surface-variant transition-colors group cursor-pointer border-l-2 border-transparent hover:border-primary"
              onClick={() => {
                setCurrentDraft(draft);
                setDocType(draft.doc_type);
              }}
            >
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-title-md text-title-md text-on-surface group-hover:text-primary transition-colors">
                  {docTypeLabels[draft.doc_type] || 'Document'}
                </h4>
                <button 
                  className="text-on-surface-variant hover:text-primary opacity-0 group-hover:opacity-100 transition-all"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDownload(draft.id);
                  }}
                >
                  <span className="material-symbols-outlined text-[20px]">download</span>
                </button>
              </div>
              <div className="flex items-center space-x-2 text-on-secondary-container font-label-md text-label-md">
                <span>{new Date(draft.created_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}</span>
                <span className="w-1 h-1 rounded-full bg-outline"></span>
                <span className="truncate">Case #{draft.case_id}</span>
              </div>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}

export default Drafting;

import { apiClient } from './apiClient';

export const documentService = {
  getAllDocuments: () => {
    return apiClient.get('/documents/');
  },
  
  generateDocument: (caseId, docType, instructions) => {
    return apiClient.post('/documents/generate', {
      case_id: caseId,
      doc_type: docType,
      additional_instructions: instructions
    });
  },
  
  downloadDocument: async (docId) => {
    // Download endpoint returns a file, so we need to use fetch directly or configure apiClient to handle blob
    const token = apiClient.getAuthToken();
    const response = await fetch(`${apiClient.baseURL}/documents/${docId}/download`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to download document');
    }
    
    const blob = await response.blob();
    
    // Extract filename from Content-Disposition if possible
    let filename = `document_${docId}.docx`;
    const disposition = response.headers.get('Content-Disposition');
    if (disposition && disposition.indexOf('filename=') !== -1) {
      const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
      const matches = filenameRegex.exec(disposition);
      if (matches != null && matches[1]) { 
        filename = matches[1].replace(/['"]/g, '');
      }
    }
    
    return { blob, filename };
  }
};

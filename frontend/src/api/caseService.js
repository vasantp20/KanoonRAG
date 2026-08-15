import { apiClient } from './apiClient';

export const caseService = {
  getAllCases: () => {
    return apiClient.get('/cases/');
  },
  
  getCase: (id) => {
    return apiClient.get(`/cases/${id}`);
  },
  
  createCase: (caseData) => {
    return apiClient.post('/cases/', caseData);
  },
  
  updateCase: (id, caseData) => {
    return apiClient.put(`/cases/${id}`, caseData);
  },
  
  deleteCase: (id) => {
    return apiClient.delete(`/cases/${id}`);
  },
  
  uploadDocument: (caseId, file) => {
    // Requires a different header (multipart/form-data)
    // usually fetch handles this automatically if you pass FormData 
    // and omit Content-Type so it can set the boundary.
    const token = apiClient.getAuthToken();
    const formData = new FormData();
    formData.append('file', file);
    
    return fetch(`${apiClient.baseURL}/cases/${caseId}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }).then(res => res.json());
  },
  
  getDocuments: (caseId) => {
    return apiClient.get(`/cases/${caseId}/documents`);
  }
};

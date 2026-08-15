import { apiClient } from './apiClient';

export const queryService = {
  sendQuery: (query, caseId = null, sessionId = null) => {
    return apiClient.post('/query/', {
      query: query,
      case_id: caseId,
      session_id: sessionId
    });
  },
  getSessions: () => {
    return apiClient.get('/query/sessions');
  },
  getSessionHistory: (sessionId) => {
    return apiClient.get(`/query/sessions/${sessionId}`);
  },
  getCaseHistory: (caseId) => {
    return apiClient.get(`/query/cases/${caseId}/history`);
  }
};

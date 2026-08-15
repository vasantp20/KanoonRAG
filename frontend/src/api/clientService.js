import { apiClient } from './apiClient';

export const clientService = {
  getAllClients: () => {
    return apiClient.get('/clients/');
  },
  
  getClient: (id) => {
    return apiClient.get(`/clients/${id}`);
  },
  
  createClient: (clientData) => {
    return apiClient.post('/clients/', clientData);
  },
  
  updateClient: (id, clientData) => {
    return apiClient.put(`/clients/${id}`, clientData);
  },
  
  deleteClient: (id) => {
    return apiClient.delete(`/clients/${id}`);
  },
  
  getClientCases: (id) => {
    return apiClient.get(`/clients/${id}/cases`);
  }
};

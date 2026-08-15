import { apiClient } from './apiClient';

export const authService = {
  login: async (email, password) => {
    const data = await apiClient.post('/auth/login', {
      email,
      password
    });
    
    // Store token
    apiClient.setAuthToken(data.access_token);
    return data;
  },

  register: async (fullName, org, email, password) => {
    const data = await apiClient.post('/auth/register', {
      full_name: fullName,
      organization: org,
      email,
      password
    });
    
    // Store token
    apiClient.setAuthToken(data.access_token);
    return data;
  },

  logout: () => {
    apiClient.setAuthToken(null);
  },

  getMe: () => {
    return apiClient.get('/me');
  }
};

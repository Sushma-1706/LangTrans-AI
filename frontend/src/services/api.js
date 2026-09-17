import axios from 'axios';
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000', timeout: 30000 });
export const submitFile = (file, translate, targetLanguage) => { const form = new FormData(); form.append('file', file); form.append('translate', translate); form.append('target_language', targetLanguage); return api.post('/upload', form); };
export const submitUrl = (mediaUrl, translate, targetLanguage) => { const form = new FormData(); form.append('media_url', mediaUrl); form.append('translate', translate); form.append('target_language', targetLanguage); return api.post('/process-url', form); };
export const getJob = (id) => api.get(`/job/${id}`);

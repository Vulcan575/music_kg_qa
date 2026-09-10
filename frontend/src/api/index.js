import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 60000
})

export const getVisualData = () => api.get('/visual')
export const sendChat = (data) => api.post('/chat', data)
export const searchAndImport = (data) => api.post('/search_import', data)
export const runSpider = () => api.post('/run_spider')

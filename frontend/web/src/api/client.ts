import axios, { AxiosInstance, AxiosResponse } from 'axios';

// 创建 axios 实例
const client: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 100000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
client.interceptors.response.use(
  (response: AxiosResponse) => {
    // 后端返回格式：{ status: 'success', data: {...} }
    // 我们直接返回整个 response.data，让各个 API 函数自己取 data 字段
    console.log(response)
    return response.data;
  },
  (error) => {
    // 统一错误处理
    const message = error.response?.data?.message || error.message || '请求失败';
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);

export default client;

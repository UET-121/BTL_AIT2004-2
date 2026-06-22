import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor - Attach Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor - Handle 401 (JWT expired / invalid)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't redirect if we're already on the login page or this IS the login request
      const isLoginRequest = error.config?.url?.includes('/user/login');
      if (!isLoginRequest) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ───
export const login = async (username, password) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await api.post('/user/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

// ─── Detections API ───
export const getDetections = async (skip = 0, limit = 100, profileId = '') => {
  let url = `/detection/get_log?skip=${skip}&limit=${limit}`;
  if (profileId) {
    url += `&profile_id=${profileId}`;
  }
  const response = await api.get(url);
  return response.data;
};

export const deleteDetection = async (logId) => {
  const response = await api.delete(`/detection/delete/${logId}`);
  return response.data;
};

export const exportDetections = async (params = {}) => {
  const query = new URLSearchParams();
  if (params.camera_id) query.append('camera_id', params.camera_id);
  if (params.start_time) query.append('start_time', params.start_time);
  if (params.end_time) query.append('end_time', params.end_time);
  const response = await api.get(`/detection/export?${query.toString()}`);
  return response.data;
};

// ─── Recognition Logs API ───
export const getRecognitionLogs = async (skip = 0, limit = 100, profileId = '') => {
  let url = `/recognition/get_logs?skip=${skip}&limit=${limit}`;
  if (profileId) {
    url += `&profile_id=${profileId}`;
  }
  const response = await api.get(url);
  return response.data;
};

export const exportRecognitionLogs = async (params = {}) => {
  const query = new URLSearchParams();
  if (params.camera_id) query.append('camera_id', params.camera_id);
  if (params.profile_id) query.append('profile_id', params.profile_id);
  if (params.start_time) query.append('start_time', params.start_time);
  if (params.end_time) query.append('end_time', params.end_time);
  const response = await api.get(`/recognition/export?${query.toString()}`);
  return response.data;
};

export const deleteRecognitionLog = async (logId) => {
  const response = await api.delete(`/recognition/delete/${logId}`);
  return response.data;
};

// ─── Cameras API ───
export const getCameras = async () => {
  const response = await api.get('/cameras/cameras-list');
  return response.data;
};

export const createCamera = async (cameraId, link, name) => {
  const response = await api.post('/cameras/create-cameras', {
    camera_id: cameraId,
    link: link,
    name: name,
  });
  return response.data;
};

export const updateCamera = async (cameraId, link, name) => {
  const response = await api.put(`/cameras/update-camera?camera_id=${cameraId}`, {
    link: link,
    name: name,
  });
  return response.data;
};

export const deleteCamera = async (cameraId) => {
  const response = await api.post(`/cameras/delete-camera?camera_id=${cameraId}`);
  return response.data;
};

export const startStream = async (cameraId) => {
  const response = await api.post(`/cameras/start-camera?camera_id=${cameraId}`);
  return response.data;
};

export const stopStream = async (cameraId) => {
  const response = await api.post(`/cameras/stop-camera?camera_id=${cameraId}`);
  return response.data;
};

export const processImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/cameras/process-image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// ─── Profiles API ───
export const getProfiles = async (skip = 0, limit = 20, search = '') => {
  let url = `/profiles/get-profile-list?skip=${skip}&limit=${limit}`;
  if (search) {
    url += `&search=${search}`;
  }
  const response = await api.get(url);
  return response.data;
};

export const createProfile = async (name, file) => {
  const formData = new FormData();
  formData.append('name', name);
  formData.append('file', file);

  const response = await api.post('/profiles/create-new-profile', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const deleteProfile = async (profileId) => {
  const response = await api.delete(`/profiles/delete-profile?profile_id=${profileId}`);
  return response.data;
};

// ─── Analytics API ───
export const getAnalyticsOverview = async () => {
  const response = await api.get('/analytics/overview');
  return response.data;
};

// ─── Webhook API ───
export const getWebhookConfig = async () => {
  const response = await api.get('/webhook/config');
  return response.data;
};

export const updateWebhookConfig = async (config) => {
  const response = await api.post('/webhook/config', config);
  return response.data;
};

export const testWebhook = async (url) => {
  const response = await api.post('/webhook/test', { url });
  return response.data;
};

// AI Config
export const getAiConfig = async () => {
  const response = await api.get('/config/');
  return response.data;
};

export const updateDetectThresholds = async (conf_thres, iou_thres) => {
  const response = await api.put('/config/detect-thresholds', null, { params: { conf_thres, iou_thres } });
  return response.data;
};

export const updateRecognitionThreshold = async (threshold) => {
  const response = await api.put('/config/recognition-threshold', null, { params: { threshold } });
  return response.data;
};


// ─── Users Management API ───
export const getUsers = async () => {
  const response = await api.get('/users/list');
  return response.data;
};

export const createUser = async (username, password, role = 'viewer') => {
  const response = await api.post('/users/create', { username, password, role });
  return response.data;
};

export const deleteUser = async (userId) => {
  const response = await api.delete(`/users/delete/${userId}`);
  return response.data;
};

export const updateUserRole = async (userId, role) => {
  const response = await api.put(`/users/update-role/${userId}`, { role });
  return response.data;
};

export default api;

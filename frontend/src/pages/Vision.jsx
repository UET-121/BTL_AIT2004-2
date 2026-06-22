import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Video, Camera, Plus, Trash2, Edit3, Eye, Power, PowerOff,
  Loader2, UploadCloud, Image as ImageIcon, Settings,
  LayoutGrid, List
} from 'lucide-react';
import { getCameras, createCamera, updateCamera, deleteCamera, startStream, stopStream, processImage } from '../services/api';
import CameraDrawer from '../components/CameraDrawer';
import LiveStreamModal from '../components/LiveStreamModal';
import Sidebar from '../components/Sidebar';
import toast from 'react-hot-toast';
import './Dashboard.css';
import './Vision.css';

const Vision = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const userRole = localStorage.getItem('user_role') || 'viewer';

  const [cameras, setCameras] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingCamera, setEditingCamera] = useState(null);

  // Live Stream Modal state
  const [streamCamera, setStreamCamera] = useState(null);

  // Camera toggle loading states
  const [togglingCameras, setTogglingCameras] = useState({});

  // Image upload
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  // WebSocket for camera status
  const wsRef = useRef(null);

  const fetchCameras = useCallback(async () => {
    try {
      const res = await getCameras();
      setCameras(res.data || []);
    } catch (err) {
      console.error('Error fetching cameras:', err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [fetchCameras]);

  // Global WebSocket for camera status updates
  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/notifications/`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const camId = String(msg.data?.camera_id);

        if (msg.topic === 'ui.camera.started') {
          setTogglingCameras(prev => ({ ...prev, [camId]: false }));
          setCameras(prev => prev.map(c =>
            String(c.id) === camId ? { ...c, is_active: true } : c
          ));
          toast.success(`Camera ${camId} đã bật thành công`);
        }

        if (msg.topic === 'ui.camera.error') {
          setTogglingCameras(prev => ({ ...prev, [camId]: false }));
          setCameras(prev => prev.map(c =>
            String(c.id) === camId ? { ...c, is_active: false } : c
          ));
          toast.error(`Lỗi Camera ${camId}: ${msg.data?.message || 'Không xác định'}`);
        }

        if (msg.topic === 'ui.camera.stopped') {
          setTogglingCameras(prev => ({ ...prev, [camId]: false }));
          setCameras(prev => prev.map(c =>
            String(c.id) === camId ? { ...c, is_active: false } : c
          ));
        }

        if (msg.topic === 'ui.camera.disconnected') {
          setTogglingCameras(prev => ({ ...prev, [camId]: false }));
          setCameras(prev => prev.map(c =>
            String(c.id) === camId ? { ...c, is_active: false } : c
          ));
          toast.error(`Camera ${camId} đã mất kết nối đột ngột!`);
        }
      } catch {
        // Ignore
      }
    };

    wsRef.current = ws;
    return () => ws.close();
  }, []);

  const handleToggleCamera = async (cam) => {
    const camId = String(cam.id);
    setTogglingCameras(prev => ({ ...prev, [camId]: true }));

    try {
      if (cam.is_active) {
        await stopStream(camId);
        // Optimistic update
        setCameras(prev => prev.map(c =>
          String(c.id) === camId ? { ...c, is_active: false } : c
        ));
        setTogglingCameras(prev => ({ ...prev, [camId]: false }));
        toast.success(`Camera ${cam.name} đã tắt`);
      } else {
        await startStream(camId);
        // Wait for WebSocket confirmation (ui.camera.started)
        // Set a timeout fallback
        setTimeout(() => {
          setTogglingCameras(prev => {
            if (prev[camId]) {
              toast.error(`Camera ${cam.name}: Không nhận được phản hồi từ backend`);
              return { ...prev, [camId]: false };
            }
            return prev;
          });
        }, 15000);
      }
    } catch (err) {
      setTogglingCameras(prev => ({ ...prev, [camId]: false }));
      toast.error(`Lỗi: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleSaveCamera = async (data, isEdit) => {
    try {
      if (isEdit) {
        await updateCamera(data.id, data.url, data.name);
        toast.success('Cập nhật camera thành công');
      } else {
        await createCamera(data.id, data.url, data.name);
        toast.success('Thêm camera thành công');
      }
      fetchCameras();
    } catch (err) {
      toast.error('Lỗi: ' + (err.response?.data?.detail || err.message));
      throw err;
    }
  };

  const handleDeleteCamera = async (cam) => {
    if (!window.confirm(`Xóa camera "${cam.name}" (ID: ${cam.id})?`)) return;
    try {
      await deleteCamera(cam.id);
      fetchCameras();
      toast.success('Đã xóa camera');
    } catch (err) {
      toast.error('Lỗi xóa: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleViewLive = (cam) => {
    if (!cam.is_active) {
      toast.error('Camera chưa được bật. Hãy bật AI Detection trước.');
      return;
    }
    setStreamCamera(cam);
  };

  const handleStreamClose = (aiStopped) => {
    if (aiStopped && streamCamera) {
      setCameras(prev => prev.map(c =>
        String(c.id) === String(streamCamera.id) ? { ...c, is_active: false } : c
      ));
    }
    setStreamCamera(null);
  };

  const handleStopAI = async (camId) => {
    try {
      await stopStream(camId);
      toast.success('Đã tắt AI camera');
    } catch (err) {
      toast.error('Lỗi tắt camera: ' + err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    navigate('/login');
  };

  const handleUploadImage = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadStatus('Đang xử lý...');
    try {
      const res = await processImage(selectedFile);
      setUploadStatus(`Thành công: ${res.message}`);
      setSelectedFile(null);
    } catch (err) {
      setUploadStatus('Lỗi: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      {/* Main Content */}
      <main className="main-content">
        <header className="content-header">
          <h1>Quản Lý Camera</h1>
          <div className="header-actions">
            <div className="view-toggle">
              <button
                className={`view-toggle-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
                title="Grid View"
              >
                <LayoutGrid size={18} />
              </button>
              <button
                className={`view-toggle-btn ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => setViewMode('list')}
                title="List View"
              >
                <List size={18} />
              </button>
            </div>
            {userRole === 'admin' && (
              <button
                className="btn-primary add-cam-btn"
                onClick={() => { setEditingCamera(null); setDrawerOpen(true); }}
              >
                <Plus size={18} /> Thêm Camera
              </button>
            )}
          </div>
        </header>

        {isLoading ? (
          <div className="loading-state">Đang tải danh sách camera...</div>
        ) : cameras.length === 0 ? (
          <div className="empty-state glass-panel">
            <Video size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem' }} />
            <p>Chưa có camera nào. Nhấn "Thêm Camera" để bắt đầu.</p>
          </div>
        ) : (
          <>
            {/* Camera Grid/List */}
            <div className={viewMode === 'grid' ? 'camera-grid' : 'camera-list-view'}>
              {cameras.map(cam => {
                const camId = String(cam.id);
                const isToggling = togglingCameras[camId];

                return viewMode === 'grid' ? (
                  /* ── Grid Card ── */
                  <div key={cam.id} className={`camera-card glass-panel ${cam.is_active ? 'card-active' : ''}`}>
                    <div className="camera-card-header">
                      <div className="camera-card-info">
                        <span className={`cam-status-badge ${cam.is_active ? 'active' : 'inactive'}`}>
                          {cam.is_active ? 'Đang hoạt động' : 'Đang tắt'}
                        </span>
                        <h3>{cam.name}</h3>
                        <span className="camera-card-id">ID: {cam.id}</span>
                      </div>
                    </div>

                    <div className="camera-card-rtsp">
                      <span className="rtsp-label">RTSP</span>
                      <span className="rtsp-url">{cam.link || cam.rtsp_url || '—'}</span>
                    </div>

                    <div className="camera-card-toggle">
                      <span className="toggle-label">AI Detection</span>
                      <button
                        className={`toggle-switch ${cam.is_active ? 'on' : 'off'} ${isToggling ? 'loading' : ''}`}
                        onClick={() => handleToggleCamera(cam)}
                        disabled={isToggling}
                        title={cam.is_active ? 'Tắt AI Detection (camera ngừng xử lý)' : 'Bật AI Detection (chạy ngầm, không stream)'}
                      >
                        {isToggling ? (
                          <Loader2 size={14} className="spin-icon toggle-loader" />
                        ) : (
                          <div className="toggle-knob" />
                        )}
                      </button>
                    </div>

                    <div className="camera-card-actions">
                      <button
                        className={`cam-action-btn view-btn ${!cam.is_active ? 'disabled' : ''}`}
                        onClick={() => handleViewLive(cam)}
                        disabled={!cam.is_active}
                        title={cam.is_active ? 'Xem trực tiếp camera' : 'Bật camera trước để xem'}
                      >
                        <Eye size={16} /> Xem Live
                      </button>
                      {userRole === 'admin' && (
                        <>
                          <button
                            className="cam-action-btn edit-btn"
                            onClick={() => { setEditingCamera(cam); setDrawerOpen(true); }}
                            title="Sửa thông tin camera"
                          >
                            <Edit3 size={16} /> Sửa
                          </button>
                          <button
                            className="cam-action-btn delete-btn"
                            onClick={() => handleDeleteCamera(cam)}
                            title="Xóa camera"
                          >
                            <Trash2 size={16} /> Xóa
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ) : (
                  /* ── List Row ── */
                  <div key={cam.id} className={`camera-row glass-panel ${cam.is_active ? 'row-active' : ''}`}>
                    <span className={`cam-status-dot ${cam.is_active ? 'active' : 'inactive'}`} />
                    <div className="camera-row-info">
                      <strong>{cam.name}</strong>
                      <span>ID: {cam.id}</span>
                    </div>
                    <span className="camera-row-rtsp">{cam.link || cam.rtsp_url || '—'}</span>
                    <button
                      className={`toggle-switch small ${cam.is_active ? 'on' : 'off'} ${isToggling ? 'loading' : ''}`}
                      onClick={() => handleToggleCamera(cam)}
                      disabled={isToggling}
                    >
                      {isToggling ? <Loader2 size={12} className="spin-icon toggle-loader" /> : <div className="toggle-knob" />}
                    </button>
                    <div className="camera-row-actions">
                      <button className="icon-btn" onClick={() => handleViewLive(cam)} disabled={!cam.is_active} title="Xem Live">
                        <Eye size={16} />
                      </button>
                      {userRole === 'admin' && (
                        <>
                          <button className="icon-btn" onClick={() => { setEditingCamera(cam); setDrawerOpen(true); }} title="Sửa">
                            <Edit3 size={16} />
                          </button>
                          <button className="icon-btn delete-btn" onClick={() => handleDeleteCamera(cam)} title="Xóa">
                            <Trash2 size={16} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Manual Image Upload Section */}
            <div className="vision-card glass-panel" style={{ marginTop: '1.5rem' }}>
              <h2><ImageIcon size={20} /> Tải ảnh thủ công</h2>
              <p className="card-desc">Tải lên một bức ảnh để test thuật toán nhận diện.</p>

              <form onSubmit={handleUploadImage} className="vision-form upload-form">
                <div className="file-upload-wrapper">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="file-input"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="file-upload-label">
                    <UploadCloud size={32} />
                    <span>{selectedFile ? selectedFile.name : 'Click để chọn file ảnh'}</span>
                  </label>
                </div>

                <button type="submit" className="btn-primary upload-btn" disabled={!selectedFile || isUploading}>
                  {isUploading ? 'Đang tải lên...' : 'Xử lý Ảnh'}
                </button>

                {uploadStatus && (
                  <div style={{ marginTop: '10px', color: uploadStatus.includes('Lỗi') ? '#ff4d4d' : '#4dff4d' }}>
                    {uploadStatus}
                  </div>
                )}
              </form>
            </div>
          </>
        )}
      </main>

      {/* Camera Drawer */}
      <CameraDrawer
        isOpen={drawerOpen}
        onClose={() => { setDrawerOpen(false); setEditingCamera(null); }}
        onSave={handleSaveCamera}
        editCamera={editingCamera}
      />

      {/* Live Stream Modal */}
      <LiveStreamModal
        isOpen={!!streamCamera}
        camera={streamCamera}
        onClose={handleStreamClose}
        onStopAI={handleStopAI}
      />
    </div>
  );
};

export default Vision;

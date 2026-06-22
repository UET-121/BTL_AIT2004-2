import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getDetections, deleteDetection, exportDetections, getCameras, getProfiles, getRecognitionLogs, deleteRecognitionLog, exportRecognitionLogs } from '../services/api';
import { getAnalyticsOverview } from '../services/api';
import './Dashboard.css';
import { Trash2, RefreshCw, Search, Play, Pause, ChevronLeft, ChevronRight, BarChart2, List, Download, Filter, FileSpreadsheet, X } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import toast from 'react-hot-toast';
import Sidebar from '../components/Sidebar';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#ef4444', '#f59e0b', '#06b6d4'];

const Dashboard = () => {
  const [detections, setDetections] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const token = localStorage.getItem("access_token");

  // Analytics State
  const [analytics, setAnalytics] = useState({
    total_detections: 0,
    known_profiles: 0,
    unknown_detections: 0,
    bar_data: [],
    pie_data: []
  });
  const [isAnalyticsLoading, setIsAnalyticsLoading] = useState(false);

  // Camera list
  const [cameraList, setCameraList] = useState([]);
  const [cameraFilter, setCameraFilter] = useState('');

  // Tabs
  const [activeTab, setActiveTab] = useState('history');

  // Pagination & Filters
  const [page, setPage] = useState(1);
  const [profileIdFilter, setProfileIdFilter] = useState('');
  const [logType, setLogType] = useState('detection'); // 'detection' or 'recognition'
  const limit = 20;

  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(false);
  const autoRefreshRef = useRef(null);

  // Export Modal
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportCameraId, setExportCameraId] = useState('');
  const [exportProfileId, setExportProfileId] = useState('');
  const [exportStartTime, setExportStartTime] = useState('');
  const [exportEndTime, setExportEndTime] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  // Profiles for export filter
  const [profileList, setProfileList] = useState([]);

  const userRole = localStorage.getItem('user_role') || 'viewer';

  const navigate = useNavigate();
  const location = useLocation();

  const fetchLogs = async (currentPage = page, filter = profileIdFilter, currentLogType = logType) => {
    setIsLoading(true);
    try {
      const skip = (currentPage - 1) * limit;
      let data;
      if (currentLogType === 'detection') {
        data = await getDetections(skip, limit, filter);
      } else {
        data = await getRecognitionLogs(skip, limit, filter);
      }
      setDetections(data.data || []);
    } catch (err) {
      console.error('Error fetching logs:', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCameraList = async () => {
    try {
      const res = await getCameras();
      setCameraList(res.data || []);
    } catch (err) {
      console.error('Error fetching cameras:', err.message);
    }
  };

  const fetchProfiles = async () => {
    try {
      const res = await getProfiles(0, 100);
      setProfileList(res.data || []);
    } catch (err) {
      console.error('Error fetching profiles:', err.message);
    }
  };

  const getCameraName = (cameraId) => {
    const cam = cameraList.find(c => String(c.id) === String(cameraId));
    return cam ? cam.name : null;
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchLogs(page, profileIdFilter, logType);
    fetchCameraList();
    fetchProfiles();
  }, [page, logType, navigate]);

  const fetchAnalytics = async () => {
    setIsAnalyticsLoading(true);
    try {
      const data = await getAnalyticsOverview();
      setAnalytics(data);
    } catch (err) {
      console.error('Analytics not available:', err.message);
      // Backend chưa có API nên lỗi là bình thường
    } finally {
      setIsAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchAnalytics();
    }
  }, [activeTab]);

  useEffect(() => {
    if (autoRefresh) {
      autoRefreshRef.current = setInterval(() => {
        fetchLogs(1, profileIdFilter, logType); // Lấy trang đầu khi auto refresh
        if (page !== 1) setPage(1);
      }, 5000);
    } else {
      if (autoRefreshRef.current) clearInterval(autoRefreshRef.current);
    }
    return () => clearInterval(autoRefreshRef.current);
  }, [autoRefresh, profileIdFilter, logType]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('username');
    navigate('/login');
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa log này?')) return;
    try {
      if (logType === 'detection') {
        await deleteDetection(id);
      } else {
        await deleteRecognitionLog(id);
      }
      fetchLogs(page, profileIdFilter, logType);
    } catch (err) {
      toast.error('Lỗi xóa log: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchLogs(1, profileIdFilter, logType);
  };

  const handleExportExcel = async () => {
    setIsExporting(true);
    try {
      const params = {};
      if (exportCameraId) params.camera_id = exportCameraId;
      if (exportProfileId) params.profile_id = exportProfileId;
      if (exportStartTime) params.start_time = exportStartTime;
      if (exportEndTime) params.end_time = exportEndTime;

      if (logType === 'detection') {
        await exportDetections(params);
      } else {
        await exportRecognitionLogs(params);
      }
      setShowExportModal(false);
      toast.success(
        'Yêu cầu xuất dữ liệu đã được gửi. File đang được xử lý, bạn sẽ nhận được thông báo tải xuống khi hoàn thành.',
        { duration: 6000 }
      );
    } catch (err) {
      toast.error('Lỗi xuất file: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      {/* Main Content */}
      <main className="main-content">
        <header className="content-header">
          <h1>Dashboard An Ninh</h1>

          <div className="header-actions">
            <div className="tabs">
              <button
                className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                <BarChart2 size={18} /> Tổng quan
              </button>
              <button
                className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
                onClick={() => setActiveTab('history')}
              >
                <List size={18} /> Lịch sử
              </button>
            </div>
          </div>
        </header>

        {activeTab === 'overview' && (
          <div className="overview-section">
            {/* Camera Filter */}
            <div className="camera-filter-section">
              <Filter size={16} />
              <label>Camera</label>
              <select
                className="camera-filter-select"
                value={cameraFilter}
                onChange={(e) => setCameraFilter(e.target.value)}
              >
                <option value="">Tất cả Camera</option>
                {cameraList.map(cam => (
                  <option key={cam.id} value={cam.id}>
                    [{cam.id}] {cam.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="kpi-grid">
              <div className="kpi-card glass-panel">
                <h3>Tổng Lượt Nhận Diện</h3>
                <p style={{ color: 'var(--accent-primary)' }}>
                  {isAnalyticsLoading ? '...' : analytics.total_detections}
                </p>
              </div>
              <div className="kpi-card glass-panel">
                <h3>Nhân Sự Đã Biết</h3>
                <p style={{ color: 'var(--success)' }}>
                  {isAnalyticsLoading ? '...' : analytics.known_profiles}
                </p>
              </div>
              <div className="kpi-card glass-panel">
                <h3>Người Lạ</h3>
                <p style={{ color: 'var(--danger)' }}>
                  {isAnalyticsLoading ? '...' : analytics.unknown_detections}
                </p>
              </div>
            </div>

            <div className="charts-grid">
              <div className="chart-card glass-panel">
                <h3>Lưu lượng theo giờ</h3>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.bar_data}>
                    <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={12} />
                    <Tooltip cursor={{ fill: 'rgba(99, 102, 241, 0.08)' }} contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', color: '#e2e8f0' }} labelStyle={{ color: '#94a3b8' }} />
                    <Bar dataKey="detections" fill="#6366f1" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="chart-card glass-panel">
                <h3>Phân bổ theo Camera</h3>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={analytics.pie_data} innerRadius={55} outerRadius={80} paddingAngle={4} dataKey="value">
                      {analytics.pie_data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', color: '#e2e8f0' }} />
                    <Legend wrapperStyle={{ fontSize: '0.8rem', color: '#94a3b8' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="history-section">
            {/* Camera Filter */}
            <div className="camera-filter-section">
              <Filter size={16} />
              <label>Camera</label>
              <select
                className="camera-filter-select"
                value={cameraFilter}
                onChange={(e) => setCameraFilter(e.target.value)}
              >
                <option value="">Tất cả Camera</option>
                {cameraList.map(cam => (
                  <option key={cam.id} value={cam.id}>
                    [{cam.id}] {cam.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="history-toolbar" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.25rem', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className={`tab-btn ${logType === 'detection' ? 'active' : ''}`}
                  onClick={() => { setLogType('detection'); setPage(1); }}
                >
                  Detection Logs
                </button>
                <button
                  className={`tab-btn ${logType === 'recognition' ? 'active' : ''}`}
                  onClick={() => { setLogType('recognition'); setPage(1); }}
                >
                  Recognition Logs
                </button>
              </div>

              <form onSubmit={handleSearch} className="search-form" style={{ marginLeft: 'auto', marginRight: '1rem' }}>
                <input
                  type="text"
                  placeholder="Tìm theo ID Nhân sự (Profile ID)..."
                  value={profileIdFilter}
                  onChange={(e) => setProfileIdFilter(e.target.value)}
                  className="search-input"
                />
                <button type="submit" className="search-btn"><Search size={18} /></button>
              </form>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="refresh-btn export-excel-btn" onClick={() => setShowExportModal(true)}>
                  <FileSpreadsheet size={18} /> Xuất Excel
                </button>
                <button
                  className={`auto-refresh-btn ${autoRefresh ? 'active' : ''}`}
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  title="Auto Refresh (5s)"
                >
                  {autoRefresh ? <Pause size={18} /> : <Play size={18} />}
                </button>
                <button className="refresh-btn" onClick={() => fetchLogs(page, profileIdFilter, logType)}>
                  <RefreshCw size={18} className={isLoading ? 'spinning' : ''} />
                  Làm mới
                </button>
              </div>
            </div>

            <div className="detections-grid">
              {isLoading && detections.length === 0 ? (
                <div className="loading-state">Đang tải dữ liệu...</div>
              ) : detections.length === 0 ? (
                <div className="empty-state glass-panel">Chưa có lịch sử nhận diện nào.</div>
              ) : (
                detections.map((item) => (
                  <div key={item.log_id} className="detection-card glass-panel">
                    <div className="card-image-wrapper">
                      {item.image_url ? (
                        <img src={
                          item.image_url.includes('http://minio:9000/license_plate-recognition-images/')
                            ? `/api/internal/${item.image_url.replace('http://minio:9000/license_plate-recognition-images/', '')}?token=${token}`
                            : `/api/internal/${item.image_url}?token=${token}`
                        }
                          alt="LicensePlate"
                          className="detection-image"
                        />
                      ) : (
                        <div className="no-image">No Image</div>
                      )}
                    </div>
                    <div className="card-content">
                      <div className="card-info">
                        <h3>{item.profile_name}</h3>
                        <span className="camera-id">
                          Cam: {item.camera_id}
                          {getCameraName(item.camera_id) && ` — ${getCameraName(item.camera_id)}`}
                        </span>
                      </div>
                      <div className="card-actions">
                        {(userRole === 'admin' || userRole === 'manager') && (
                          <button
                            className="icon-btn delete-btn"
                            onClick={() => handleDelete(item.log_id)}
                            title="Xóa"
                          >
                            <Trash2 size={18} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Pagination Controls */}
            <div className="pagination">
              <button
                className="page-btn"
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                <ChevronLeft size={20} />
              </button>
              <span className="page-info">Trang {page}</span>
              <button
                className="page-btn"
                disabled={detections.length < limit}
                onClick={() => setPage(p => p + 1)}
              >
                <ChevronRight size={20} />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Export Excel Modal */}
      {showExportModal && (
        <div className="export-modal-overlay" onClick={() => setShowExportModal(false)}>
          <div className="export-modal glass-panel" onClick={(e) => e.stopPropagation()}>
            <div className="export-modal-header">
              <h2><FileSpreadsheet size={20} /> Xuất Báo Cáo Excel</h2>
              <button className="export-close-btn" onClick={() => setShowExportModal(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="export-modal-body">
              <div className="export-field">
                <label>Lọc theo Camera</label>
                <select value={exportCameraId} onChange={(e) => setExportCameraId(e.target.value)}>
                  <option value="">Tất cả Camera</option>
                  {cameraList.map(cam => (
                    <option key={cam.id} value={cam.id}>[{cam.id}] {cam.name}</option>
                  ))}
                </select>
              </div>

              {logType === 'recognition' && (
                <div className="export-field">
                  <label>Lọc theo Người nhận diện</label>
                  <select value={exportProfileId} onChange={(e) => setExportProfileId(e.target.value)}>
                    <option value="">Tất cả</option>
                    {profileList.map(p => (
                      <option key={p.id} value={p.id}>{p.name} (ID: {p.id})</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="export-field">
                <label>Thời gian bắt đầu</label>
                <input
                  type="datetime-local"
                  value={exportStartTime}
                  onChange={(e) => setExportStartTime(e.target.value)}
                />
              </div>

              <div className="export-field">
                <label>Thời gian kết thúc</label>
                <input
                  type="datetime-local"
                  value={exportEndTime}
                  onChange={(e) => setExportEndTime(e.target.value)}
                />
              </div>
            </div>

            <div className="export-modal-footer">
              <button className="drawer-btn-cancel" onClick={() => setShowExportModal(false)}>Hủy</button>
              <button
                className="drawer-btn-save"
                onClick={handleExportExcel}
                disabled={isExporting}
              >
                {isExporting ? 'Đang gửi...' : 'Xuất Báo Cáo'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

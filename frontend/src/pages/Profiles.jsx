import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getProfiles, createProfile, deleteProfile, getCameras } from '../services/api';
import './Dashboard.css';
import './Profiles.css';
import { Trash2, Plus, X } from 'lucide-react';
import Sidebar from '../components/Sidebar';

const Profiles = () => {
  const [profiles, setProfiles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Pagination & Filters
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const limit = 20;

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  // Camera list
  const [cameraList, setCameraList] = useState([]);

  const navigate = useNavigate();
  const location = useLocation();

  const fetchProfiles = async (currentPage = page, searchQuery = search) => {
    setIsLoading(true);
    try {
      const skip = (currentPage - 1) * limit;
      const data = await getProfiles(skip, limit, searchQuery);
      setProfiles(data.data || []);
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout();
      }
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchProfiles(page, search);
    fetchCameraList();
  }, [page, navigate]);

  const fetchCameraList = async () => {
    try {
      const res = await getCameras();
      setCameraList(res.data || []);
    } catch (err) {
      console.error('Error fetching cameras:', err);
    }
  };

  const userRole = localStorage.getItem('user_role') || 'viewer';

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('username');
    navigate('/login');
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa nhân viên này? Lịch sử nhận diện cũng sẽ bị mất.')) return;
    try {
      await deleteProfile(id);
      fetchProfiles(page, search);
    } catch (err) {
      alert('Lỗi xóa: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchProfiles(1, search);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!newName || !selectedFile) return;
    setIsUploading(true);
    setUploadError('');
    try {
      await createProfile(newName, selectedFile);
      setIsModalOpen(false);
      setNewName('');
      setSelectedFile(null);
      fetchProfiles(1, search); // Làm mới danh sách
    } catch (err) {
      setUploadError(err.response?.data?.detail || err.message);
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
          <h1>Quản Lý Nhân Sự</h1>
          
          <div className="header-actions">
            <form onSubmit={handleSearch} className="search-form">
              <input 
                type="text" 
                placeholder="Tìm theo tên..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="search-input"
              />
              <button type="submit" className="search-btn">Tìm</button>
            </form>

            <button className="btn-primary add-profile-btn" onClick={() => setIsModalOpen(true)}>
              <Plus size={18} />
              Thêm Mới
            </button>
          </div>
        </header>

        <div className="profiles-container glass-panel">
          {isLoading ? (
            <div className="loading-state">Đang tải dữ liệu...</div>
          ) : profiles.length === 0 ? (
            <div className="empty-state">Chưa có hồ sơ nhân sự nào.</div>
          ) : (
            <table className="profiles-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Tên Nhân Viên</th>
                  <th>Ngày Tạo</th>
                  <th>Hành Động</th>
                </tr>
              </thead>
              <tbody>
                {profiles.map(p => (
                  <tr key={p.id}>
                    <td>{p.id}</td>
                    <td>{p.name}</td>
                    <td>{p.created_at}</td>
                    <td>
                      <button className="icon-btn delete-btn" onClick={() => handleDelete(p.id)} title="Xóa">
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Create Modal */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel">
            <div className="modal-header">
              <h2>Thêm Nhân Sự Mới</h2>
              <button className="close-btn" onClick={() => setIsModalOpen(false)}>
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleCreateSubmit} className="modal-form">
              <div className="input-group">
                <label>Tên nhân viên</label>
                <input 
                  type="text" 
                  value={newName} 
                  onChange={(e) => setNewName(e.target.value)} 
                  required 
                  placeholder="Nhập tên..."
                />
              </div>
              <div className="input-group">
                <label>Ảnh biển số (Rõ nét)</label>
                <input 
                  type="file" 
                  accept="image/*" 
                  onChange={(e) => setSelectedFile(e.target.files[0])} 
                  required 
                />
              </div>
              {uploadError && <div className="error-msg">{uploadError}</div>}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>Hủy</button>
                <button type="submit" className="btn-primary" disabled={isUploading}>
                  {isUploading ? 'Đang xử lý...' : 'Thêm'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Profiles;

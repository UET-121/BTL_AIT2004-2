import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserPlus, RefreshCw, Trash2, Shield, Eye, X, Loader2,
  UserCheck, Users as UsersIcon,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { getUsers, createUser, deleteUser, updateUserRole } from '../services/api';
import Sidebar from '../components/Sidebar';
import './Users.css';

const ROLE_LABELS = {
  admin: 'Admin',
  manager: 'Manager',
  viewer: 'Viewer',
};

const Users = () => {
  const navigate = useNavigate();

  const userRole = localStorage.getItem('user_role') || 'viewer';
  const currentUsername = localStorage.getItem('username') || '';

  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Create form state
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('viewer');
  const [isCreating, setIsCreating] = useState(false);

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getUsers();
      setUsers(data);
    } catch (err) {
      toast.error('Không thể tải danh sách users: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('username');
    navigate('/login');
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (!newUsername.trim() || !newPassword.trim()) {
      toast.error('Vui lòng điền đầy đủ thông tin.');
      return;
    }
    setIsCreating(true);
    try {
      await createUser(newUsername.trim(), newPassword, newRole);
      toast.success(`Đã tạo tài khoản '${newUsername}' (${ROLE_LABELS[newRole]}) thành công!`);
      setShowCreateModal(false);
      setNewUsername('');
      setNewPassword('');
      setNewRole('viewer');
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Lỗi tạo tài khoản.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteUser = async (user) => {
    if (!window.confirm(`Bạn có chắc muốn xóa tài khoản "${user.username}"?`)) return;
    try {
      await deleteUser(user.id);
      toast.success(`Đã xóa tài khoản '${user.username}'.`);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Lỗi xóa tài khoản.');
    }
  };

  const handleRoleChange = async (user, newRoleValue) => {
    if (newRoleValue === user.role) return;
    try {
      await updateUserRole(user.id, newRoleValue);
      toast.success(`Đã đổi quyền '${user.username}' → ${ROLE_LABELS[newRoleValue]}.`);
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Lỗi đổi quyền.');
    }
  };

  // Stats
  const stats = {
    total: users.length,
    admin: users.filter(u => u.role === 'admin').length,
    manager: users.filter(u => u.role === 'manager').length,
    viewer: users.filter(u => u.role === 'viewer').length,
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      {/* Main Content */}
      <main className="main-content">
        <div style={{ padding: '1.5rem' }}>
          {/* Header */}
          <div className="users-header">
            <h1>Quản lý Tài khoản</h1>
            <div className="users-header-actions">
              <button className="btn-refresh" onClick={fetchUsers} disabled={isLoading}>
                <RefreshCw size={15} className={isLoading ? 'spin' : ''} />
                Làm mới
              </button>
              <button className="btn-create-user" onClick={() => setShowCreateModal(true)}>
                <UserPlus size={16} />
                Tạo tài khoản
              </button>
            </div>
          </div>

          {/* Stat Cards */}
          <div className="users-stats">
            <div className="users-stat-card">
              <div className="users-stat-icon total"><UsersIcon size={18} /></div>
              <div className="users-stat-info">
                <div className="stat-num">{stats.total}</div>
                <div className="stat-label">Tổng tài khoản</div>
              </div>
            </div>
            <div className="users-stat-card">
              <div className="users-stat-icon admin"><Shield size={18} /></div>
              <div className="users-stat-info">
                <div className="stat-num">{stats.admin}</div>
                <div className="stat-label">Admin</div>
              </div>
            </div>
            <div className="users-stat-card">
              <div className="users-stat-icon manager"><UserCheck size={18} /></div>
              <div className="users-stat-info">
                <div className="stat-num">{stats.manager}</div>
                <div className="stat-label">Manager</div>
              </div>
            </div>
            <div className="users-stat-card">
              <div className="users-stat-icon viewer"><Eye size={18} /></div>
              <div className="users-stat-info">
                <div className="stat-num">{stats.viewer}</div>
                <div className="stat-label">Viewer</div>
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="users-table-container glass-panel">
            {isLoading ? (
              <div className="users-loading">
                <div className="users-spinner" />
                <span>Đang tải danh sách tài khoản...</span>
              </div>
            ) : users.length === 0 ? (
              <div className="users-empty">
                <UsersIcon size={40} style={{ opacity: 0.3 }} />
                <span>Chưa có tài khoản nào.</span>
              </div>
            ) : (
              <table className="users-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Tài khoản</th>
                    <th>Quyền hạn</th>
                    <th>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(user => (
                    <tr key={user.id}>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>#{user.id}</td>
                      <td>
                        <div className="user-info-cell">
                          <div className={`user-avatar role-${user.role}`}>
                            {user.username.charAt(0).toUpperCase()}
                          </div>
                          <span className="user-name">
                            {user.username}
                            {user.username === currentUsername && (
                              <span className="current-user-tag">(bạn)</span>
                            )}
                          </span>
                        </div>
                      </td>
                      <td>
                        {userRole === 'admin' && user.username !== currentUsername ? (
                          <select
                            className="role-select"
                            value={user.role}
                            onChange={(e) => handleRoleChange(user, e.target.value)}
                          >
                            <option value="viewer">Viewer</option>
                            <option value="manager">Manager</option>
                            <option value="admin">Admin</option>
                          </select>
                        ) : (
                          <span className={`role-badge ${user.role}`}>
                            {ROLE_LABELS[user.role]}
                          </span>
                        )}
                      </td>
                      <td>
                        <div className="users-actions-cell">
                          <button
                            className="btn-delete-user"
                            onClick={() => handleDeleteUser(user)}
                            disabled={
                              user.username === currentUsername ||
                              (userRole === 'manager' && user.role !== 'viewer')
                            }
                            title={
                              user.username === currentUsername
                                ? 'Không thể xóa tài khoản của chính mình'
                                : userRole === 'manager' && user.role !== 'viewer'
                                ? 'Manager chỉ được xóa tài khoản Viewer'
                                : `Xóa ${user.username}`
                            }
                          >
                            <Trash2 size={13} />
                            Xóa
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3><UserPlus size={18} /> Tạo tài khoản mới</h3>
              <button className="modal-close-btn" onClick={() => setShowCreateModal(false)}>
                <X size={16} />
              </button>
            </div>
            <form className="modal-form" onSubmit={handleCreateUser}>
              <div className="form-field">
                <label>Tên đăng nhập</label>
                <input
                  type="text"
                  placeholder="Nhập username..."
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  autoFocus
                  required
                  minLength={3}
                  maxLength={50}
                />
              </div>
              <div className="form-field">
                <label>Mật khẩu</label>
                <input
                  type="password"
                  placeholder="Tối thiểu 6 ký tự..."
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
              <div className="form-field">
                <label>Quyền hạn</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                >
                  <option value="viewer">Viewer — Xem dữ liệu</option>
                  {userRole === 'admin' && (
                    <>
                      <option value="manager">Manager — Quản lý Camera & Profiles</option>
                      <option value="admin">Admin — Toàn quyền</option>
                    </>
                  )}
                </select>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-modal-cancel"
                  onClick={() => setShowCreateModal(false)}
                >
                  Hủy
                </button>
                <button type="submit" className="btn-modal-submit" disabled={isCreating}>
                  {isCreating ? <Loader2 size={15} className="spin" /> : <UserPlus size={15} />}
                  {isCreating ? 'Đang tạo...' : 'Tạo tài khoản'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;

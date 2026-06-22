import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { login } from '../services/api';
import './Login.css';
import { Lock, User, Eye, EyeOff, Loader2 } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Check if redirected due to expired session
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('expired') === 'true') {
      toast.error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.', {
        duration: 5000,
        id: 'session-expired',
      });
      // Clean the URL without reloading
      window.history.replaceState({}, '', '/login');
    }
  }, [location.search]);

  // If already logged in, redirect to dashboard
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const validate = () => {
    const errors = {};
    if (!username.trim()) {
      errors.username = 'Vui lòng nhập tên đăng nhập';
    } else if (username.trim().length < 3) {
      errors.username = 'Tên đăng nhập phải có ít nhất 3 ký tự';
    }
    if (!password) {
      errors.password = 'Vui lòng nhập mật khẩu';
    } else if (password.length < 3) {
      errors.password = 'Mật khẩu phải có ít nhất 3 ký tự';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (!validate()) return;

    setIsLoading(true);
    try {
      const data = await login(username.trim(), password);
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('username', data.username || username.trim());
      if (data.role) {
        localStorage.setItem('user_role', data.role);
      } else {
        // Fallback to viewer (least privilege) if backend doesn't return role
        localStorage.setItem('user_role', 'viewer');
      }
      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      const status = err.response?.status;
      if (status === 401) {
        setError('Tên đăng nhập hoặc mật khẩu không đúng.');
      } else if (status === 422) {
        setError('Dữ liệu đăng nhập không hợp lệ. Vui lòng kiểm tra lại.');
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Đăng nhập thất bại. Vui lòng thử lại.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <Toaster position="top-center" />
      <div className="login-box glass-panel">
        <div className="login-logo">
          <div className="logo-icon">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="12" fill="url(#logo-grad)" />
              <path d="M12 14C12 14 14 10 20 10C26 10 28 14 28 14" stroke="white" strokeWidth="2" strokeLinecap="round" />
              <circle cx="16" cy="18" r="2" fill="white" />
              <circle cx="24" cy="18" r="2" fill="white" />
              <path d="M14 24C14 24 16 28 20 28C24 28 26 24 26 24" stroke="white" strokeWidth="2" strokeLinecap="round" />
              <defs>
                <linearGradient id="logo-grad" x1="0" y1="0" x2="40" y2="40">
                  <stop stopColor="#6366f1" />
                  <stop offset="1" stopColor="#a855f7" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>
        <h2 className="login-title text-gradient">Real-Time Lpr Recognition</h2>
        <p className="login-subtitle">Đăng nhập vào hệ thống quản trị</p>

        {error && (
          <div className="error-message" role="alert">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" style={{ flexShrink: 0 }}>
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zM7 5a1 1 0 112 0v3a1 1 0 01-2 0V5zm1 7a1 1 0 100-2 1 1 0 000 2z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} noValidate>
          <div className={`input-group ${fieldErrors.username ? 'has-error' : ''}`}>
            <User size={20} className="input-icon" />
            <input
              id="login-username"
              type="text"
              placeholder="Tên đăng nhập"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value);
                if (fieldErrors.username) setFieldErrors(prev => ({ ...prev, username: '' }));
              }}
              autoComplete="username"
              autoFocus
            />
            {fieldErrors.username && <span className="field-error">{fieldErrors.username}</span>}
          </div>

          <div className={`input-group ${fieldErrors.password ? 'has-error' : ''}`}>
            <Lock size={20} className="input-icon" />
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Mật khẩu"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) setFieldErrors(prev => ({ ...prev, password: '' }));
              }}
              autoComplete="current-password"
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              tabIndex={-1}
              aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
            {fieldErrors.password && <span className="field-error">{fieldErrors.password}</span>}
          </div>

          <button type="submit" className="login-btn" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 size={18} className="spin-icon" />
                Đang đăng nhập...
              </>
            ) : (
              'Đăng nhập'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Save, Send, Loader2, CheckCircle, XCircle, Shield, Bell, Activity, Sliders
} from 'lucide-react';
import { getWebhookConfig, updateWebhookConfig, testWebhook, getAiConfig, updateDetectThresholds, updateRecognitionThreshold } from '../services/api';
import Sidebar from '../components/Sidebar';
import toast from 'react-hot-toast';
import './Dashboard.css';
import './Webhooks.css';

const EVENT_OPTIONS = [
  { key: 'stranger_detected', label: 'Phát hiện biển số Người lạ (Stranger Detected)', icon: '👤' },
  { key: 'staff_detected', label: 'Phát hiện biển số Nhân viên (Staff Detected)', icon: '🧑‍💼' },
  { key: 'camera_error', label: 'Camera bị lỗi kết nối (Camera Connection Error)', icon: '📹' },
];

const Webhooks = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const userRole = localStorage.getItem('user_role') || 'viewer';

  const [url, setUrl] = useState('');
  const [secret, setSecret] = useState('');
  const [isActive, setIsActive] = useState(false);
  const [events, setEvents] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [testResult, setTestResult] = useState(null);

  // AI Config State
  const [confThres, setConfThres] = useState(0.5);
  const [iouThres, setIouThres] = useState(0.4);
  const [faceMatchThres, setFaceMatchThres] = useState(0.5);
  const [isSavingAi, setIsSavingAi] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setIsLoading(true);
    try {
      const [webhookData, aiData] = await Promise.all([
        getWebhookConfig().catch(() => ({})),
        getAiConfig().catch(() => ({}))
      ]);

      setUrl(webhookData.url || '');
      setSecret(webhookData.secret || '');
      setIsActive(webhookData.is_active || false);
      setEvents(webhookData.events || []);

      if (aiData) {
        setConfThres(aiData.conf_thres ?? 0.5);
        setIouThres(aiData.iou_thres ?? 0.4);
        setFaceMatchThres(aiData.license_plate_match_threshold ?? 0.5);
      }
    } catch {
      // API may not exist yet – that's OK
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleEvent = (eventKey) => {
    setEvents(prev =>
      prev.includes(eventKey)
        ? prev.filter(e => e !== eventKey)
        : [...prev, eventKey]
    );
  };

  const handleSave = async () => {
    if (!url.trim()) {
      toast.error('Vui lòng nhập URL Webhook');
      return;
    }
    setIsSaving(true);
    try {
      await updateWebhookConfig({ url, secret, is_active: isActive, events });
      toast.success('Đã lưu cấu hình Webhook');
    } catch (err) {
      toast.error('Lỗi: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    if (!url.trim()) {
      toast.error('Vui lòng nhập URL Webhook trước');
      return;
    }
    setIsTesting(true);
    setTestResult(null);
    try {
      await testWebhook(url);
      setTestResult('success');
      toast.success('Gửi test thành công! Kiểm tra kênh nhận.');
    } catch (err) {
      setTestResult('error');
      toast.error('Test thất bại: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveAiConfig = async () => {
    setIsSavingAi(true);
    try {
      await updateDetectThresholds(confThres, iouThres);
      await updateRecognitionThreshold(faceMatchThres);
      toast.success('Đã lưu cấu hình AI toàn hệ thống');
    } catch (err) {
      toast.error('Lỗi khi lưu cấu hình AI: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsSavingAi(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    navigate('/login');
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />

      {/* Main Content */}
      <main className="main-content">
        <header className="content-header">
          <h1>Settings</h1>
        </header>

        {isLoading ? (
          <div className="loading-state">Đang tải cấu hình...</div>
        ) : (
          <div className="webhook-container">
            {/* Webhook URL */}
            <div className="webhook-card glass-panel">
              <div className="webhook-card-header">
                <Bell size={20} />
                <h3>Cấu hình Webhook</h3>
                <div className="webhook-active-toggle">
                  <span className="toggle-label-text">{isActive ? 'Đang bật' : 'Đang tắt'}</span>
                  <button
                    className={`toggle-switch ${isActive ? 'on' : 'off'}`}
                    onClick={() => setIsActive(!isActive)}
                  >
                    <div className="toggle-knob" />
                  </button>
                </div>
              </div>

              <div className="webhook-form">
                <div className="webhook-field">
                  <label htmlFor="webhook-url">URL Webhook</label>
                  <input
                    id="webhook-url"
                    type="url"
                    placeholder="https://discord.com/api/webhooks/... hoặc https://your-system.com/api/event"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                </div>

                <div className="webhook-field">
                  <label htmlFor="webhook-secret">
                    <Shield size={14} /> Secret Token (HMAC-SHA256)
                  </label>
                  <input
                    id="webhook-secret"
                    type="password"
                    placeholder="Chuỗi bảo mật để ký số payload"
                    value={secret}
                    onChange={(e) => setSecret(e.target.value)}
                  />
                  <span className="field-hint">Hệ thống đích sẽ dùng token này để xác thực nguồn gửi.</span>
                </div>
              </div>
            </div>

            {/* Event Triggers */}
            <div className="webhook-card glass-panel">
              <div className="webhook-card-header">
                <Activity size={20} />
                <h3>Sự kiện kích hoạt (Event Triggers)</h3>
              </div>

              <div className="webhook-events">
                {EVENT_OPTIONS.map(evt => (
                  <label key={evt.key} className={`event-option ${events.includes(evt.key) ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      checked={events.includes(evt.key)}
                      onChange={() => handleToggleEvent(evt.key)}
                    />
                    <span className="event-icon">{evt.icon}</span>
                    <span className="event-label">{evt.label}</span>
                    {events.includes(evt.key) && <CheckCircle size={16} className="event-check" />}
                  </label>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="webhook-actions">
              <button
                className="webhook-test-btn"
                onClick={handleTest}
                disabled={isTesting || !url.trim()}
              >
                {isTesting ? (
                  <><Loader2 size={16} className="spin-icon" /> Đang gửi...</>
                ) : (
                  <><Send size={16} /> Gửi Test</>
                )}
                {testResult === 'success' && <CheckCircle size={16} className="test-success" />}
                {testResult === 'error' && <XCircle size={16} className="test-error" />}
              </button>

              <button
                className="webhook-save-btn"
                onClick={handleSave}
                disabled={isSaving}
              >
                {isSaving ? (
                  <><Loader2 size={16} className="spin-icon" /> Đang lưu...</>
                ) : (
                  <><Save size={16} /> Lưu Cấu Hình</>
                )}
              </button>
            </div>

            {/* AI Settings */}
            <div className="webhook-card glass-panel" style={{ marginTop: '2rem' }}>
              <div className="webhook-card-header">
                <Sliders size={20} />
                <h3>Cấu Hình AI (AI Thresholds)</h3>
              </div>

              <div className="webhook-form">
                <div className="webhook-field">
                  <label htmlFor="conf-thres">Ngưỡng Confidence (0.1 - 1.0)</label>
                  <input
                    id="conf-thres"
                    type="number"
                    step="0.05"
                    min="0.1"
                    max="1.0"
                    value={confThres}
                    onChange={(e) => setConfThres(parseFloat(e.target.value))}
                  />
                  <span className="field-hint">Ngưỡng tin cậy tối thiểu để nhận diện một đối tượng là biển số.</span>
                </div>

                <div className="webhook-field">
                  <label htmlFor="iou-thres">Ngưỡng IoU (0.1 - 1.0)</label>
                  <input
                    id="iou-thres"
                    type="number"
                    step="0.05"
                    min="0.1"
                    max="1.0"
                    value={iouThres}
                    onChange={(e) => setIouThres(parseFloat(e.target.value))}
                  />
                  <span className="field-hint">Ngưỡng giao nhau để gộp các bounding boxes trùng lặp (NMS).</span>
                </div>

                <div className="webhook-field">
                  <label htmlFor="license_plate-match-thres">Ngưỡng Nhận Diện Biển Số (0.1 - 1.0)</label>
                  <input
                    id="license_plate-match-thres"
                    type="number"
                    step="0.05"
                    min="0.1"
                    max="1.0"
                    value={faceMatchThres}
                    onChange={(e) => setFaceMatchThres(parseFloat(e.target.value))}
                  />
                  <span className="field-hint">Độ tương đồng (Cosine Similarity) tối thiểu để xác định danh tính một người. Càng cao càng khắt khe.</span>
                </div>
              </div>

              <div className="webhook-actions" style={{ marginTop: '1rem' }}>
                <button
                  className="webhook-save-btn"
                  onClick={handleSaveAiConfig}
                  disabled={isSavingAi}
                >
                  {isSavingAi ? (
                    <><Loader2 size={16} className="spin-icon" /> Đang lưu...</>
                  ) : (
                    <><Save size={16} /> Lưu Cấu Hình AI</>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Webhooks;

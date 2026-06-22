import React, { useState, useEffect } from 'react';
import { X, Save, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

const RTSP_REGEX = /^rtsp:\/\/.+/;

const CameraDrawer = ({ isOpen, onClose, onSave, editCamera = null }) => {
  const [camId, setCamId] = useState('');
  const [camName, setCamName] = useState('');
  const [camUrl, setCamUrl] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [urlTouched, setUrlTouched] = useState(false);

  const isEdit = !!editCamera;
  const isUrlValid = RTSP_REGEX.test(camUrl);

  useEffect(() => {
    if (editCamera) {
      setCamId(String(editCamera.id || ''));
      setCamName(editCamera.name || '');
      setCamUrl(editCamera.link || editCamera.rtsp_url || '');
      setUrlTouched(true);
    } else {
      setCamId('');
      setCamName('');
      setCamUrl('');
      setUrlTouched(false);
    }
  }, [editCamera, isOpen]);

  const handleSave = async (e) => {
    e.preventDefault();
    if (!camId.trim() || !camName.trim() || !camUrl.trim()) return;
    if (!isUrlValid) return;

    setIsSaving(true);
    try {
      await onSave({ id: camId.trim(), name: camName.trim(), url: camUrl.trim() }, isEdit);
      onClose();
    } catch {
      // Error handled by parent
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="drawer-backdrop" onClick={onClose} />

      {/* Drawer Panel */}
      <div className={`drawer-panel glass-panel ${isOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <h2>{isEdit ? 'Sửa Camera' : 'Thêm Camera Mới'}</h2>
          <button className="drawer-close" onClick={onClose} aria-label="Đóng">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSave} className="drawer-form">
          {/* Basic Info Section */}
          <div className="drawer-section">
            <h3 className="drawer-section-title">Thông tin cơ bản</h3>

            <div className="drawer-field">
              <label htmlFor="drawer-cam-name">Tên Camera</label>
              <input
                id="drawer-cam-name"
                type="text"
                placeholder="VD: Camera Hành Lang Tầng 2"
                value={camName}
                onChange={(e) => setCamName(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="drawer-field">
              <label htmlFor="drawer-cam-id">Mã Camera (ID)</label>
              <input
                id="drawer-cam-id"
                type="text"
                placeholder="VD: 1, 2, 3"
                value={camId}
                onChange={(e) => setCamId(e.target.value)}
                required
                disabled={isEdit}
                className={isEdit ? 'disabled-input' : ''}
              />
              <span className="field-hint">Mã định danh duy nhất, không dấu, không khoảng trắng.</span>
            </div>
          </div>

          {/* Connection Config Section */}
          <div className="drawer-section">
            <h3 className="drawer-section-title">Cấu hình kết nối</h3>

            <div className="drawer-field">
              <label htmlFor="drawer-cam-url">Đường dẫn RTSP Stream</label>
              <input
                id="drawer-cam-url"
                type="text"
                placeholder="rtsp://admin:password@192.168.1.100:554/stream"
                value={camUrl}
                onChange={(e) => {
                  setCamUrl(e.target.value);
                  if (!urlTouched) setUrlTouched(true);
                }}
                required
                className={urlTouched ? (isUrlValid ? 'input-valid' : 'input-invalid') : ''}
              />
              {urlTouched && (
                <span className={`rtsp-validation ${isUrlValid ? 'valid' : 'invalid'}`}>
                  {isUrlValid ? (
                    <><CheckCircle size={14} /> Định dạng RTSP hợp lệ</>
                  ) : (
                    <><AlertCircle size={14} /> URL phải bắt đầu bằng rtsp://...</>
                  )}
                </span>
              )}
              <span className="field-hint">
                Mẫu: rtsp://admin:password@ip_address:port/h264
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="drawer-actions">
            <button type="button" className="drawer-btn-cancel" onClick={onClose}>
              Hủy bỏ
            </button>
            <button
              type="submit"
              className="drawer-btn-save"
              disabled={isSaving || !camId.trim() || !camName.trim() || (urlTouched && !isUrlValid)}
            >
              {isSaving ? (
                <><Loader2 size={16} className="spin-icon" /> Đang lưu...</>
              ) : (
                <><Save size={16} /> Lưu Cấu Hình</>
              )}
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default CameraDrawer;

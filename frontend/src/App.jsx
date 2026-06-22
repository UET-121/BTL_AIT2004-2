import React, { useEffect, useRef } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Vision from './pages/Vision';
import Profiles from './pages/Profiles';
import Webhooks from './pages/Webhooks';
import Monitoring from './pages/Monitoring';
import Users from './pages/Users';
import ProtectedRoute from './components/ProtectedRoute';
import toast, { Toaster } from 'react-hot-toast';

function App() {
  const lastToastedAt = useRef({});
  const wsRef = useRef(null);

  React.useEffect(() => {
    if (wsRef.current) return;

    const token = localStorage.getItem('access_token');
    if (!token) return; // Don't connect WS if not logged in

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws/notifications/`;
    let ws;
    let reconnectTimeout;

    const connectWebSocket = () => {
      console.log('[WS] Attempting to connect to:', wsUrl);
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[WS] Connected successfully to', wsUrl);
      };

      ws.onclose = (e) => {
        console.log('[WS] Connection closed', e.reason);
        // Tự động kết nối lại sau 3 giây nếu bị đóng
        reconnectTimeout = setTimeout(() => {
          if (!wsRef.current) connectWebSocket();
        }, 3000);
      };

      ws.onerror = (e) => {
        console.error('[WS] Error:', e);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          console.log('[WS] Received message:', msg.topic, msg);

        // ── LicensePlate Detection Notifications ──
        if (msg.topic && msg.topic.startsWith('ui.license_plate.detected')) {
          const boxes = msg.data?.boxes || [];
          const camId = msg.data?.camera_id || 'Unknown';
          const now = Date.now();

          boxes.forEach(box => {
            if (!box.track_id) return;

            const lastToastTime = lastToastedAt.current[box.track_id] || 0;

            if (now - lastToastTime > 10000) {

              lastToastedAt.current[box.track_id] = now;

              toast.success(`Phát hiện đối tượng (ID: ${box.track_id}) tại Camera ${camId}`);
            }
          });
        }

        // ── Export Completed Notification ──
        if (msg.topic === 'ui.export.completed') {
          const downloadUrl = msg.data?.download_url;
          const message = msg.data?.message || 'Báo cáo Excel đã sẵn sàng!';

          if (downloadUrl) {
            const accessToken = localStorage.getItem('access_token');
            const fullUrl = `${window.location.origin}${downloadUrl}?token=${accessToken}`;

            // Tự động tải xuống
            const a = document.createElement('a');
            a.href = fullUrl;
            a.download = '';
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            toast.success(`${message} (File đang được tải về...)`, { duration: 5000 });
          } else {
            toast.success(message, { duration: 5000 });
          }
        }
        // ── Export Error Notification ──
        if (msg.topic === 'ui.export.error') {
          const message = msg.data?.message || 'Có lỗi xảy ra khi xuất dữ liệu.';
          toast.error(`Lỗi xuất dữ liệu: ${message}`, { duration: 10000 });
        }
      } catch (e) {
        console.error('[WS] Parse Error:', e);
      }
    }; // End of ws.onmessage
    
  }; // End of connectWebSocket()
  
  connectWebSocket();
  wsRef.current = true;

  return () => {
    console.log('[WS] Cleanup called, closing websocket');
    if (ws) {
      ws.onclose = null; // Prevent reconnect loop on unmount
      ws.close();
    }
    clearTimeout(reconnectTimeout);
    wsRef.current = null;
  };
}, []);

  return (
    <>
      <Toaster position="bottom-right" />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<Login />} />

        {/* Dashboard is accessible by all users */}
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />

        {/* Admin and Manager routes */}
        <Route path="/profiles" element={<ProtectedRoute allowedRoles={['admin', 'manager']}><Profiles /></ProtectedRoute>} />
        <Route path="/vision" element={<ProtectedRoute allowedRoles={['admin', 'manager']}><Vision /></ProtectedRoute>} />
        <Route path="/monitoring" element={<ProtectedRoute allowedRoles={['admin', 'manager']}><Monitoring /></ProtectedRoute>} />

        {/* Admin-only routes */}
        <Route path="/webhooks" element={<ProtectedRoute allowedRoles={['admin']}><Webhooks /></ProtectedRoute>} />

        {/* Admin and Manager: User management */}
        <Route path="/users" element={<ProtectedRoute allowedRoles={['admin', 'manager']}><Users /></ProtectedRoute>} />

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
}

export default App;

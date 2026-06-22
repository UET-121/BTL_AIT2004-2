import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Power, MonitorOff } from 'lucide-react';

const LiveStreamModal = ({ isOpen, camera, onClose, onStopAI }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const wsRef = useRef(null);
  const drawFrameRef = useRef(null);
  const latestBoxesRef = useRef([]);
  const [status, setStatus] = useState('connecting');

  const cleanup = useCallback(() => {
    if (drawFrameRef.current) {
      cancelAnimationFrame(drawFrameRef.current);
      drawFrameRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    latestBoxesRef.current = [];
    setStatus('disconnected');
  }, []);

  const renderCanvas = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (video.videoWidth > 0 && video.videoHeight > 0) {
      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const boxes = latestBoxesRef.current;

      boxes.forEach(box => {
        const [x_min, y_min, x_max, y_max] = box.bbox;
        const width = x_max - x_min;
        const height = y_max - y_min;

        // Draw bounding box
        const isKnown = box.profile_name && box.profile_name !== 'Unknown';
        ctx.strokeStyle = isKnown ? '#10b981' : '#f59e0b';
        ctx.lineWidth = 3;
        ctx.strokeRect(x_min, y_min, width, height);

        // Draw label background
        const label = box.profile_name || `ID: ${box.track_id}`;
        ctx.font = 'bold 16px Inter, sans-serif';
        const textWidth = ctx.measureText(label).width;
        ctx.fillStyle = isKnown ? 'rgba(16, 185, 129, 0.85)' : 'rgba(245, 158, 11, 0.85)';
        ctx.fillRect(x_min, y_min - 24, textWidth + 12, 24);

        // Draw label text
        ctx.fillStyle = '#ffffff';
        ctx.fillText(label, x_min + 6, y_min - 6);
      });
    }

    drawFrameRef.current = requestAnimationFrame(renderCanvas);
  }, []);

  const startWebRTC = useCallback(async (camId) => {
    try {
      setStatus('connecting');

      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        iceTransportPolicy: 'all',
      });
      peerConnectionRef.current = pc;

      pc.addTransceiver('video', { direction: 'recvonly' });

      pc.ontrack = (event) => {
        if (videoRef.current) {
          videoRef.current.srcObject = event.streams[0];
          setStatus('streaming');
          if (!drawFrameRef.current) {
            drawFrameRef.current = requestAnimationFrame(renderCanvas);
          }
        }
      };

      pc.onconnectionstatechange = () => {
        if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
          setStatus('error');
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Wait for ICE gathering
      await new Promise((resolve) => {
        if (pc.iceGatheringState === 'complete') {
          resolve();
        } else {
          pc.onicegatheringstatechange = () => {
            if (pc.iceGatheringState === 'complete') resolve();
          };
          setTimeout(resolve, 3000);
        }
      });

      const webrtcUrl = `/whep/cam_${camId}/whep`;
      const response = await fetch(webrtcUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: pc.localDescription.sdp,
      });

      if (!response.ok) {
        throw new Error('Không thể kết nối WebRTC');
      }

      const answerSdp = await response.text();
      await pc.setRemoteDescription(
        new RTCSessionDescription({ type: 'answer', sdp: answerSdp })
      );
    } catch (err) {
      console.error('WebRTC error:', err.message);
      setStatus('error');
    }
  }, [renderCanvas]);

  // Connect WebSocket for bounding boxes
  useEffect(() => {
    if (!isOpen || !camera) return;

    const camId = camera.id;

    // Start WebRTC
    startWebRTC(camId);

    // Connect WebSocket for license_plate detection boxes
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/notifications/`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.topic === `ui.license_plate.detected.${camId}`) {
          latestBoxesRef.current = msg.data?.boxes || [];
        }
      } catch {
        // Ignore parse errors
      }
    };

    wsRef.current = ws;

    return () => {
      cleanup();
    };
  }, [isOpen, camera, startWebRTC, cleanup]);

  const handleCloseView = () => {
    cleanup();
    onClose(false); // false = don't stop AI
  };

  const handleStopAIAndClose = () => {
    cleanup();
    onStopAI(camera.id);
    onClose(true); // true = AI stopped
  };

  if (!isOpen || !camera) return null;

  return (
    <div className="stream-modal-overlay" onClick={handleCloseView}>
      <div className="stream-modal glass-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="stream-modal-header">
          <div className="stream-modal-title">
            <div className={`stream-status-dot ${status}`} />
            <h3>
              {camera.name}
              <span className="stream-cam-id">ID: {camera.id}</span>
            </h3>
          </div>
          <button className="stream-close-btn" onClick={handleCloseView} aria-label="Đóng">
            <X size={20} />
          </button>
        </div>

        {/* Video Area */}
        <div className="stream-video-container">
          {status === 'connecting' && (
            <div className="stream-loading">
              <div className="stream-spinner" />
              <p>Đang kết nối camera...</p>
            </div>
          )}
          {status === 'error' && (
            <div className="stream-loading">
              <MonitorOff size={48} />
              <p>Không thể kết nối. Camera có thể chưa được bật.</p>
            </div>
          )}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              display: status === 'streaming' ? 'block' : 'none',
            }}
          />
          <canvas
            ref={canvasRef}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              pointerEvents: 'none',
              zIndex: 5,
              display: status === 'streaming' ? 'block' : 'none',
            }}
          />
        </div>

        {/* Footer Actions */}
        <div className="stream-modal-footer">
          <div className="stream-action-group">
            <button
              className="stream-btn-close-view"
              onClick={handleCloseView}
              title="Chỉ đóng màn hình xem. AI vẫn tiếp tục xử lý camera này trên backend."
            >
              <MonitorOff size={16} />
              Đóng màn hình
            </button>
            <span className="stream-tooltip">AI vẫn chạy ngầm</span>
          </div>
          <div className="stream-action-group">
            <button
              className="stream-btn-stop-ai"
              onClick={handleStopAIAndClose}
              title="Đóng màn hình VÀ tắt hoàn toàn AI Worker cho camera này. Camera sẽ ngừng xử lý."
            >
              <Power size={16} />
              Tắt AI &amp; Đóng
            </button>
            <span className="stream-tooltip danger">Tắt hoàn toàn camera</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveStreamModal;

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Cpu, Server, ActivitySquare, RefreshCw, AlertCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import './Dashboard.css';
import './Monitoring.css';

const PROMETHEUS_URL = '/prometheus/api/v1/query_range';

// Helper to format time (HH:mm:ss)
const formatTime = (unixTime) => {
  const date = new Date(unixTime * 1000);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const MetricChart = ({ title, subtitle, icon, query, unit, color, type = 'area' }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      const end = Math.floor(Date.now() / 1000);
      const start = end - 30 * 60; // last 30 minutes
      const step = 15; // 15 seconds resolution

      const response = await axios.get(PROMETHEUS_URL, {
        params: { query, start, end, step }
      });

      const results = response.data?.data?.result;
      if (results && results.length > 0) {
        const values = results[0].values;
        const formattedData = values.map(([timestamp, value]) => ({
          timeLabel: formatTime(timestamp),
          value: parseFloat(value)
        }));
        setData(formattedData);
      } else {
        setData([]);
      }
      setError(null);
    } catch (err) {
      console.error('Error fetching prometheus data:', err);
      setError('Không thể lấy dữ liệu từ Prometheus');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000); // refresh every 15s
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  const formatYAxis = (tick) => {
    if (unit === 'bytes') {
      if (tick === 0) return '0';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(tick) / Math.log(k));
      return parseFloat((tick / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    if (unit === 'percent') {
      return `${(tick * 100).toFixed(1)}%`;
    }
    return parseFloat(tick).toFixed(1);
  };

  const formatTooltip = (value) => {
    if (unit === 'bytes') {
      if (value === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(value) / Math.log(k));
      return parseFloat((value / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    if (unit === 'percent') {
      return `${(value * 100).toFixed(2)}%`;
    }
    return parseFloat(value).toFixed(2) + (unit ? ` ${unit}` : '');
  };

  return (
    <div className="metric-card glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '380px' }}>
      <div className="metric-card-header" style={{ marginBottom: '15px' }}>
        {icon}
        <div>
          <h3>{title}</h3>
          <span className="metric-subtitle">{subtitle}</span>
        </div>
      </div>
      <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
        {loading && data.length === 0 && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <RefreshCw size={24} className="spin-icon" style={{ color: 'var(--text-muted)' }} />
          </div>
        )}
        {error && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444', flexDirection: 'column', gap: '8px' }}>
            <AlertCircle size={32} />
            <p>{error}</p>
          </div>
        )}
        {!error && data.length === 0 && !loading && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <p>Không có dữ liệu</p>
          </div>
        )}
        {!error && data.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            {type === 'area' ? (
              <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id={`color-${title.replace(/\s+/g, '')}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={color} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="timeLabel" 
                  stroke="rgba(255,255,255,0.4)" 
                  fontSize={11}
                  tickMargin={10}
                  minTickGap={30}
                />
                <YAxis 
                  stroke="rgba(255,255,255,0.4)" 
                  fontSize={11} 
                  tickFormatter={formatYAxis}
                  width={55}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)' }}
                  itemStyle={{ color: '#fff', fontWeight: 600 }}
                  formatter={(value) => [formatTooltip(value), title]}
                  labelStyle={{ color: 'rgba(255,255,255,0.6)', marginBottom: '5px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="value" stroke={color} strokeWidth={2} fillOpacity={1} fill={`url(#color-${title.replace(/\s+/g, '')})`} isAnimationActive={false} />
              </AreaChart>
            ) : (
              <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="timeLabel" 
                  stroke="rgba(255,255,255,0.4)" 
                  fontSize={11}
                  tickMargin={10}
                  minTickGap={30}
                />
                <YAxis 
                  stroke="rgba(255,255,255,0.4)" 
                  fontSize={11} 
                  tickFormatter={formatYAxis}
                  width={55}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)' }}
                  itemStyle={{ color: '#fff', fontWeight: 600 }}
                  formatter={(value) => [formatTooltip(value), title]}
                  labelStyle={{ color: 'rgba(255,255,255,0.6)', marginBottom: '5px', fontSize: '12px' }}
                />
                <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

const Monitoring = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const userRole = localStorage.getItem('user_role') || 'viewer';

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
          <h1>📊 Giám Sát Hệ Thống</h1>
          <div className="header-actions">
            {/* Auto refresh is handled internally by charts */}
            <span style={{ color: 'var(--text-muted)', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#10b981', boxShadow: '0 0 8px #10b981' }}></div>
              Live (cập nhật mỗi 15s)
            </span>
          </div>
        </header>

        <div className="monitoring-info glass-panel" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
            Biểu đồ hiển thị dữ liệu trực tiếp từ <strong>Prometheus API</strong>, cung cấp cái nhìn chi tiết về hiệu năng của Backend (FastAPI).
          </p>
        </div>

        <div className="metrics-grid">
          <MetricChart
            title="Lưu lượng Truy cập API"
            subtitle="Số lượng request mỗi giây"
            icon={<ActivitySquare size={20} style={{ color: '#8b5cf6' }} />}
            query="sum(rate(http_requests_total[1m]))"
            unit="req/s"
            color="#8b5cf6"
            type="area"
          />

          <MetricChart
            title="Mức tiêu thụ RAM (Backend)"
            subtitle="Resident Memory Bytes"
            icon={<Server size={20} style={{ color: '#ec4899' }} />}
            query="sum(process_resident_memory_bytes)"
            unit="bytes"
            color="#ec4899"
            type="area"
          />

          <MetricChart
            title="Mức tiêu thụ CPU (Backend)"
            subtitle="Process CPU Time Rate"
            icon={<Cpu size={20} style={{ color: '#3b82f6' }} />}
            query="sum(rate(process_cpu_seconds_total[1m]))"
            unit="percent"
            color="#3b82f6"
            type="line"
          />
        </div>
      </main>
    </div>
  );
};

export default Monitoring;

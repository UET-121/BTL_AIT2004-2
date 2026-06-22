import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Camera, Video, Users, Webhook, Activity, LogOut, UserCheck, Settings
} from 'lucide-react';

/**
 * Shared sidebar component used by all pages.
 * Order: Detections → Profiles → Cameras → Users → Monitoring → Webhooks (admin only)
 */
const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const userRole = localStorage.getItem('user_role') || 'viewer';
  const isManagerOrAdmin = userRole === 'admin' || userRole === 'manager';

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('username');
    navigate('/login');
  };

  const navItem = (path, icon, label) => (
    <button
      key={path}
      className={`nav-item ${location.pathname === path ? 'active' : ''}`}
      onClick={() => navigate(path)}
    >
      {icon}
      {label}
    </button>
  );

  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-header">
        <h2 className="text-gradient">LicensePlate System</h2>
      </div>

      <nav className="sidebar-nav">
        {navItem('/dashboard', <Camera size={20} />, 'Detections')}

        {isManagerOrAdmin && (
          <>
            {navItem('/profiles', <UserCheck size={20} />, 'Profiles')}
            {navItem('/vision', <Video size={20} />, 'Cameras')}
            {navItem('/users', <Users size={20} />, 'Users')}
            {navItem('/monitoring', <Activity size={20} />, 'Monitoring')}
          </>
        )}

        {userRole === 'admin' && (
          navItem('/webhooks', <Settings size={20} />, 'Settings')
        )}
      </nav>

      <div className="sidebar-footer">
        <button className="nav-item logout-btn" onClick={handleLogout}>
          <LogOut size={20} />
          Logout
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;

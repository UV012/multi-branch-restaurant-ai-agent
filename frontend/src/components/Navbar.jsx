import React from 'react';
import { UtensilsCrossed, Sparkles, Shield, User, LogOut, Clock, ShoppingBag } from 'lucide-react';

export default function Navbar({
  currentView,
  onSwitchView,
  currentCustomer,
  currentStaff,
  onOpenCustomerAuth,
  onOpenStaffAuth,
  onOpenMyHistory,
  onCustomerLogout,
  onStaffLogout,
}) {
  return (
    <header className="navbar">
      {/* Brand */}
      <div className="nav-brand">
        <div className="brand-icon">
          <UtensilsCrossed size={22} />
        </div>
        <div>
          <span>GourmetBistro</span>
          <span style={{ color: 'var(--primary)', marginLeft: '4px' }}>AI</span>
        </div>
      </div>

      {/* Main View Switcher Tabs */}
      <div className="nav-tabs">
        <button
          className={`nav-tab-btn ${currentView === 'customer' ? 'active' : ''}`}
          onClick={() => onSwitchView('customer')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Sparkles size={15} /> Customer Dining & Chat
        </button>
        <button
          className={`nav-tab-btn ${currentView === 'admin' ? 'active' : ''}`}
          onClick={() => onSwitchView('admin')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Shield size={15} /> Staff Portal
        </button>
      </div>

      {/* User Actions */}
      <div className="nav-actions">
        {currentView === 'customer' ? (
          currentCustomer ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <button
                onClick={onOpenMyHistory}
                className="btn-outline btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <ShoppingBag size={14} /> My Activity
              </button>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
                <span className="badge badge-neutral" style={{ padding: '4px 8px' }}>
                  <User size={13} style={{ marginRight: '4px' }} />
                  {currentCustomer.name}
                </span>
                <button
                  onClick={onCustomerLogout}
                  title="Sign out"
                  style={{ color: 'var(--text-muted)', padding: '4px' }}
                >
                  <LogOut size={16} />
                </button>
              </div>
            </div>
          ) : (
            <button onClick={onOpenCustomerAuth} className="btn-primary btn-sm">
              <User size={14} /> Sign In / Register
            </button>
          )
        ) : (
          !currentStaff && (
            <button onClick={onOpenStaffAuth} className="btn-primary btn-sm">
              <Shield size={14} /> Staff Sign In
            </button>
          )
        )}
      </div>
    </header>
  );
}

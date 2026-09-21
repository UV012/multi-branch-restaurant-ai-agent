import React, { useState } from 'react';
import OrdersManager from './OrdersManager';
import ReservationsManager from './ReservationsManager';
import MenuManager from './MenuManager';
import BranchTableManager from './BranchTableManager';
import { ShoppingBag, Calendar, Utensils, MapPin, LogOut, Shield } from 'lucide-react';

export default function AdminLayout({ currentStaff, branches, onLogout, onRefreshBranches }) {
  const [activeTab, setActiveTab] = useState('orders'); // 'orders' | 'reservations' | 'menu' | 'branches'

  return (
    <div className="admin-container">
      {/* Staff Header */}
      <div className="admin-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--secondary)' }}>
              Staff Management Portal
            </span>
            <span className="badge badge-info" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Shield size={12} /> {currentStaff.role.toUpperCase()}
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            Logged in as <strong>{currentStaff.username}</strong>
            {currentStaff.branch_id
              ? ` • Branch ID #${currentStaff.branch_id}`
              : ' • All Branches (Superadmin)'}
          </p>
        </div>

        <button
          onClick={onLogout}
          className="btn-outline btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444' }}
        >
          <LogOut size={14} /> Staff Sign Out
        </button>
      </div>

      {/* Admin Tabs */}
      <div className="admin-tabs">
        <button
          className={`admin-tab ${activeTab === 'orders' ? 'active' : ''}`}
          onClick={() => setActiveTab('orders')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <ShoppingBag size={16} /> Live Orders
        </button>
        <button
          className={`admin-tab ${activeTab === 'reservations' ? 'active' : ''}`}
          onClick={() => setActiveTab('reservations')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Calendar size={16} /> Table Reservations
        </button>
        <button
          className={`admin-tab ${activeTab === 'menu' ? 'active' : ''}`}
          onClick={() => setActiveTab('menu')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Utensils size={16} /> Menu & Inventory Stock
        </button>
        <button
          className={`admin-tab ${activeTab === 'branches' ? 'active' : ''}`}
          onClick={() => setActiveTab('branches')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <MapPin size={16} /> Branches & Tables
        </button>
      </div>

      {/* Subtab Content */}
      {activeTab === 'orders' && (
        <OrdersManager currentStaff={currentStaff} branches={branches} />
      )}

      {activeTab === 'reservations' && (
        <ReservationsManager currentStaff={currentStaff} branches={branches} />
      )}

      {activeTab === 'menu' && (
        <MenuManager currentStaff={currentStaff} branches={branches} />
      )}

      {activeTab === 'branches' && (
        <BranchTableManager
          currentStaff={currentStaff}
          branches={branches}
          onRefreshBranches={onRefreshBranches}
        />
      )}
    </div>
  );
}

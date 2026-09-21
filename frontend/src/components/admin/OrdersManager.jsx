import React, { useState, useEffect } from 'react';
import { api } from '../../api';
import { ShoppingBag, RefreshCw, Check, Clock, Truck, XCircle, AlertCircle, ChevronRight } from 'lucide-react';

export default function OrdersManager({ currentStaff, branches }) {
  const [orders, setOrders] = useState([]);
  const [selectedBranchId, setSelectedBranchId] = useState(
    currentStaff.branch_id || (branches[0] ? branches[0].id : 1)
  );
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);
  const [error, setError] = useState('');

  const fetchOrders = async () => {
    setLoading(true);
    setError('');
    try {
      const bId = currentStaff.branch_id || selectedBranchId;
      const data = await api.getStaffOrders(bId, statusFilter || null);
      setOrders(data);
    } catch (err) {
      setError(err.message || 'Failed to load staff orders.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [selectedBranchId, statusFilter]);

  const handleUpdateStatus = async (orderId, newStatus) => {
    setUpdatingId(orderId);
    try {
      await api.updateOrderStatus(orderId, newStatus);
      await fetchOrders();
    } catch (err) {
      alert(`Failed to update order #${orderId}: ${err.message}`);
    } finally {
      setUpdatingId(null);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'placed':
        return <span className="badge badge-info">PLACED</span>;
      case 'preparing':
        return <span className="badge badge-warning">PREPARING</span>;
      case 'ready':
        return <span className="badge badge-success">READY</span>;
      case 'delivered':
        return <span className="badge badge-neutral">DELIVERED</span>;
      case 'cancelled':
        return <span className="badge badge-danger">CANCELLED</span>;
      default:
        return <span className="badge badge-neutral">{status.toUpperCase()}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Controls Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          background: 'white',
          padding: '1rem 1.25rem',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--surface-border)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {!currentStaff.branch_id && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>Branch:</label>
              <select
                value={selectedBranchId}
                onChange={(e) => setSelectedBranchId(Number(e.target.value))}
                style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
              >
                {branches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
            >
              <option value="">All Statuses</option>
              <option value="placed">Placed</option>
              <option value="preparing">Preparing</option>
              <option value="ready">Ready</option>
              <option value="delivered">Delivered</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        <button
          onClick={fetchOrders}
          disabled={loading}
          className="btn-outline btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh Orders
        </button>
      </div>

      {error && (
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', background: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: '8px', fontSize: '0.875rem' }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Orders List */}
      {loading && orders.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading live orders...
        </div>
      ) : orders.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', background: 'white', borderRadius: 'var(--radius-lg)', border: '1px solid var(--surface-border)', color: 'var(--text-muted)' }}>
          <ShoppingBag size={40} style={{ margin: '0 auto 8px', opacity: 0.4 }} />
          <p>No orders found matching the filter.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1rem' }}>
          {orders.map((o) => (
            <div
              key={o.id}
              style={{
                background: 'white',
                border: '1px solid var(--surface-border)',
                borderRadius: 'var(--radius-lg)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--secondary)' }}>
                      #{o.id}
                    </span>
                    <span style={{ fontSize: '0.8rem', background: '#f1f5f9', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                      {o.order_type.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Customer: <strong>{o.customer_name || 'Guest'}</strong>
                  </div>
                </div>
                {getStatusBadge(o.status)}
              </div>

              {/* Order Items */}
              <div
                style={{
                  background: '#f8fafc',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  fontSize: '0.85rem',
                }}
              >
                {o.items.map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>
                      {item.quantity}x Item #{item.menu_item_id}
                      {item.item_notes ? ` (${item.item_notes})` : ''}
                    </span>
                    <span style={{ fontWeight: 600 }}>
                      ${(Number(item.unit_price) * item.quantity).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              {o.delivery_address && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  <strong>Address:</strong> {o.delivery_address}
                </div>
              )}

              {o.special_notes && (
                <div style={{ fontSize: '0.8rem', color: '#9a3412', background: 'var(--primary-light)', padding: '6px 8px', borderRadius: '6px' }}>
                  <strong>Notes:</strong> {o.special_notes}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '6px', borderTop: '1px solid #f1f5f9' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {new Date(o.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--primary)' }}>
                  ${Number(o.total_amount).toFixed(2)}
                </span>
              </div>

              {/* Action Buttons for Status Flow */}
              <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                {o.status === 'placed' && (
                  <button
                    disabled={updatingId === o.id}
                    onClick={() => handleUpdateStatus(o.id, 'preparing')}
                    className="btn-primary btn-sm"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    <Clock size={14} /> Start Preparing
                  </button>
                )}

                {o.status === 'preparing' && (
                  <button
                    disabled={updatingId === o.id}
                    onClick={() => handleUpdateStatus(o.id, 'ready')}
                    className="btn-primary btn-sm"
                    style={{ flex: 1, justifyContent: 'center', background: '#10b981' }}
                  >
                    <Check size={14} /> Mark Ready
                  </button>
                )}

                {o.status === 'ready' && (
                  <button
                    disabled={updatingId === o.id}
                    onClick={() => handleUpdateStatus(o.id, 'delivered')}
                    className="btn-secondary btn-sm"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    <Truck size={14} /> Complete / Delivered
                  </button>
                )}

                {o.status !== 'cancelled' && o.status !== 'delivered' && (
                  <button
                    disabled={updatingId === o.id}
                    onClick={() => {
                      if (confirm(`Cancel order #${o.id}?`)) {
                        handleUpdateStatus(o.id, 'cancelled');
                      }
                    }}
                    className="btn-outline btn-sm"
                    style={{ color: '#ef4444' }}
                    title="Cancel Order"
                  >
                    <XCircle size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

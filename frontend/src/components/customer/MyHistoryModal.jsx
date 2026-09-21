import React, { useState, useEffect } from 'react';
import { api } from '../../api';
import { X, ShoppingBag, Calendar, RefreshCw, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function MyHistoryModal({ isOpen, onClose }) {
  const [tab, setTab] = useState('orders'); // 'orders' | 'reservations'
  const [orders, setOrders] = useState([]);
  const [reservations, setReservations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      if (tab === 'orders') {
        const data = await api.getMyOrders();
        setOrders(data);
      } else {
        const data = await api.getMyReservations();
        setReservations(data);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch your history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen, tab]);

  if (!isOpen) return null;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'confirmed':
      case 'ready':
      case 'delivered':
        return <span className="badge badge-success">{status.toUpperCase()}</span>;
      case 'preparing':
      case 'pending':
        return <span className="badge badge-warning">{status.toUpperCase()}</span>;
      case 'cancelled':
        return <span className="badge badge-danger">{status.toUpperCase()}</span>;
      default:
        return <span className="badge badge-info">{status.toUpperCase()}</span>;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: '650px', maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className={`nav-tab-btn ${tab === 'orders' ? 'active' : ''}`}
              onClick={() => setTab('orders')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <ShoppingBag size={16} /> My Orders
            </button>
            <button
              className={`nav-tab-btn ${tab === 'reservations' ? 'active' : ''}`}
              onClick={() => setTab('reservations')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Calendar size={16} /> My Reservations
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={fetchData}
              disabled={loading}
              title="Refresh"
              style={{ color: 'var(--text-muted)' }}
            >
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
            </button>
            <button onClick={onClose} style={{ color: 'var(--text-muted)' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {error && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', background: '#fee2e2', color: '#b91c1c', padding: '8px 12px', borderRadius: '8px', fontSize: '0.85rem', marginBottom: '1rem' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              Loading your {tab}...
            </div>
          ) : tab === 'orders' ? (
            orders.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                <ShoppingBag size={36} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                <p>No orders placed yet. Ask our AI Assistant to place your first order!</p>
              </div>
            ) : (
              orders.map((o) => (
                <div
                  key={o.id}
                  style={{
                    border: '1px solid var(--surface-border)',
                    borderRadius: '10px',
                    padding: '12px 14px',
                    background: 'white',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--secondary)' }}>
                        Order #{o.id}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        • {o.branch_name || `Branch #${o.branch_id}`}
                      </span>
                      <span style={{ fontSize: '0.75rem', background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px' }}>
                        {o.order_type.toUpperCase()}
                      </span>
                    </div>
                    {getStatusBadge(o.status)}
                  </div>

                  <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', margin: '6px 0' }}>
                    {o.items && o.items.map((item, idx) => (
                      <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
                        <span>
                          {item.quantity}x Item #{item.menu_item_id}
                          {item.item_notes ? ` (${item.item_notes})` : ''}
                        </span>
                        <span style={{ fontWeight: 500 }}>
                          ${(Number(item.unit_price) * item.quantity).toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginTop: '6px',
                      paddingTop: '6px',
                      borderTop: '1px solid #f1f5f9',
                      fontSize: '0.85rem',
                    }}
                  >
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                      {new Date(o.created_at).toLocaleString()}
                    </span>
                    <span style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '0.95rem' }}>
                      Total: ${Number(o.total_amount).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))
            )
          ) : (
            reservations.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                <Calendar size={36} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                <p>No reservations booked yet. Chat with AI to reserve a table!</p>
              </div>
            ) : (
              reservations.map((r) => (
                <div
                  key={r.id}
                  style={{
                    border: '1px solid var(--surface-border)',
                    borderRadius: '10px',
                    padding: '12px 14px',
                    background: 'white',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--secondary)' }}>
                        Reservation #{r.id}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        • {r.branch_name || `Branch #${r.branch_id}`}
                      </span>
                    </div>
                    {getStatusBadge(r.status)}
                  </div>

                  <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', margin: '6px 0' }}>
                    <div>
                      <strong>Party Size:</strong> {r.party_size} Guests
                    </div>
                    <div>
                      <strong>Area:</strong> {r.seating_area_preference || 'Standard'}
                    </div>
                    <div>
                      <strong>Table Assigned:</strong> {r.table_label || (r.table_id ? `Table #${r.table_id}` : 'Pending assignment')}
                    </div>
                    <div>
                      <strong>Duration:</strong> {r.duration_minutes} Mins
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginTop: '6px',
                      paddingTop: '6px',
                      borderTop: '1px solid #f1f5f9',
                      fontSize: '0.8rem',
                      color: 'var(--text-muted)',
                    }}
                  >
                    <span>
                      📅 {new Date(r.start_time).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
                    </span>
                    {r.status === 'confirmed' && (
                      <span style={{ color: '#15803d', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                        <CheckCircle2 size={13} /> Auto-Confirmed
                      </span>
                    )}
                  </div>
                </div>
              ))
            )
          )}
        </div>
      </div>
    </div>
  );
}

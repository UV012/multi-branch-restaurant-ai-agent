import React, { useState, useEffect } from 'react';
import { api } from '../../api';
import { MapPin, Plus, RefreshCw, Layers, Check, X, ShieldAlert } from 'lucide-react';

export default function BranchTableManager({ currentStaff, branches, onRefreshBranches }) {
  const [selectedBranchId, setSelectedBranchId] = useState(
    currentStaff.branch_id || (branches[0] ? branches[0].id : 1)
  );
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Add Table Modal State
  const [isAddTableOpen, setIsAddTableOpen] = useState(false);
  const [newTableLabel, setNewTableLabel] = useState('');
  const [newTableArea, setNewTableArea] = useState('indoor');
  const [newTableCap, setNewTableCap] = useState('4');
  const [newTableMinCap, setNewTableMinCap] = useState('2');

  const fetchTables = async () => {
    setLoading(true);
    setError('');
    try {
      const bId = currentStaff.branch_id || selectedBranchId;
      const data = await api.getStaffTables(bId);
      setTables(data);
    } catch (err) {
      setError(err.message || 'Failed to load branch tables.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTables();
  }, [selectedBranchId]);

  const handleToggleTable = async (table) => {
    try {
      await api.updateTable(table.id, {
        is_active: !table.is_active,
      });
      await fetchTables();
    } catch (err) {
      alert(`Failed to update table: ${err.message}`);
    }
  };

  const handleCreateTable = async (e) => {
    e.preventDefault();
    if (!newTableLabel.trim()) return;
    try {
      const bId = currentStaff.branch_id || selectedBranchId;
      await api.createTable({
        branch_id: bId,
        label: newTableLabel.trim(),
        seating_area: newTableArea,
        capacity: Number(newTableCap),
        min_capacity: Number(newTableMinCap) || 1,
        is_active: true,
      });
      setIsAddTableOpen(false);
      setNewTableLabel('');
      await fetchTables();
      if (onRefreshBranches) onRefreshBranches();
    } catch (err) {
      alert(`Failed to create table: ${err.message}`);
    }
  };

  const selectedBranch = branches.find((b) => b.id === selectedBranchId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Bar */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
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

          {selectedBranch && (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              📍 {selectedBranch.address} • ⏰ {selectedBranch.opening_hours}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => setIsAddTableOpen(true)} className="btn-primary btn-sm">
            <Plus size={14} /> Add Table
          </button>
          <button onClick={fetchTables} className="btn-outline btn-sm">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: '8px', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      {/* Tables Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
        {tables.map((t) => (
          <div
            key={t.id}
            style={{
              background: 'white',
              border: '1px solid var(--surface-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              opacity: t.is_active ? 1 : 0.6,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 800, fontSize: '1.15rem', color: 'var(--secondary)' }}>
                {t.label}
              </span>
              <button
                onClick={() => handleToggleTable(t)}
                className={`badge ${t.is_active ? 'badge-success' : 'badge-danger'}`}
                style={{ cursor: 'pointer' }}
                title="Click to toggle table availability"
              >
                {t.is_active ? 'Active' : 'Offline'}
              </button>
            </div>

            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <div>
                <strong>Seating Area:</strong>{' '}
                <span style={{ textTransform: 'capitalize' }}>{t.seating_area}</span>
              </div>
              <div>
                <strong>Capacity:</strong> {t.min_capacity} - {t.capacity} Persons
              </div>
            </div>

            <div style={{ marginTop: 'auto', paddingTop: '8px', borderTop: '1px solid #f1f5f9', fontSize: '0.75rem', color: 'var(--accent)', fontWeight: 600 }}>
              ✓ Guarded by PostgreSQL GIST Exclusion
            </div>
          </div>
        ))}
      </div>

      {/* Add Table Modal */}
      {isAddTableOpen && (
        <div className="modal-overlay" onClick={() => setIsAddTableOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Add Table to Branch</h3>
            <form onSubmit={handleCreateTable} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Table Label</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. T12 or Booth-4"
                  value={newTableLabel}
                  onChange={(e) => setNewTableLabel(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Seating Area</label>
                <select
                  value={newTableArea}
                  onChange={(e) => setNewTableArea(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                >
                  <option value="indoor">Indoor</option>
                  <option value="outdoor">Outdoor Patio</option>
                  <option value="rooftop">Rooftop Garden</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Max Capacity</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={newTableCap}
                    onChange={(e) => setNewTableCap(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Min Capacity</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={newTableMinCap}
                    onChange={(e) => setNewTableMinCap(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
                <button type="button" onClick={() => setIsAddTableOpen(false)} className="btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn-primary btn-sm">
                  Add Table
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

import React from 'react';
import { MapPin, Clock, Phone, Info, ShieldCheck } from 'lucide-react';

export default function BranchSelector({ branches, selectedBranchId, onSelectBranch, branchFaq }) {
  const selectedBranch = branches.find((b) => b.id === selectedBranchId) || branches[0];

  return (
    <div className="sidebar-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.75rem' }}>
        <MapPin size={18} style={{ color: 'var(--primary)' }} />
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--secondary)' }}>Select Branch</h3>
      </div>

      <div className="branch-select-box">
        <select
          value={selectedBranchId || (selectedBranch ? selectedBranch.id : '')}
          onChange={(e) => onSelectBranch(Number(e.target.value))}
        >
          {branches.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name} — {b.city || 'Downtown'}
            </option>
          ))}
        </select>
      </div>

      {selectedBranch && (
        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', color: 'var(--text-muted)' }}>
            <MapPin size={14} style={{ marginTop: '3px', flexShrink: 0 }} />
            <span>{selectedBranch.address || 'Address not specified'}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
            <Clock size={14} style={{ flexShrink: 0 }} />
            <span>{selectedBranch.opening_hours || '10:00 AM - 11:00 PM'}</span>
          </div>

          {selectedBranch.phone && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
              <Phone size={14} style={{ flexShrink: 0 }} />
              <span>{selectedBranch.phone}</span>
            </div>
          )}

          {branchFaq && branchFaq.dining_policy && (
            <div
              style={{
                marginTop: '0.5rem',
                padding: '8px 10px',
                background: 'var(--primary-light)',
                borderRadius: '8px',
                border: '1px solid #fed7aa',
                fontSize: '0.8rem',
                color: '#9a3412',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '6px',
              }}
            >
              <Info size={14} style={{ marginTop: '2px', flexShrink: 0 }} />
              <div>
                <strong>Branch Policy:</strong> {branchFaq.dining_policy}
              </div>
            </div>
          )}

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: 'var(--accent)',
              fontSize: '0.75rem',
              fontWeight: 600,
              marginTop: '4px',
            }}
          >
            <ShieldCheck size={14} />
            <span>Auto-Confirm Reservations Active</span>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { Utensils, MessageSquarePlus, AlertTriangle } from 'lucide-react';

export default function MenuExplorer({ menuData, onAskAiToOrder }) {
  const [activeCategory, setActiveCategory] = useState('ALL');

  if (!menuData || !menuData.categories) {
    return (
      <div className="sidebar-card" style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
        <Utensils size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
        <p>Loading restaurant menu...</p>
      </div>
    );
  }

  const categories = menuData.categories || [];
  const allItems = categories.flatMap((cat) =>
    (cat.items || []).map((item) => ({ ...item, category_name: cat.name }))
  );

  const displayedItems =
    activeCategory === 'ALL'
      ? allItems
      : (categories.find((c) => c.name === activeCategory)?.items || []).map((item) => ({
          ...item,
          category_name: activeCategory,
        }));

  return (
    <div className="sidebar-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Utensils size={18} style={{ color: 'var(--primary)' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--secondary)' }}>Live Menu & Stock</h3>
        </div>
        <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
          {allItems.length} Items
        </span>
      </div>

      {/* Category Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '6px',
          overflowX: 'auto',
          paddingBottom: '6px',
          marginBottom: '0.75rem',
          scrollbarWidth: 'none',
        }}
      >
        <button
          className={`chip-btn ${activeCategory === 'ALL' ? 'active' : ''}`}
          style={{
            background: activeCategory === 'ALL' ? 'var(--primary)' : '#f1f5f9',
            color: activeCategory === 'ALL' ? 'white' : 'var(--text-main)',
            fontWeight: 600,
          }}
          onClick={() => setActiveCategory('ALL')}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            key={c.id}
            className={`chip-btn ${activeCategory === c.name ? 'active' : ''}`}
            style={{
              background: activeCategory === c.name ? 'var(--primary)' : '#f1f5f9',
              color: activeCategory === c.name ? 'white' : 'var(--text-main)',
              fontWeight: 600,
            }}
            onClick={() => setActiveCategory(c.name)}
          >
            {c.name}
          </button>
        ))}
      </div>

      {/* Items Scrollable List */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '2px' }}>
        {displayedItems.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', margin: '1rem 0' }}>
            No items in this category.
          </p>
        ) : (
          displayedItems.map((item) => {
            const isAvailable = item.is_available && item.stock_quantity > 0;
            return (
              <div
                key={item.id}
                style={{
                  border: '1px solid var(--surface-border)',
                  borderRadius: '8px',
                  padding: '10px 12px',
                  background: isAvailable ? 'white' : '#f8fafc',
                  opacity: isAvailable ? 1 : 0.65,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--secondary)' }}>
                    {item.name}
                  </span>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--primary)' }}>
                    ${Number(item.base_price).toFixed(2)}
                  </span>
                </div>

                {item.description && (
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.3 }}>
                    {item.description}
                  </p>
                )}

                {item.variants && item.variants.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '2px' }}>
                    {item.variants.map((v) => (
                      <span
                        key={v.id}
                        style={{
                          fontSize: '0.7rem',
                          background: '#f1f5f9',
                          padding: '1px 6px',
                          borderRadius: '4px',
                          color: '#475569',
                        }}
                      >
                        {v.variant_name} {v.price_delta > 0 ? `(+$${v.price_delta})` : ''}
                      </span>
                    ))}
                  </div>
                )}

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '4px',
                    paddingTop: '4px',
                    borderTop: '1px dashed #f1f5f9',
                  }}
                >
                  {isAvailable ? (
                    <span style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: 600 }}>
                      ✓ In Stock ({item.stock_quantity})
                    </span>
                  ) : (
                    <span
                      style={{
                        fontSize: '0.75rem',
                        color: '#b91c1c',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <AlertTriangle size={12} /> Sold Out
                    </span>
                  )}

                  {isAvailable && (
                    <button
                      className="btn-sm"
                      style={{
                        background: 'var(--primary-light)',
                        color: 'var(--primary)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontWeight: 600,
                      }}
                      onClick={() => onAskAiToOrder(`I want to order 1 ${item.name}`)}
                    >
                      <MessageSquarePlus size={12} /> Ask AI to Order
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

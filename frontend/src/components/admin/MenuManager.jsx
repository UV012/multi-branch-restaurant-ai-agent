import React, { useState, useEffect } from 'react';
import { api } from '../../api';
import { Utensils, Plus, RefreshCw, AlertTriangle, Check, Edit2, Package, X } from 'lucide-react';

export default function MenuManager({ currentStaff, branches }) {
  const [selectedBranchId, setSelectedBranchId] = useState(
    currentStaff.branch_id || (branches[0] ? branches[0].id : 1)
  );
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stockEdits, setStockEdits] = useState({}); // { [itemId]: number }
  const [savingStockId, setSavingStockId] = useState(null);

  // New Item Modal State
  const [isAddItemOpen, setIsAddItemOpen] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [newItemDesc, setNewItemDesc] = useState('');
  const [newItemPrice, setNewItemPrice] = useState('');
  const [newItemCatId, setNewItemCatId] = useState('');
  const [newItemStock, setNewItemStock] = useState('50');
  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [newCatName, setNewCatName] = useState('');

  const fetchMenuData = async () => {
    setLoading(true);
    setError('');
    try {
      const bId = currentStaff.branch_id || selectedBranchId;
      const res = await api.getBranchMenu(bId);
      setCategories(res.categories || []);

      // Initialize stockEdits state
      const initialStock = {};
      (res.categories || []).forEach((c) => {
        (c.items || []).forEach((item) => {
          initialStock[item.id] = item.stock_quantity;
        });
      });
      setStockEdits(initialStock);
    } catch (err) {
      setError(err.message || 'Failed to load menu and stock.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMenuData();
  }, [selectedBranchId]);

  const handleStockInputChange = (itemId, val) => {
    setStockEdits((prev) => ({
      ...prev,
      [itemId]: Number(val),
    }));
  };

  const handleQuickAddStock = async (item, delta) => {
    const current = stockEdits[item.id] !== undefined ? stockEdits[item.id] : item.stock_quantity;
    const updated = Math.max(0, current + delta);
    await handleSaveStock(item.id, updated);
  };

  const handleSaveStock = async (itemId, targetStock = null) => {
    setSavingStockId(itemId);
    try {
      const bId = currentStaff.branch_id || selectedBranchId;
      const qty = targetStock !== null ? targetStock : stockEdits[itemId];
      await api.updateItemStock(itemId, bId, qty);
      await fetchMenuData();
    } catch (err) {
      alert(`Failed to update stock: ${err.message}`);
    } finally {
      setSavingStockId(null);
    }
  };

  const handleToggleAvailable = async (item) => {
    try {
      await api.updateMenuItem(item.id, {
        is_available: !item.is_available,
      });
      await fetchMenuData();
    } catch (err) {
      alert(`Failed to update availability: ${err.message}`);
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    if (!newCatName.trim()) return;
    try {
      const bId = currentStaff.branch_id || selectedBranchId;
      await api.createCategory({
        branch_id: bId,
        name: newCatName.trim(),
      });
      setNewCatName('');
      setIsAddingCategory(false);
      await fetchMenuData();
    } catch (err) {
      alert(`Failed to create category: ${err.message}`);
    }
  };

  const handleCreateItem = async (e) => {
    e.preventDefault();
    if (!newItemName.trim() || !newItemCatId || !newItemPrice) return;
    try {
      await api.createMenuItem({
        category_id: Number(newItemCatId),
        name: newItemName.trim(),
        description: newItemDesc.trim() || undefined,
        base_price: Number(newItemPrice),
        initial_stock: Number(newItemStock) || 50,
      });
      setIsAddItemOpen(false);
      setNewItemName('');
      setNewItemDesc('');
      setNewItemPrice('');
      await fetchMenuData();
    } catch (err) {
      alert(`Failed to create item: ${err.message}`);
    }
  };

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
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Inventory adjusts automatically on each AI order placement.
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setIsAddingCategory(true)}
            className="btn-secondary btn-sm"
          >
            <Plus size={14} /> New Category
          </button>
          <button
            onClick={() => {
              if (categories.length > 0) setNewItemCatId(categories[0].id);
              setIsAddItemOpen(true);
            }}
            className="btn-primary btn-sm"
          >
            <Plus size={14} /> New Menu Item
          </button>
          <button onClick={fetchMenuData} className="btn-outline btn-sm">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '10px 14px', borderRadius: '8px', fontSize: '0.875rem' }}>
          {error}
        </div>
      )}

      {/* Menu Categories and Items Table */}
      {categories.map((cat) => (
        <div
          key={cat.id}
          style={{
            background: 'white',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--surface-border)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '10px 16px',
              background: '#f8fafc',
              borderBottom: '1px solid var(--surface-border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--secondary)' }}>
              {cat.name}
            </h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {cat.items?.length || 0} Items
            </span>
          </div>

          <table className="data-table" style={{ border: 'none', borderRadius: 0 }}>
            <thead>
              <tr>
                <th>Item Name & Description</th>
                <th>Price</th>
                <th>Status</th>
                <th>Branch Stock</th>
                <th>Restock Action</th>
              </tr>
            </thead>
            <tbody>
              {(cat.items || []).map((item) => {
                const effectiveStock =
                  stockEdits[item.id] !== undefined ? stockEdits[item.id] : item.stock_quantity;
                const isSaving = savingStockId === item.id;
                const isOutOfStock = effectiveStock <= 0;

                return (
                  <tr key={item.id} style={{ background: isOutOfStock ? '#fffbeb' : 'white' }}>
                    <td style={{ maxWidth: '300px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--secondary)' }}>{item.name}</div>
                      {item.description && (
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          {item.description}
                        </div>
                      )}
                      {item.variants && item.variants.length > 0 && (
                        <div style={{ display: 'flex', gap: '4px', marginTop: '4px' }}>
                          {item.variants.map((v) => (
                            <span
                              key={v.id}
                              style={{
                                fontSize: '0.7rem',
                                background: '#f1f5f9',
                                padding: '1px 5px',
                                borderRadius: '3px',
                              }}
                            >
                              {v.variant_name} (+${v.price_delta})
                            </span>
                          ))}
                        </div>
                      )}
                    </td>

                    <td style={{ fontWeight: 600 }}>${Number(item.base_price).toFixed(2)}</td>

                    <td>
                      <button
                        onClick={() => handleToggleAvailable(item)}
                        className={`badge ${item.is_available ? 'badge-success' : 'badge-danger'}`}
                        style={{ cursor: 'pointer' }}
                        title="Click to toggle availability"
                      >
                        {item.is_available ? 'Active' : 'Disabled'}
                      </button>
                    </td>

                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="number"
                          min="0"
                          value={effectiveStock}
                          onChange={(e) => handleStockInputChange(item.id, e.target.value)}
                          style={{
                            width: '70px',
                            padding: '4px 6px',
                            borderRadius: '4px',
                            border: '1px solid var(--surface-border)',
                            fontWeight: 700,
                            textAlign: 'center',
                            color: isOutOfStock ? '#b91c1c' : 'inherit',
                          }}
                        />
                        <button
                          onClick={() => handleSaveStock(item.id)}
                          disabled={isSaving}
                          className="btn-primary btn-sm"
                          style={{ padding: '4px 8px' }}
                        >
                          {isSaving ? '...' : <Check size={13} />}
                        </button>
                      </div>
                      {isOutOfStock && (
                        <div style={{ fontSize: '0.7rem', color: '#b91c1c', fontWeight: 600, marginTop: '2px' }}>
                          Auto-marked Sold Out
                        </div>
                      )}
                    </td>

                    <td>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button
                          onClick={() => handleQuickAddStock(item, 10)}
                          className="btn-outline btn-sm"
                          style={{ fontSize: '0.75rem' }}
                        >
                          +10
                        </button>
                        <button
                          onClick={() => handleQuickAddStock(item, 50)}
                          className="btn-outline btn-sm"
                          style={{ fontSize: '0.75rem' }}
                        >
                          +50
                        </button>
                        <button
                          onClick={() => handleSaveStock(item.id, 0)}
                          className="btn-outline btn-sm"
                          style={{ fontSize: '0.75rem', color: '#ef4444' }}
                          title="Zero Out Stock"
                        >
                          Zero
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ))}

      {/* Add Category Modal */}
      {isAddingCategory && (
        <div className="modal-overlay" onClick={() => setIsAddingCategory(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Create Menu Category</h3>
            <form onSubmit={handleCreateCategory}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Category Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Seafood, Chef's Specials"
                  value={newCatName}
                  onChange={(e) => setNewCatName(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" onClick={() => setIsAddingCategory(false)} className="btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn-primary btn-sm">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Item Modal */}
      {isAddItemOpen && (
        <div className="modal-overlay" onClick={() => setIsAddItemOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Add New Menu Item</h3>
            <form onSubmit={handleCreateItem} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Category</label>
                <select
                  value={newItemCatId}
                  onChange={(e) => setNewItemCatId(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Item Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Truffle Mushroom Risotto"
                  value={newItemName}
                  onChange={(e) => setNewItemName(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Description</label>
                <textarea
                  placeholder="Short description of ingredients..."
                  value={newItemDesc}
                  onChange={(e) => setNewItemDesc(e.target.value)}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)', resize: 'vertical' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Base Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="18.50"
                    value={newItemPrice}
                    onChange={(e) => setNewItemPrice(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', fontWeight: 600 }}>Initial Stock</label>
                  <input
                    type="number"
                    min="0"
                    placeholder="50"
                    value={newItemStock}
                    onChange={(e) => setNewItemStock(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--surface-border)' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
                <button type="button" onClick={() => setIsAddItemOpen(false)} className="btn-secondary btn-sm">
                  Cancel
                </button>
                <button type="submit" className="btn-primary btn-sm">
                  Add Item
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

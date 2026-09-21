import React, { useState, useEffect } from 'react';
import {
  api,
  getStoredCustomer,
  getStoredStaff,
  removeCustomerToken,
  removeStaffToken,
} from './api';
import Navbar from './components/Navbar';
import BranchSelector from './components/customer/BranchSelector';
import MenuExplorer from './components/customer/MenuExplorer';
import ChatWidget from './components/customer/ChatWidget';
import CustomerAuthModal from './components/customer/CustomerAuthModal';
import MyHistoryModal from './components/customer/MyHistoryModal';
import AdminLoginModal from './components/admin/AdminLoginModal';
import AdminLayout from './components/admin/AdminLayout';
import { Shield, Sparkles, AlertCircle } from 'lucide-react';

export default function App() {
  const [currentView, setCurrentView] = useState('customer'); // 'customer' | 'admin'
  const [branches, setBranches] = useState([]);
  const [selectedBranchId, setSelectedBranchId] = useState(null);
  const [menuData, setMenuData] = useState(null);
  const [branchFaq, setBranchFaq] = useState(null);

  // Auth States
  const [currentCustomer, setCurrentCustomer] = useState(getStoredCustomer());
  const [currentStaff, setCurrentStaff] = useState(getStoredStaff());

  // Modal States
  const [isCustomerAuthOpen, setIsCustomerAuthOpen] = useState(false);
  const [isStaffAuthOpen, setIsStaffAuthOpen] = useState(false);
  const [isMyHistoryOpen, setIsMyHistoryOpen] = useState(false);

  // Chat prefill trigger
  const [prefilledPrompt, setPrefilledPrompt] = useState(null);

  // Initial Data Fetch
  const loadBranches = async () => {
    try {
      const data = await api.getBranches();
      setBranches(data);
      if (data.length > 0 && !selectedBranchId) {
        setSelectedBranchId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load branches:', err);
    }
  };

  useEffect(() => {
    loadBranches();
  }, []);

  // Fetch branch menu & FAQ when selected branch changes
  useEffect(() => {
    if (selectedBranchId) {
      api.getBranchMenu(selectedBranchId)
        .then(setMenuData)
        .catch((err) => console.error('Error fetching menu:', err));

      api.getBranchFaq(selectedBranchId)
        .then(setBranchFaq)
        .catch((err) => console.error('Error fetching branch FAQ:', err));
    }
  }, [selectedBranchId]);

  // Handle Logout
  const handleCustomerLogout = () => {
    removeCustomerToken();
    setCurrentCustomer(null);
  };

  const handleStaffLogout = () => {
    removeStaffToken();
    setCurrentStaff(null);
    setCurrentView('customer');
  };

  const selectedBranch = branches.find((b) => b.id === selectedBranchId) || branches[0];

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <Navbar
        currentView={currentView}
        onSwitchView={(v) => {
          if (v === 'admin' && !currentStaff) {
            setIsStaffAuthOpen(true);
          } else {
            setCurrentView(v);
          }
        }}
        currentCustomer={currentCustomer}
        currentStaff={currentStaff}
        onOpenCustomerAuth={() => setIsCustomerAuthOpen(true)}
        onOpenStaffAuth={() => setIsStaffAuthOpen(true)}
        onOpenMyHistory={() => setIsMyHistoryOpen(true)}
        onCustomerLogout={handleCustomerLogout}
        onStaffLogout={handleStaffLogout}
      />

      {/* Main Viewport */}
      {currentView === 'customer' ? (
        <main className="chat-page">
          {/* Left Sidebar: Branch Info & Live Menu with Stock */}
          <aside className="chat-sidebar">
            <BranchSelector
              branches={branches}
              selectedBranchId={selectedBranchId}
              onSelectBranch={setSelectedBranchId}
              branchFaq={branchFaq}
            />

            <MenuExplorer
              menuData={menuData}
              onAskAiToOrder={(prompt) => {
                if (!currentCustomer) {
                  setIsCustomerAuthOpen(true);
                } else {
                  setPrefilledPrompt(prompt);
                }
              }}
            />
          </aside>

          {/* Right Area: Interactive Conversational AI Agent */}
          <section style={{ flex: 1, display: 'flex', minHeight: 0, minWidth: 0 }}>
            <ChatWidget
              currentCustomer={currentCustomer}
              selectedBranch={selectedBranch}
              onRequireAuth={() => setIsCustomerAuthOpen(true)}
              prefilledPrompt={prefilledPrompt}
              onClearPrefill={() => setPrefilledPrompt(null)}
            />
          </section>
        </main>
      ) : (
        <main style={{ flex: 1, background: '#f8fafc' }}>
          {currentStaff ? (
            <AdminLayout
              currentStaff={currentStaff}
              branches={branches}
              onLogout={handleStaffLogout}
              onRefreshBranches={loadBranches}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '6rem 2rem' }}>
              <Shield size={48} style={{ color: 'var(--primary)', margin: '0 auto 1rem' }} />
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.5rem' }}>
                Restricted Staff Portal
              </h2>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                Please sign in with your staff or administrator credentials to manage restaurant operations.
              </p>
              <button onClick={() => setIsStaffAuthOpen(true)} className="btn-primary">
                Staff Sign In
              </button>
            </div>
          )}
        </main>
      )}

      {/* Modals */}
      <CustomerAuthModal
        isOpen={isCustomerAuthOpen}
        onClose={() => setIsCustomerAuthOpen(false)}
        onAuthSuccess={(cust) => setCurrentCustomer(cust)}
      />

      <MyHistoryModal
        isOpen={isMyHistoryOpen}
        onClose={() => setIsMyHistoryOpen(false)}
      />

      <AdminLoginModal
        isOpen={isStaffAuthOpen}
        onClose={() => setIsStaffAuthOpen(false)}
        onLoginSuccess={(staff) => {
          setCurrentStaff(staff);
          setCurrentView('admin');
        }}
      />
    </div>
  );
}

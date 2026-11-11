import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from '../components/common/Sidebar';
import Navbar from '../components/common/Navbar';
import ConfirmModal from '../components/common/ConfirmModal';
import StartResearchModal from '../components/research/StartResearchModal';
import { useAuth } from '../context/AuthContext';

export default function AppLayout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [logoutModalOpen, setLogoutModalOpen] = useState(false);
  const [researchModalOpen, setResearchModalOpen] = useState(false);
  const [modalInitialStock, setModalInitialStock] = useState(null);

  const handleConfirmLogout = async () => {
    await logout();
    setLogoutModalOpen(false);
    navigate('/login');
  };

  const openResearchModal = (stockData = null) => {
    setModalInitialStock(stockData);
    setResearchModalOpen(true);
  };

  const handleTaskCreated = (newTask) => {
    // Navigate to history so user immediately sees the running task
    navigate('/history');
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      {/* Sidebar */}
      <Sidebar
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
        onOpenLogoutModal={() => setLogoutModalOpen(true)}
      />

      {/* Main Content Area */}
      <div className="lg:pl-64 flex flex-col min-h-screen">
        {/* Top Navbar */}
        <Navbar
          setMobileOpen={setMobileOpen}
          onOpenNewResearchModal={() => openResearchModal(null)}
        />

        {/* Dynamic Page Content */}
        <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto animate-fade-in">
          <Outlet context={{ openResearchModal }} />
        </main>
      </div>

      {/* Start Research Modal */}
      <StartResearchModal
        isOpen={researchModalOpen}
        onClose={() => setResearchModalOpen(false)}
        initialData={modalInitialStock}
        onTaskCreated={handleTaskCreated}
      />

      {/* Sign Out Confirmation Modal */}
      <ConfirmModal
        isOpen={logoutModalOpen}
        title="Sign Out of QuantAgent"
        message="Are you sure you want to end your current session? You will need to enter your credentials to access your dashboard again."
        confirmText="Sign Out"
        cancelText="Stay Signed In"
        onConfirm={handleConfirmLogout}
        onCancel={() => setLogoutModalOpen(false)}
        isDangerous={false}
      />
    </div>
  );
}


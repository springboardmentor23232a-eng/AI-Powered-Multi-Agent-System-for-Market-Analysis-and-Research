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

  const handleTaskCreated = () => {
    navigate('/history');
  };

  return (
    <div className="min-h-screen terminal-grid-bg text-slate-800 font-sans">
      <Sidebar
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
        onOpenLogoutModal={() => setLogoutModalOpen(true)}
      />

      <div className="lg:pl-72 flex flex-col min-h-screen">
        <Navbar
          setMobileOpen={setMobileOpen}
          onOpenNewResearchModal={() => openResearchModal(null)}
        />

        <main className="flex-1 p-4 sm:p-7 max-w-[1440px] w-full mx-auto">
          <Outlet context={{ openResearchModal }} />
        </main>
      </div>

      <StartResearchModal
        isOpen={researchModalOpen}
        onClose={() => setResearchModalOpen(false)}
        initialData={modalInitialStock}
        onTaskCreated={handleTaskCreated}
      />

      <ConfirmModal
        isOpen={logoutModalOpen}
        title="Sign Out of QuantAgent Studio"
        message="Are you sure you want to end your current session? Your research dossiers and watchlists remain saved in PostgreSQL."
        confirmText="Sign Out"
        cancelText="Stay Signed In"
        onConfirm={handleConfirmLogout}
        onCancel={() => setLogoutModalOpen(false)}
        isDangerous={false}
      />
    </div>
  );
}

import React, { useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { SearchModal } from '../SearchModal';
import { DetailDrawer } from '../DetailDrawer';
import { ToastContainer, ToastMessage } from '../ui/Toast';
import { Transaction } from '../../api/client';

interface LayoutProps {
  children: React.ReactNode;
  currentPage: string;
  onNavigate: (page: string) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  selectedTransaction: Transaction | null;
  onSelectTransaction: (t: Transaction | null) => void;
  toasts: ToastMessage[];
  onDismissToast: (id: string) => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  currentPage,
  onNavigate,
  onRefresh,
  isRefreshing,
  selectedTransaction,
  onSelectTransaction,
  toasts,
  onDismissToast,
}) => {
  const [searchOpen, setSearchOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] flex flex-col font-sans">
      <Header onOpenSearch={() => setSearchOpen(true)} onRefresh={onRefresh} isRefreshing={isRefreshing} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar currentPage={currentPage} onNavigate={onNavigate} />

        <main className="flex-1 overflow-y-auto p-6 bg-[#F8FAFC]">
          {children}
        </main>
      </div>

      <SearchModal
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        onSelectTransaction={(t) => onSelectTransaction(t)}
      />

      <DetailDrawer
        transaction={selectedTransaction}
        onClose={() => onSelectTransaction(null)}
        onRefresh={onRefresh}
      />

      <ToastContainer toasts={toasts} onDismiss={onDismissToast} />
    </div>
  );
};
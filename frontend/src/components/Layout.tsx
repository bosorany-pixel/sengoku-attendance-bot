import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { motion } from 'framer-motion';

interface LayoutProps {
  children: ReactNode;
  title: string;
  subtitle: string;
  showSidebar?: boolean;
}

export function Layout({ children, title, subtitle, showSidebar = true }: LayoutProps) {
  return (
    <div className="min-h-screen bg-dark-bg p-5">
      <div className="container mx-auto max-w-7xl">
        <div className="flex flex-col lg:flex-row gap-5">
          {showSidebar && <Sidebar />}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="flex-1 text-center"
          >
            <h1 className="font-display text-4xl font-semibold text-white mb-2 tracking-tight">{title}</h1>
            <p className="font-display text-dark-textLight mb-6 text-sm tracking-wide">{subtitle}</p>
            {children}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

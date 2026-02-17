import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { SparkBackground } from './SparkBackground';
import { motion } from 'framer-motion';

interface LayoutProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  showSidebar?: boolean;
}

export function Layout({ children, title, subtitle, showSidebar = true }: LayoutProps) {
  const showHeader = title != null && title !== '';
  return (
    <div
      className="min-h-screen p-5 relative"
      style={{
        background: 'linear-gradient(to top, #7f1d1d 0%, #1e1e1e 50%, #1e1e1e 100%)',
        backgroundAttachment: 'fixed',
      }}
    >
      <SparkBackground />
      <div className="container mx-auto max-w-7xl relative z-10">
        <div className="flex flex-col lg:flex-row gap-5">
          {showSidebar && <Sidebar />}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className={`flex-1 ${showHeader ? 'text-center' : ''}`}
          >
            {showHeader && (
              <>
                <h1 className="font-display text-4xl font-semibold text-white mb-2 tracking-tight">{title}</h1>
                <p className="font-display text-dark-textLight mb-6 text-sm tracking-wide">{subtitle ?? ''}</p>
              </>
            )}
            {children}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

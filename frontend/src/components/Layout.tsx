import type { ReactNode } from 'react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { SparkBackground } from './SparkBackground';
import { motion, AnimatePresence } from 'framer-motion';

interface LayoutProps {
  children: ReactNode;
  title?: string;
  titleHref?: string;
  subtitle?: string;
  showSidebar?: boolean;
}

export function Layout({ children, title, titleHref, subtitle, showSidebar = true }: LayoutProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const showHeader = title != null && title !== '';
  const showBurger = !showSidebar;

  return (
    <div
      className="min-h-screen p-5 relative"
      style={{
        background: 'linear-gradient(to top, #7f1d1d 0%, #1e1e1e 50%, #1e1e1e 100%)',
        backgroundAttachment: 'fixed',
      }}
    >
      <SparkBackground />
      {showBurger && (
        <button
          type="button"
          onClick={() => setMenuOpen(true)}
          className="fixed top-5 left-5 z-20 flex flex-col gap-1.5 p-2 rounded-lg bg-dark-card/90 border border-dark-border text-white hover:bg-dark-card focus:outline-none focus:ring-2 focus:ring-accent-blue/50"
          aria-label="Открыть меню История"
        >
          <span className="block w-5 h-0.5 bg-current rounded" />
          <span className="block w-5 h-0.5 bg-current rounded" />
          <span className="block w-5 h-0.5 bg-current rounded" />
        </button>
      )}
      <AnimatePresence>
        {menuOpen && showBurger && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/60 z-30"
              onClick={() => setMenuOpen(false)}
              aria-hidden
            />
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'tween', duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="fixed top-0 left-0 bottom-0 w-64 max-w-[85vw] z-40 overflow-y-auto p-4 pt-14 bg-dark-card border-r border-dark-border shadow-xl"
            >
              <button
                type="button"
                onClick={() => setMenuOpen(false)}
                className="absolute top-3 right-3 p-1.5 rounded text-dark-textLight hover:text-white hover:bg-white/10"
                aria-label="Закрыть"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <Sidebar />
            </motion.div>
          </>
        )}
      </AnimatePresence>
      <div className="container mx-auto max-w-7xl relative z-10">
        <div className="flex flex-col lg:flex-row gap-5">
          {showSidebar && <Sidebar />}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className={`flex-1 ${showHeader ? 'text-center' : ''} ${showBurger ? 'pl-12' : ''}`}
          >
            {showHeader && (
              <>
                <h1 className="font-display text-4xl font-semibold text-white mb-2 tracking-tight">
                  {titleHref ? (
                    <Link to={titleHref} className="text-white hover:text-white/90 focus:outline-none focus:underline">
                      {title}
                    </Link>
                  ) : (
                    title
                  )}
                </h1>
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

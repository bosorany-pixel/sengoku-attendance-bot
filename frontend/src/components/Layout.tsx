import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { motion } from 'framer-motion';

interface LayoutProps {
  children: ReactNode;
  title: string;
  subtitle: string;
}

export function Layout({ children, title, subtitle }: LayoutProps) {
  return (
    <div className="min-h-screen bg-dark-bg p-5">
      <div className="container mx-auto max-w-7xl">
        <div className="flex flex-col lg:flex-row gap-5">
          <Sidebar />
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="flex-1 text-center"
          >
            <h1 className="text-4xl font-bold text-white mb-2">{title}</h1>
            <p className="text-dark-textLight mb-5">{subtitle}</p>
            {children}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

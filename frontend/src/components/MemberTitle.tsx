import { motion } from 'framer-motion';

interface MemberTitleProps {
  title: string;
  subtitle: string;
}

export function MemberTitle({ title, subtitle }: MemberTitleProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="text-left"
    >
      <h1 className="font-display text-4xl font-semibold text-white mb-2 tracking-tight">{title}</h1>
      <p className="font-display text-dark-textLight text-sm tracking-wide">{subtitle}</p>
    </motion.div>
  );
}

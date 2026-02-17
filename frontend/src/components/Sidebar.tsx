import { Link, useSearchParams } from 'react-router-dom';
import { useArchives } from '../hooks/useArchives';
import { motion } from 'framer-motion';

export function Sidebar() {
  const [searchParams] = useSearchParams();
  const currentDb = searchParams.get('db');
  const { data: archives, isLoading } = useArchives();

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="w-48 flex-shrink-0 bg-dark-card border border-dark-border rounded p-4"
    >
      <h3 className="text-white text-center mb-3 font-semibold">История</h3>
      <ul className="space-y-1">
        <li>
          <Link
            to="/"
            className={`block py-1 text-sm ${
              !currentDb
                ? 'text-accent-green font-bold'
                : 'text-accent-blue'
            }`}
          >
            Текущий
          </Link>
        </li>
        {isLoading ? (
          <li className="text-dark-textLight text-sm">Loading...</li>
        ) : (
          archives?.map((archive) => (
            <li key={archive.file}>
              <Link
                to={`/?db=${archive.file}`}
                className={`block py-1 text-sm ${
                  currentDb === archive.file
                    ? 'text-accent-green font-bold'
                    : 'text-accent-blue'
                }`}
              >
                {archive.name}
              </Link>
            </li>
          ))
        )}
      </ul>
    </motion.div>
  );
}

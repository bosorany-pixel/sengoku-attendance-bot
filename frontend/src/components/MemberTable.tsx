import { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import type { Member } from '../lib/types';
import { motion } from 'framer-motion';

interface MemberTableProps {
  members: Member[];
}

function formatMoney(value: number): string {
  if (value === null || value === undefined) return '—';
  return value.toLocaleString('ru-RU').replace(/,/g, ' ');
}

export function MemberTable({ members }: MemberTableProps) {
  const [searchParams] = useSearchParams();
  const [filter, setFilter] = useState('');
  const currentDb = searchParams.get('db');

  const filteredMembers = useMemo(() => {
    if (!filter) return members;
    const lowerFilter = filter.toLowerCase();
    return members.filter((m) =>
      m.display_name?.toLowerCase().includes(lowerFilter)
    );
  }, [members, filter]);

  const dbQuery = currentDb ? `?db=${currentDb}` : '';

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="max-w-4xl mx-auto"
    >
      <motion.div
        className="flex gap-2 mb-5"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.3 }}
      >
        <input
          id="nickFilter"
          type="text"
          placeholder="Поиск по нику…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="flex-1 font-display text-dark-text bg-dark-card/80 border border-dark-border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-accent-blue/40 focus:border-accent-blue/50 transition-all duration-200 placeholder:text-dark-textLight/70"
        />
        <motion.button
          type="button"
          onClick={() => setFilter('')}
          className="font-display px-4 py-3 rounded-xl bg-dark-card/80 border border-dark-border text-dark-textLight hover:bg-white/10 hover:text-white hover:border-dark-border transition-all duration-200 cursor-pointer"
          title="Сбросить"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          ×
        </motion.button>
      </motion.div>

      <motion.div
        className="overflow-hidden rounded-2xl border border-dark-border bg-dark-card/60 shadow-xl"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.35 }}
      >
        <div className="overflow-x-auto">
          <table className="w-full font-display">
            <thead>
              <tr className="bg-white/[0.06] text-left">
                <th className="px-4 py-3.5 text-xs font-semibold uppercase tracking-wider text-dark-textLight first:rounded-tl-2xl">
                  Ник
                </th>
                <th className="px-4 py-3.5 text-xs font-semibold uppercase tracking-wider text-dark-textLight">
                  нажми на меня
                </th>
                <th className="px-4 py-3.5 text-xs font-semibold uppercase tracking-wider text-dark-textLight">
                  Посещений
                </th>
                <th className="px-4 py-3.5 text-xs font-semibold uppercase tracking-wider text-dark-textLight last:rounded-tr-2xl">
                  Серебра
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredMembers.map((member, index) => (
                <motion.tr
                  key={member.uid}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.05 + index * 0.02, duration: 0.25 }}
                  className="border-b border-dark-border/60 last:border-b-0 transition-colors duration-200 hover:bg-white/[0.04]"
                >
                  <td className="px-4 py-3">
                    <Link
                      to={`/bp/${member.uid}`}
                      className="text-accent-blue hover:underline transition-colors duration-200 font-medium"
                    >
                      {member.display_name || '—'}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-dark-textLight text-sm">
                    <Link
                      to={`/user/${member.uid}${dbQuery}`}
                      className="text-accent-blue hover:underline transition-colors duration-200"
                    >
                      {member.uid}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-dark-text tabular-nums">
                    {member.event_count}
                  </td>
                  <td className="px-4 py-3 tabular-nums">
                    <Link
                      to={`/payment/${member.uid}${dbQuery}`}
                      className="text-accent-blue hover:underline transition-colors duration-200"
                    >
                      {formatMoney(member.total_amount)}
                    </Link>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </motion.div>
  );
}

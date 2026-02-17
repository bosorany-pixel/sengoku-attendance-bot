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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex gap-2 mb-4 max-w-4xl mx-auto">
        <input
          id="nickFilter"
          type="text"
          placeholder="Поиск по нику…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="flex-1 input-search"
        />
        <button
          onClick={() => setFilter('')}
          className="btn-primary"
          title="Сбросить"
        >
          ×
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full max-w-4xl mx-auto bg-dark-card border border-dark-border">
          <thead>
            <tr className="bg-[#333] text-left">
              <th className="border border-[#555] p-2.5">Ник</th>
              <th className="border border-[#555] p-2.5">нажми на меня</th>
              <th className="border border-[#555] p-2.5">
                Количество посещенного контента
              </th>
              <th className="border border-[#555] p-2.5">
                Серебра (на счету гильдии)
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredMembers.map((member, index) => (
              <motion.tr
                key={member.uid}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.02 }}
                className="table-row even:bg-[#242424]"
              >
                <td className="border border-[#555] p-2.5">
                  {member.display_name || '—'}
                </td>
                <td className="border border-[#555] p-2.5">
                  <Link
                    to={`/user/${member.uid}${dbQuery}`}
                    className="text-accent-blue hover:underline"
                  >
                    {member.uid}
                  </Link>
                </td>
                <td className="border border-[#555] p-2.5">
                  {member.event_count}
                </td>
                <td className="border border-[#555] p-2.5">
                  <Link
                    to={`/payment/${member.uid}${dbQuery}`}
                    className="text-accent-blue hover:underline"
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
  );
}

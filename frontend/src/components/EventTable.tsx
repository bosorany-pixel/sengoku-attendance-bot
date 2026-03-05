import type { Event } from '../lib/types';
import { motion } from 'framer-motion';

interface EventTableProps {
  events: Event[];
}

export function EventTable({ events }: EventTableProps) {
  const getDiscordLink = (event: Event) => {
    if (event.channel_id === '0') return null;
    return `https://discord.com/channels/${event.guild_id}/${event.channel_id}/${event.message_id}`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="overflow-x-auto"
    >
      <table className="w-full max-w-4xl mx-auto bg-dark-card border border-dark-border">
        <thead>
          <tr className="bg-[#333] text-left">
            <th className="border border-[#555] p-2.5">Канал</th>
            <th className="border border-[#555] p-2.5">Сообщение</th>
            <th className="border border-[#555] p-2.5">Дата</th>
            <th className="border border-[#555] p-2.5">Статус</th>
            <th className="border border-[#555] p-2.5">Очки</th>
            <th className="border border-[#555] p-2.5">Discord</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event, index) => {
            const link = getDiscordLink(event);
            return (
              <motion.tr
                key={event.message_id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.02 }}
                className="table-row even:bg-[#242424]"
              >
                <td className="border border-[#555] p-2.5">
                  {event.channel_name}
                </td>
                <td className="border border-[#555] p-2.5 max-w-xs truncate">
                  {event.message_text}
                </td>
                <td className="border border-[#555] p-2.5">
                  {event.read_time ? new Date(event.read_time).toLocaleDateString('ru-RU') : '—'}
                </td>
                <td className="border border-[#555] p-2.5 text-center">
                  {event.disband ? '✗' : '✓'}
                </td>
                <td className="border border-[#555] p-2.5 text-center">
                  {event.points || '—'}
                </td>
                <td className="border border-[#555] p-2.5 text-center">
                  {link ? (
                    <a
                      href={link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent-blue hover:underline"
                    >
                      🔗
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </motion.div>
  );
}

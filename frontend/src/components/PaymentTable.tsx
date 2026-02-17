import type { Payment } from '../lib/types';
import { motion } from 'framer-motion';

interface PaymentTableProps {
  payments: Payment[];
}

function formatMoney(value: number): string {
  if (value === null || value === undefined) return '—';
  return value.toLocaleString('ru-RU', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  }).replace(/,/g, ' ');
}

export function PaymentTable({ payments }: PaymentTableProps) {
  const getDiscordLink = (payment: Payment) => {
    if (payment.channel_id === 0) return null;
    return `https://discord.com/channels/${payment.guild_id}/${payment.channel_id}/${payment.message_id}`;
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
            <th className="border border-[#555] p-2.5">Сумма выплаты</th>
            <th className="border border-[#555] p-2.5">Общая сумма</th>
            <th className="border border-[#555] p-2.5">Участников</th>
            <th className="border border-[#555] p-2.5">Дата</th>
            <th className="border border-[#555] p-2.5">Discord</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((payment, index) => {
            const link = getDiscordLink(payment);
            return (
              <motion.tr
                key={payment.message_id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.02 }}
                className="table-row even:bg-[#242424]"
              >
                <td className="border border-[#555] p-2.5">
                  {formatMoney(payment.payment_sum)}
                </td>
                <td className="border border-[#555] p-2.5">
                  {formatMoney(payment.payment_ammount)}
                </td>
                <td className="border border-[#555] p-2.5 text-center">
                  {payment.user_amount}
                </td>
                <td className="border border-[#555] p-2.5">
                  {payment.pay_time ? new Date(payment.pay_time).toLocaleDateString('ru-RU') : '—'}
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

import { useParams, useSearchParams, Link } from 'react-router-dom';
import { useMembers } from '../hooks/useMembers';
import { useUserEvents } from '../hooks/useUserEvents';
import { useUserPayments } from '../hooks/useUserPayments';
import { Layout } from '../components/Layout';
import { MemberTitle } from '../components/MemberTitle';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { BpContent } from '../components/BpContent';
import { EventTable } from '../components/EventTable';
import { PaymentTable } from '../components/PaymentTable';
import { motion, AnimatePresence } from 'framer-motion';

type TabId = 'bp' | 'events' | 'payments';

const TABS: { id: TabId; label: string }[] = [
  { id: 'bp', label: 'Батлпас' },
  { id: 'events', label: 'Посещения' },
  { id: 'payments', label: 'Выплаты' },
];

export function MemberDetailPage() {
  const { uid } = useParams<{ uid: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const userId = uid ?? '';
  const tab = (searchParams.get('tab') as TabId) || 'bp';
  const validTab = TABS.some((t) => t.id === tab) ? tab : 'bp';

  const { data: members } = useMembers(searchParams.get('db') || undefined);
  const { data: events, isLoading: eventsLoading, error: eventsError } = useUserEvents(userId, searchParams.get('db') || undefined);
  const { data: payments, isLoading: paymentsLoading, error: paymentsError } = useUserPayments(userId, searchParams.get('db') || undefined);

  const user = members?.find((m) => m.uid === userId);
  const displayName = user?.display_name ?? 'мембер';

  const setTab = (t: TabId) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', t);
    setSearchParams(next);
  };

  const formatPovDate = (iso: string | null | undefined) => {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return '—';
    }
  };
  const povLine = user
    ? `Повки ${user.pov_count ?? 0} / проверено ${user.checked_pov_count ?? 0} · последний POV: ${formatPovDate(user.last_pov)} · последний проверенный: ${formatPovDate(user.last_checked_pov)}`
    : '';
  const subtitle =
    validTab === 'bp'
      ? (povLine ? `Батлпас · ${displayName} · ${povLine}` : `Батлпас · ${displayName}`)
      : validTab === 'events'
        ? events ? `Сходил на ${events.length} контентов` : 'Загрузка...'
        : payments ? `${payments.length} выплат` : 'Загрузка...';

  return (
    <Layout showSidebar={false}>
      <div className="max-w-4xl mx-auto text-left">
        <Link to="/" className="inline-flex items-center gap-1.5 text-accent-blue hover:underline text-sm mb-4">
          ← На главную
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
          <MemberTitle title={displayName} subtitle={subtitle} />
          <div className="flex gap-2 flex-shrink-0">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                className={`font-display px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  validTab === t.id
                    ? 'bg-accent-blue/20 text-accent-blue border border-accent-blue/40'
                    : 'bg-dark-card/80 border border-dark-border text-dark-textLight hover:bg-white/5 hover:text-white'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          {validTab === 'bp' && (
            <motion.div
              key="bp"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 12 }}
              transition={{ duration: 0.2 }}
            >
              <BpContent userId={userId} />
            </motion.div>
          )}
          {validTab === 'events' && (
            <motion.div
              key="events"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 12 }}
              transition={{ duration: 0.2 }}
            >
              {eventsError && (
                <div className="text-red-400 mb-4">
                  Ошибка: {eventsError instanceof Error ? eventsError.message : 'Unknown error'}
                </div>
              )}
              {eventsLoading || !events ? (
                <LoadingSpinner />
              ) : (
                <div className="overflow-x-auto rounded-2xl border border-dark-border overflow-hidden">
                  <EventTable events={events} />
                </div>
              )}
            </motion.div>
          )}
          {validTab === 'payments' && (
            <motion.div
              key="payments"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 12 }}
              transition={{ duration: 0.2 }}
            >
              {paymentsError && (
                <div className="text-red-400 mb-4">
                  Ошибка: {paymentsError instanceof Error ? paymentsError.message : 'Unknown error'}
                </div>
              )}
              {paymentsLoading || !payments ? (
                <LoadingSpinner />
              ) : (
                <div className="overflow-x-auto rounded-2xl border border-dark-border overflow-hidden">
                  <PaymentTable payments={payments} />
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Layout>
  );
}

import { useParams, useSearchParams } from 'react-router-dom';
import { useUserEvents } from '../hooks/useUserEvents';
import { useMembers } from '../hooks/useMembers';
import { Layout } from '../components/Layout';
import { EventTable } from '../components/EventTable';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function UserEventsPage() {
  const { uid } = useParams<{ uid: string }>();
  const [searchParams] = useSearchParams();
  const db = searchParams.get('db') || undefined;
  
  const userId = uid || '';
  const { data: events, isLoading: eventsLoading, error } = useUserEvents(userId, db);
  const { data: members } = useMembers(db);

  const user = members?.find((m) => m.uid === userId);
  const userName = user?.display_name || 'без имени';

  if (error) {
    return (
      <Layout title="Ошибка" subtitle="Не удалось загрузить данные">
        <div className="text-red-400">
          Ошибка загрузки: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </Layout>
    );
  }

  if (eventsLoading || !events) {
    return (
      <Layout title={userName} subtitle="Загрузка...">
        <LoadingSpinner />
      </Layout>
    );
  }

  const subtitle = `Сходил на ${events.length} контентов (✓ — проведенные, ✗ — дизбанднутые)`;

  return (
    <Layout title={userName} subtitle={subtitle}>
      <EventTable events={events} />
    </Layout>
  );
}

import { useParams, useSearchParams } from 'react-router-dom';
import { useUserPayments } from '../hooks/useUserPayments';
import { useMembers } from '../hooks/useMembers';
import { Layout } from '../components/Layout';
import { PaymentTable } from '../components/PaymentTable';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function UserPaymentsPage() {
  const { uid } = useParams<{ uid: string }>();
  const [searchParams] = useSearchParams();
  const db = searchParams.get('db') || undefined;
  
  const userId = uid || '';
  const { data: payments, isLoading: paymentsLoading, error } = useUserPayments(userId, db);
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

  if (paymentsLoading || !payments) {
    return (
      <Layout title={userName} subtitle="Загрузка...">
        <LoadingSpinner />
      </Layout>
    );
  }

  const subtitle = `${payments.length} выплат мембера`;

  return (
    <Layout title={userName} subtitle={subtitle}>
      <PaymentTable payments={payments} />
    </Layout>
  );
}

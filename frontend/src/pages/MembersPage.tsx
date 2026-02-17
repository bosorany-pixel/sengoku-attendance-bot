import { useSearchParams } from 'react-router-dom';
import { useMembers } from '../hooks/useMembers';
import { Layout } from '../components/Layout';
import { MemberTable } from '../components/MemberTable';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function MembersPage() {
  const [searchParams] = useSearchParams();
  const db = searchParams.get('db') || undefined;
  const { data: members, isLoading, error } = useMembers(db);

  if (error) {
    return (
      <Layout title="Ошибка" subtitle="Не удалось загрузить данные">
        <div className="text-red-400">
          Ошибка загрузки: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      </Layout>
    );
  }

  if (isLoading || !members) {
    return (
      <Layout title="мемберы × контент" subtitle="Загрузка...">
        <LoadingSpinner />
      </Layout>
    );
  }

  const subtitle = `Всего мемберов: ${members.length}`;

  return (
    <Layout title="MORDOR" subtitle={subtitle}>
      <MemberTable members={members} />
    </Layout>
  );
}

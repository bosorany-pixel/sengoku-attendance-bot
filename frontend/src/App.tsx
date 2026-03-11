import { BrowserRouter, Routes, Route, Navigate, useParams, useSearchParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MembersPage } from './pages/MembersPage';
import { MemberDetailPage } from './pages/MemberDetailPage';
import { TimeoutPage } from './pages/TimeoutPage';
import WelcomePage from './pages/WelcomePage';
import { IS_EREBOR } from './lib/install';

function RedirectToMember({ tab }: { tab: string }) {
  const { uid } = useParams<{ uid: string }>();
  const [searchParams] = useSearchParams();
  const db = searchParams.get('db');
  const to = db ? `/member/${uid}?tab=${tab}&db=${db}` : `/member/${uid}?tab=${tab}`;
  return <Navigate to={to} replace />;
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={import.meta.env.BASE_URL}>
        <Routes>
          <Route path="/" element={IS_EREBOR ? <WelcomePage /> : <MembersPage />} />
          <Route path="/welcome" element={IS_EREBOR ? <WelcomePage /> : <Navigate to="/" replace />} />
          <Route path="/members" element={IS_EREBOR ? <MembersPage /> : <Navigate to="/" replace />} />
          <Route path="/member/:uid" element={<MemberDetailPage />} />
          <Route path="/user/:uid" element={<RedirectToMember tab="events" />} />
          <Route path="/payment/:uid" element={<RedirectToMember tab="payments" />} />
          <Route path="/bp/:uid" element={<RedirectToMember tab="bp" />} />
          <Route path="/timeout" element={<TimeoutPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MembersPage } from './pages/MembersPage';
import { UserEventsPage } from './pages/UserEventsPage';
import { UserPaymentsPage } from './pages/UserPaymentsPage';
import { TimeoutPage } from './pages/TimeoutPage';

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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MembersPage />} />
          <Route path="/user/:uid" element={<UserEventsPage />} />
          <Route path="/payment/:uid" element={<UserPaymentsPage />} />
          <Route path="/timeout" element={<TimeoutPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

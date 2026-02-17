import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useUserPayments(uid: string, db?: string) {
  return useQuery({
    queryKey: ['userPayments', uid, db],
    queryFn: () => api.getUserPayments(uid, db),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

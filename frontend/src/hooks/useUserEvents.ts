import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useUserEvents(uid: string, db?: string) {
  return useQuery({
    queryKey: ['userEvents', uid, db],
    queryFn: () => api.getUserEvents(uid, db),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

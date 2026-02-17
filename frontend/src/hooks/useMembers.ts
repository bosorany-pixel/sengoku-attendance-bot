import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useMembers(db?: string) {
  return useQuery({
    queryKey: ['members', db],
    queryFn: () => api.getMembers(db),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

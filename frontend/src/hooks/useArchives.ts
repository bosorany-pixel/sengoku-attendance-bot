import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useArchives() {
  return useQuery({
    queryKey: ['archives'],
    queryFn: () => api.getArchives(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

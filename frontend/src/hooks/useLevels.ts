import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useLevelsAndAchievements() {
  return useQuery({
    queryKey: ['levels'],
    queryFn: () => api.getLevelsAndAchievements(),
    staleTime: 5 * 60 * 1000,
  });
}

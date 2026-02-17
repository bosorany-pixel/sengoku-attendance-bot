import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useUserAchievements(uid: string) {
  return useQuery({
    queryKey: ['userAchievements', uid],
    queryFn: () => api.getUserAchievements(uid),
    enabled: !!uid,
    staleTime: 5 * 60 * 1000,
  });
}

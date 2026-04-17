import { useQuery } from '@tanstack/react-query';
import { getMatches } from '../services/api';

export const useMatches = (treeId: number) => {
  return useQuery({
    queryKey: ['matches', treeId],
    queryFn: () => getMatches(treeId),
    enabled: !!treeId,
  });
};

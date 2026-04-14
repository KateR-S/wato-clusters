import { useQuery } from '@tanstack/react-query';
import { getHypotheses } from '../services/api';

export const useHypotheses = (treeId: number, clusterId: number) => {
  return useQuery({
    queryKey: ['hypotheses', treeId, clusterId],
    queryFn: () => getHypotheses(treeId, clusterId),
    enabled: !!treeId && !!clusterId,
  });
};

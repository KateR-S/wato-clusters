import { useQuery } from '@tanstack/react-query';
import { getClusters, getCluster } from '../services/api';

export const useClusters = () => {
  return useQuery({
    queryKey: ['clusters'],
    queryFn: getClusters,
  });
};

export const useCluster = (id: number) => {
  return useQuery({
    queryKey: ['clusters', id],
    queryFn: () => getCluster(id),
    enabled: !!id,
  });
};

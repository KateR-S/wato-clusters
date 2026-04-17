import { useQuery } from '@tanstack/react-query';
import { getTrees, getTree } from '../services/api';

export const useTrees = () => {
  return useQuery({
    queryKey: ['trees'],
    queryFn: getTrees,
  });
};

export const useTree = (id: number) => {
  return useQuery({
    queryKey: ['trees', id],
    queryFn: () => getTree(id),
    enabled: !!id,
  });
};

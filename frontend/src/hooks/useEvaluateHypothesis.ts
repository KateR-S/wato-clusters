import { useMutation } from '@tanstack/react-query';
import { evaluateHypothesis } from '../services/api';
import type { AnchorEntry } from '../types';

export const useEvaluateHypothesis = (treeId: number, clusterId: number) => {
  return useMutation({
    mutationFn: (anchors: AnchorEntry[]) =>
      evaluateHypothesis(treeId, clusterId, anchors),
  });
};

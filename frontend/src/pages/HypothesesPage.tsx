import { useParams } from 'react-router-dom';
import { useState } from 'react';
import { useHypotheses } from '../hooks/useHypotheses';
import { useEvaluateHypothesis } from '../hooks/useEvaluateHypothesis';
import { useTree } from '../hooks/useTrees';
import { useCluster } from '../hooks/useClusters';
import { HypothesesPanel } from '../components/Hypotheses/HypothesesPanel';
import { EvaluationPanel } from '../components/Hypotheses/EvaluationPanel';
import type { AnchorEntry, Hypothesis } from '../types';

export const HypothesesPage = () => {
  const { treeId, clusterId } = useParams<{ treeId: string; clusterId: string }>();
  const treeIdNum = parseInt(treeId!);
  const clusterIdNum = parseInt(clusterId!);

  const { data: hypotheses = [], isLoading, error } = useHypotheses(treeIdNum, clusterIdNum);
  const { data: tree } = useTree(treeIdNum);
  const { data: cluster } = useCluster(clusterIdNum);

  const [evalResults, setEvalResults] = useState<Hypothesis[] | null>(null);
  const evaluateMutation = useEvaluateHypothesis(treeIdNum, clusterIdNum);

  const handleEvaluate = (anchors: AnchorEntry[]) => {
    evaluateMutation.mutate(anchors, {
      onSuccess: (data) => setEvalResults(data),
    });
  };

  if (isLoading) return <div className="p-8 text-gray-500">Loading hypotheses...</div>;
  if (error) return <div className="p-8 text-red-500">Failed to load hypotheses.</div>;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Placement Hypotheses</h1>
      <p className="text-gray-500 text-sm mb-4">
        Tree #{treeId} × Cluster #{clusterId}
      </p>
      <div className="bg-white rounded border shadow-sm p-4">
        <HypothesesPanel hypotheses={hypotheses} />

        <EvaluationPanel
          treePeople={tree?.people ?? []}
          clusterPeople={cluster?.people ?? []}
          isPending={evaluateMutation.isPending}
          results={evalResults}
          onEvaluate={handleEvaluate}
        />
      </div>
    </div>
  );
};

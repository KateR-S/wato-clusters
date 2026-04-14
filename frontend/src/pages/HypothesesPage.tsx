import { useParams } from 'react-router-dom';
import { useHypotheses } from '../hooks/useHypotheses';
import { HypothesesPanel } from '../components/Hypotheses/HypothesesPanel';

export const HypothesesPage = () => {
  const { treeId, clusterId } = useParams<{ treeId: string; clusterId: string }>();
  const { data: hypotheses = [], isLoading, error } = useHypotheses(
    parseInt(treeId!),
    parseInt(clusterId!)
  );

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
      </div>
    </div>
  );
};

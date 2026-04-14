import { useParams } from 'react-router-dom';
import { useCluster } from '../hooks/useClusters';
import { ClusterViewer } from '../components/Cluster/ClusterViewer';
import { AddClusterPersonForm } from '../components/Cluster/AddClusterPersonForm';
import { AddClusterRelationshipForm } from '../components/Cluster/AddClusterRelationshipForm';

export const ClusterPage = () => {
  const { id } = useParams<{ id: string }>();
  const clusterId = parseInt(id!);
  const { data: cluster, isLoading, error } = useCluster(clusterId);

  if (isLoading) return <div className="p-8 text-gray-500">Loading cluster...</div>;
  if (error || !cluster) return <div className="p-8 text-red-500">Failed to load cluster.</div>;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">{cluster.name}</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <ClusterViewer people={cluster.people} relationships={cluster.relationships} />
        </div>
        <div className="space-y-6">
          <div className="bg-white rounded border p-4 shadow-sm">
            <AddClusterPersonForm clusterId={clusterId} />
          </div>
          <div className="bg-white rounded border p-4 shadow-sm">
            <AddClusterRelationshipForm clusterId={clusterId} people={cluster.people} />
          </div>
        </div>
      </div>
    </div>
  );
};

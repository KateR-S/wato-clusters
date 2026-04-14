import { useNavigate } from 'react-router-dom';
import type { Cluster } from '../../types';

interface Props {
  clusters: Cluster[];
  onDelete: (id: number) => void;
}

export const ClusterList = ({ clusters, onDelete }: Props) => {
  const navigate = useNavigate();

  if (clusters.length === 0) {
    return <p className="text-gray-500 text-sm">No clusters yet. Create one below.</p>;
  }

  return (
    <ul className="space-y-2">
      {clusters.map((cluster) => (
        <li key={cluster.id} className="flex items-center justify-between bg-white p-3 rounded shadow-sm border">
          <div>
            <span className="font-medium">{cluster.name}</span>
            <span className="text-gray-400 text-sm ml-2">
              {new Date(cluster.created_at).toLocaleDateString()}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => navigate(`/clusters/${cluster.id}`)}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded"
            >
              View
            </button>
            <button
              onClick={() => onDelete(cluster.id)}
              className="bg-red-600 hover:bg-red-700 text-white text-sm px-3 py-1 rounded"
            >
              Delete
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
};

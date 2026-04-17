import { useNavigate } from 'react-router-dom';
import type { Tree } from '../../types';

interface Props {
  trees: Tree[];
  onDelete: (id: number) => void;
}

export const TreeList = ({ trees, onDelete }: Props) => {
  const navigate = useNavigate();

  if (trees.length === 0) {
    return <p className="text-gray-500 text-sm">No trees yet. Create one below.</p>;
  }

  return (
    <ul className="space-y-2">
      {trees.map((tree) => (
        <li key={tree.id} className="flex items-center justify-between bg-white p-3 rounded shadow-sm border">
          <div>
            <span className="font-medium">{tree.name}</span>
            <span className="text-gray-400 text-sm ml-2">
              {new Date(tree.created_at).toLocaleDateString()}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => navigate(`/trees/${tree.id}`)}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded"
            >
              View
            </button>
            <button
              onClick={() => onDelete(tree.id)}
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

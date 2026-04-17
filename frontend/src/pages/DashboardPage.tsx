import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTrees } from '../hooks/useTrees';
import { useClusters } from '../hooks/useClusters';
import { createTree, deleteTree, createCluster, deleteCluster } from '../services/api';
import { TreeList } from '../components/Tree/TreeList';
import { ClusterList } from '../components/Cluster/ClusterList';
import { GedcomUpload } from '../components/Tree/GedcomUpload';

export const DashboardPage = () => {
  const queryClient = useQueryClient();
  const { data: trees = [], isLoading: treesLoading } = useTrees();
  const { data: clusters = [], isLoading: clustersLoading } = useClusters();

  const [newTreeName, setNewTreeName] = useState('');
  const [newClusterName, setNewClusterName] = useState('');
  const [showGedcom, setShowGedcom] = useState<number | null>(null);

  const createTreeMutation = useMutation({
    mutationFn: () => createTree(newTreeName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trees'] });
      setNewTreeName('');
    },
  });

  const deleteTreeMutation = useMutation({
    mutationFn: (id: number) => deleteTree(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trees'] }),
  });

  const createClusterMutation = useMutation({
    mutationFn: () => createCluster(newClusterName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] });
      setNewClusterName('');
    },
  });

  const deleteClusterMutation = useMutation({
    mutationFn: (id: number) => deleteCluster(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['clusters'] }),
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-10">
      {/* Trees Section */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">My Trees</h2>
        {treesLoading ? (
          <p className="text-gray-500">Loading...</p>
        ) : (
          <TreeList trees={trees} onDelete={(id) => deleteTreeMutation.mutate(id)} />
        )}
        <form
          onSubmit={(e) => { e.preventDefault(); createTreeMutation.mutate(); }}
          className="mt-4 flex gap-2"
        >
          <input
            placeholder="New tree name"
            value={newTreeName}
            onChange={(e) => setNewTreeName(e.target.value)}
            required
            className="border rounded px-3 py-2 text-sm flex-1"
          />
          <button
            type="submit"
            disabled={createTreeMutation.isPending}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            Create Tree
          </button>
        </form>
        <div className="mt-4">
          <button
            onClick={() => setShowGedcom(showGedcom === -1 ? null : -1)}
            className="text-purple-600 hover:underline text-sm"
          >
            {showGedcom === -1 ? 'Hide GEDCOM Upload' : 'Upload GEDCOM'}
          </button>
          {showGedcom === -1 && trees.length > 0 && (
            <div className="mt-3 bg-white p-4 rounded border">
              <p className="text-sm text-gray-600 mb-3">Select a tree to upload GEDCOM to:</p>
              {trees.map((tree) => (
                <div key={tree.id} className="mb-4">
                  <p className="text-sm font-medium mb-2">{tree.name}</p>
                  <GedcomUpload treeId={tree.id} />
                </div>
              ))}
            </div>
          )}
          {showGedcom === -1 && trees.length === 0 && (
            <p className="text-sm text-gray-500 mt-2">Create a tree first to upload GEDCOM.</p>
          )}
        </div>
      </section>

      {/* Clusters Section */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">My Clusters</h2>
        {clustersLoading ? (
          <p className="text-gray-500">Loading...</p>
        ) : (
          <ClusterList clusters={clusters} onDelete={(id) => deleteClusterMutation.mutate(id)} />
        )}
        <form
          onSubmit={(e) => { e.preventDefault(); createClusterMutation.mutate(); }}
          className="mt-4 flex gap-2"
        >
          <input
            placeholder="New cluster name"
            value={newClusterName}
            onChange={(e) => setNewClusterName(e.target.value)}
            required
            className="border rounded px-3 py-2 text-sm flex-1"
          />
          <button
            type="submit"
            disabled={createClusterMutation.isPending}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            Create Cluster
          </button>
        </form>
      </section>
    </div>
  );
};

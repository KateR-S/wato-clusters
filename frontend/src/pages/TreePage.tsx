import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useTree } from '../hooks/useTrees';
import { useClusters } from '../hooks/useClusters';
import { deletePerson, deleteRelationship } from '../services/api';
import { TreeViewer } from '../components/Tree/TreeViewer';
import { AddPersonForm } from '../components/Tree/AddPersonForm';
import { AddRelationshipForm } from '../components/Tree/AddRelationshipForm';
import { GedcomUpload } from '../components/Tree/GedcomUpload';
import { MatchManager } from '../components/Matches/MatchManager';
import type { Person } from '../types';

export const TreePage = () => {
  const { id } = useParams<{ id: string }>();
  const treeId = parseInt(id!);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { data: tree, isLoading, error } = useTree(treeId);
  const { data: clusters = [] } = useClusters();
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [selectedClusterId, setSelectedClusterId] = useState('');

  const deletePersonMutation = useMutation({
    mutationFn: (personId: number) => deletePerson(treeId, personId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trees', treeId] });
      setSelectedPerson(null);
    },
  });

  const deleteRelMutation = useMutation({
    mutationFn: (relId: number) => deleteRelationship(treeId, relId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trees', treeId] }),
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading tree...</div>;
  if (error || !tree) return <div className="p-8 text-red-500">Failed to load tree.</div>;

  return (
    <div className="flex h-[calc(100vh-64px)]">
      {/* Sidebar */}
      <aside className="w-80 bg-white border-r overflow-y-auto p-4 space-y-6 flex-shrink-0">
        <div>
          <h2 className="text-lg font-bold text-gray-800">{tree.name}</h2>
          <p className="text-sm text-gray-500">{tree.people.length} people, {tree.relationships.length} relationships</p>
        </div>

        <AddPersonForm treeId={treeId} />
        <hr />
        <AddRelationshipForm treeId={treeId} people={tree.people} />
        <hr />
        <GedcomUpload treeId={treeId} />
        <hr />
        <MatchManager treeId={treeId} people={tree.people} />
        <hr />

        <div className="space-y-2">
          <h3 className="font-semibold text-gray-700">Generate Hypotheses</h3>
          <select
            value={selectedClusterId}
            onChange={(e) => setSelectedClusterId(e.target.value)}
            className="w-full border rounded px-2 py-1 text-sm"
          >
            <option value="">Select a cluster</option>
            {clusters.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <button
            onClick={() => {
              if (selectedClusterId) {
                navigate(`/trees/${treeId}/hypotheses/${selectedClusterId}`);
              }
            }}
            disabled={!selectedClusterId}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-1.5 rounded text-sm disabled:opacity-50"
          >
            View Hypotheses
          </button>
        </div>

        {selectedPerson && (
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <h4 className="font-semibold text-blue-800">Selected: {selectedPerson.first_name} {selectedPerson.last_name}</h4>
            <p className="text-sm text-blue-600">
              {selectedPerson.birth_year && `b. ${selectedPerson.birth_year} · `}
              {selectedPerson.sex === 'M' ? '♂ Male' : selectedPerson.sex === 'F' ? '♀ Female' : 'Unknown sex'}
            </p>
            <div className="mt-2 flex gap-2">
              <button
                onClick={() => deletePersonMutation.mutate(selectedPerson.id)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Delete Person
              </button>
              <button onClick={() => setSelectedPerson(null)} className="text-gray-500 text-sm">
                Deselect
              </button>
            </div>
            <div className="mt-2">
              <p className="text-xs text-gray-500 font-medium uppercase mb-1">Relationships</p>
              {tree.relationships
                .filter((r) => r.person1_id === selectedPerson.id || r.person2_id === selectedPerson.id)
                .map((r) => {
                  const other = tree.people.find(
                    (p) => p.id === (r.person1_id === selectedPerson.id ? r.person2_id : r.person1_id)
                  );
                  return (
                    <div key={r.id} className="flex items-center justify-between text-sm">
                      <span>{r.rel_type} of {other?.first_name} {other?.last_name}</span>
                      <button
                        onClick={() => deleteRelMutation.mutate(r.id)}
                        className="text-red-400 hover:text-red-600 text-xs ml-2"
                      >
                        ✕
                      </button>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 p-4 overflow-auto">
        <TreeViewer
          people={tree.people}
          relationships={tree.relationships}
          onPersonClick={setSelectedPerson}
        />
      </main>
    </div>
  );
};

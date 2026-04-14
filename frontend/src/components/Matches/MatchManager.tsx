import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useMatches } from '../../hooks/useMatches';
import { useClusters } from '../../hooks/useClusters';
import { useCluster } from '../../hooks/useClusters';
import { addMatch, deleteMatch } from '../../services/api';
import type { Person } from '../../types';

interface Props {
  treeId: number;
  people: Person[];
}

const ClusterPeopleSelector = ({
  clusterId,
  value,
  onChange,
}: {
  clusterId: number;
  value: string;
  onChange: (v: string) => void;
}) => {
  const { data: cluster } = useCluster(clusterId);
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required
      className="w-full border rounded px-2 py-1 text-sm"
    >
      <option value="">Select cluster person</option>
      {cluster?.people.map((p) => (
        <option key={p.id} value={p.id}>{p.name}</option>
      ))}
    </select>
  );
};

export const MatchManager = ({ treeId, people }: Props) => {
  const queryClient = useQueryClient();
  const { data: matches = [], isLoading } = useMatches(treeId);
  const { data: clusters = [] } = useClusters();

  const [showForm, setShowForm] = useState(false);
  const [personId, setPersonId] = useState('');
  const [clusterId, setClusterId] = useState('');
  const [clusterPersonId, setClusterPersonId] = useState('');
  const [cm, setCm] = useState('');

  const addMutation = useMutation({
    mutationFn: () =>
      addMatch(treeId, {
        person_id: parseInt(personId),
        cluster_person_id: parseInt(clusterPersonId),
        centimorgans: parseFloat(cm),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches', treeId] });
      setShowForm(false);
      setPersonId('');
      setClusterId('');
      setClusterPersonId('');
      setCm('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (matchId: number) => deleteMatch(treeId, matchId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['matches', treeId] }),
  });

  const getPerson = (id: number) => people.find((p) => p.id === id);

  if (isLoading) return <p className="text-sm text-gray-500">Loading matches...</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-700">DNA Matches</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded"
        >
          {showForm ? 'Cancel' : 'Add Match'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={(e) => { e.preventDefault(); addMutation.mutate(); }}
          className="space-y-2 bg-gray-50 p-3 rounded border"
        >
          <select
            value={personId}
            onChange={(e) => setPersonId(e.target.value)}
            required
            className="w-full border rounded px-2 py-1 text-sm"
          >
            <option value="">Select tree person</option>
            {people.map((p) => (
              <option key={p.id} value={p.id}>
                {p.first_name} {p.last_name}
              </option>
            ))}
          </select>
          <select
            value={clusterId}
            onChange={(e) => { setClusterId(e.target.value); setClusterPersonId(''); }}
            required
            className="w-full border rounded px-2 py-1 text-sm"
          >
            <option value="">Select cluster</option>
            {clusters.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          {clusterId && (
            <ClusterPeopleSelector
              clusterId={parseInt(clusterId)}
              value={clusterPersonId}
              onChange={setClusterPersonId}
            />
          )}
          <input
            type="number"
            step="0.1"
            placeholder="Centimorgans (cM)"
            value={cm}
            onChange={(e) => setCm(e.target.value)}
            required
            className="w-full border rounded px-2 py-1 text-sm"
          />
          <button
            type="submit"
            disabled={addMutation.isPending}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-1.5 rounded text-sm disabled:opacity-50"
          >
            {addMutation.isPending ? 'Saving...' : 'Save Match'}
          </button>
        </form>
      )}

      {matches.length === 0 ? (
        <p className="text-sm text-gray-500">No matches recorded yet.</p>
      ) : (
        <ul className="space-y-2">
          {matches.map((match) => {
            const person = getPerson(match.person_id);
            return (
              <li key={match.id} className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded border text-sm">
                <div>
                  <span className="font-medium">
                    {person ? `${person.first_name} ${person.last_name}` : `Person #${match.person_id}`}
                  </span>
                  <span className="text-gray-500 ml-2">↔ Cluster Person #{match.cluster_person_id}</span>
                  <span className="ml-2 text-blue-600 font-medium">{match.centimorgans} cM</span>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(match.id)}
                  className="text-red-500 hover:text-red-700 text-xs"
                >
                  Remove
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

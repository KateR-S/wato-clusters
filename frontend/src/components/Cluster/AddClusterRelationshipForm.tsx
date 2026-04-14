import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { addClusterRelationship } from '../../services/api';
import type { ClusterPerson } from '../../types';

interface Props {
  clusterId: number;
  people: ClusterPerson[];
}

export const AddClusterRelationshipForm = ({ clusterId, people }: Props) => {
  const queryClient = useQueryClient();
  const [person1Id, setPerson1Id] = useState('');
  const [person2Id, setPerson2Id] = useState('');
  const [relType, setRelType] = useState('parent');

  const mutation = useMutation({
    mutationFn: () =>
      addClusterRelationship(clusterId, {
        person1_id: parseInt(person1Id),
        person2_id: parseInt(person2Id),
        rel_type: relType,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters', clusterId] });
      setPerson1Id('');
      setPerson2Id('');
      setRelType('parent');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="font-semibold text-gray-700">Add Relationship</h3>
      {mutation.isError && <div className="text-red-600 text-sm">Failed to add relationship.</div>}
      <select
        value={person1Id}
        onChange={(e) => setPerson1Id(e.target.value)}
        required
        className="w-full border rounded px-2 py-1 text-sm"
      >
        <option value="">Select Person 1</option>
        {people.map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
      <select
        value={relType}
        onChange={(e) => setRelType(e.target.value)}
        className="w-full border rounded px-2 py-1 text-sm"
      >
        <option value="parent">Parent</option>
        <option value="spouse">Spouse</option>
        <option value="sibling">Sibling</option>
        <option value="half-sibling">Half-Sibling</option>
      </select>
      <select
        value={person2Id}
        onChange={(e) => setPerson2Id(e.target.value)}
        required
        className="w-full border rounded px-2 py-1 text-sm"
      >
        <option value="">Select Person 2</option>
        {people.map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </select>
      <button
        type="submit"
        disabled={mutation.isPending}
        className="w-full bg-green-600 hover:bg-green-700 text-white py-1.5 rounded text-sm disabled:opacity-50"
      >
        {mutation.isPending ? 'Adding...' : 'Add Relationship'}
      </button>
    </form>
  );
};

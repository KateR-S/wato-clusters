import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { addClusterPerson } from '../../services/api';

interface Props {
  clusterId: number;
}

export const AddClusterPersonForm = ({ clusterId }: Props) => {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [birthYear, setBirthYear] = useState('');

  const mutation = useMutation({
    mutationFn: () =>
      addClusterPerson(clusterId, {
        name,
        birth_year: birthYear ? parseInt(birthYear) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters', clusterId] });
      setName('');
      setBirthYear('');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="font-semibold text-gray-700">Add Person to Cluster</h3>
      {mutation.isError && <div className="text-red-600 text-sm">Failed to add person.</div>}
      <input
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
        className="w-full border rounded px-2 py-1 text-sm"
      />
      <input
        type="number"
        placeholder="Birth year (optional)"
        value={birthYear}
        onChange={(e) => setBirthYear(e.target.value)}
        className="w-full border rounded px-2 py-1 text-sm"
      />
      <button
        type="submit"
        disabled={mutation.isPending}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-1.5 rounded text-sm disabled:opacity-50"
      >
        {mutation.isPending ? 'Adding...' : 'Add Person'}
      </button>
    </form>
  );
};

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { addPerson } from '../../services/api';

interface Props {
  treeId: number;
}

export const AddPersonForm = ({ treeId }: Props) => {
  const queryClient = useQueryClient();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [sex, setSex] = useState<'M' | 'F' | 'U'>('U');

  const mutation = useMutation({
    mutationFn: () =>
      addPerson(treeId, {
        first_name: firstName,
        last_name: lastName,
        birth_year: birthYear ? parseInt(birthYear) : undefined,
        sex,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trees', treeId] });
      setFirstName('');
      setLastName('');
      setBirthYear('');
      setSex('U');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="font-semibold text-gray-700">Add Person</h3>
      {mutation.isError && (
        <div className="text-red-600 text-sm">Failed to add person.</div>
      )}
      <div className="grid grid-cols-2 gap-2">
        <input
          placeholder="First name"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
          className="border rounded px-2 py-1 text-sm"
        />
        <input
          placeholder="Last name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          required
          className="border rounded px-2 py-1 text-sm"
        />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <input
          type="number"
          placeholder="Birth year"
          value={birthYear}
          onChange={(e) => setBirthYear(e.target.value)}
          className="border rounded px-2 py-1 text-sm"
        />
        <select
          value={sex}
          onChange={(e) => setSex(e.target.value as 'M' | 'F' | 'U')}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="U">Unknown</option>
          <option value="M">Male</option>
          <option value="F">Female</option>
        </select>
      </div>
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

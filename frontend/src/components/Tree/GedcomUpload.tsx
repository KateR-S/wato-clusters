import { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadGedcom } from '../../services/api';

interface Props {
  treeId: number;
}

export const GedcomUpload = ({ treeId }: Props) => {
  const queryClient = useQueryClient();
  const [treeName, setTreeName] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: () => {
      const file = fileRef.current?.files?.[0];
      if (!file) throw new Error('No file selected');
      return uploadGedcom(treeId, file, treeName);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trees', treeId] });
      setTreeName('');
      if (fileRef.current) fileRef.current.value = '';
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="font-semibold text-gray-700">Upload GEDCOM</h3>
      {mutation.isError && (
        <div className="text-red-600 text-sm">Upload failed.</div>
      )}
      {mutation.isSuccess && (
        <div className="text-green-600 text-sm">Uploaded successfully!</div>
      )}
      <input
        type="text"
        placeholder="Tree name"
        value={treeName}
        onChange={(e) => setTreeName(e.target.value)}
        required
        className="w-full border rounded px-2 py-1 text-sm"
      />
      <input
        ref={fileRef}
        type="file"
        accept=".ged"
        required
        className="w-full text-sm"
      />
      <button
        type="submit"
        disabled={mutation.isPending}
        className="w-full bg-purple-600 hover:bg-purple-700 text-white py-1.5 rounded text-sm disabled:opacity-50"
      >
        {mutation.isPending ? 'Uploading...' : 'Upload GEDCOM'}
      </button>
    </form>
  );
};

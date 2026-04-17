import { useState } from 'react';
import type { Person, ClusterPerson, AnchorEntry, Hypothesis } from '../../types';
import { HypothesesPanel } from './HypothesesPanel';

// All relationship types that can appear in the hypothesis engine.
// Must stay in sync with CM_RANGES in backend/app/hypothesis_engine.py.
const RELATIONSHIP_TYPES = [
  'parent',
  'child',
  'full_sibling',
  'half_sibling',
  'grandparent',
  'grandchild',
  'aunt_uncle',
  'niece_nephew',
  'half_aunt_uncle',
  'half_niece_nephew',
  'great_grandparent',
  'great_grandchild',
  '1st_cousin',
  '1st_cousin_1r',
  '1st_cousin_2r',
  '2nd_cousin',
  '2nd_cousin_1r',
  '3rd_cousin',
  'half_1st_cousin',
] as const;

interface AnchorRow {
  cluster_person_id: string;
  tree_person_id: string;
  relationship: string;
}

interface Props {
  treePeople: Person[];
  clusterPeople: ClusterPerson[];
  isPending: boolean;
  results: Hypothesis[] | null;
  onEvaluate: (anchors: AnchorEntry[]) => void;
}

const emptyRow = (): AnchorRow => ({
  cluster_person_id: '',
  tree_person_id: '',
  relationship: RELATIONSHIP_TYPES[0],
});

export const EvaluationPanel = ({
  treePeople,
  clusterPeople,
  isPending,
  results,
  onEvaluate,
}: Props) => {
  const [rows, setRows] = useState<AnchorRow[]>([emptyRow()]);

  const updateRow = (index: number, field: keyof AnchorRow, value: string) => {
    setRows((prev) =>
      prev.map((r, i) => (i === index ? { ...r, [field]: value } : r))
    );
  };

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);

  const removeRow = (index: number) =>
    setRows((prev) => prev.filter((_, i) => i !== index));

  const handleEvaluate = () => {
    const anchors: AnchorEntry[] = rows
      .filter((r) => r.cluster_person_id && r.tree_person_id && r.relationship)
      .map((r) => ({
        cluster_person_id: parseInt(r.cluster_person_id),
        tree_person_id: parseInt(r.tree_person_id),
        relationship: r.relationship,
      }));
    onEvaluate(anchors);
  };

  const hasValidRow = rows.some(
    (r) => r.cluster_person_id && r.tree_person_id && r.relationship
  );

  return (
    <div className="mt-8 border-t pt-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-1">
        Evaluate a Posited Relationship
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Specify one or more fixed (cluster person → tree person → relationship)
        anchors, then evaluate how well they fit the observed cM data.
      </p>

      <div className="space-y-2 mb-4">
        {rows.map((row, i) => (
          <div key={i} className="flex flex-wrap gap-2 items-center">
            {/* Cluster person */}
            <select
              value={row.cluster_person_id}
              onChange={(e) => updateRow(i, 'cluster_person_id', e.target.value)}
              className="border rounded px-2 py-1 text-sm min-w-[140px]"
            >
              <option value="">Cluster person…</option>
              {clusterPeople.map((cp) => (
                <option key={cp.id} value={cp.id}>
                  {cp.name}
                </option>
              ))}
            </select>

            <span className="text-gray-400 text-sm">is</span>

            {/* Relationship */}
            <select
              value={row.relationship}
              onChange={(e) => updateRow(i, 'relationship', e.target.value)}
              className="border rounded px-2 py-1 text-sm min-w-[160px]"
            >
              {RELATIONSHIP_TYPES.map((rel) => (
                <option key={rel} value={rel}>
                  {rel}
                </option>
              ))}
            </select>

            <span className="text-gray-400 text-sm">of</span>

            {/* Tree person */}
            <select
              value={row.tree_person_id}
              onChange={(e) => updateRow(i, 'tree_person_id', e.target.value)}
              className="border rounded px-2 py-1 text-sm min-w-[140px]"
            >
              <option value="">Tree person…</option>
              {treePeople.map((tp) => (
                <option key={tp.id} value={tp.id}>
                  {tp.first_name} {tp.last_name}
                </option>
              ))}
            </select>

            {rows.length > 1 && (
              <button
                onClick={() => removeRow(i)}
                className="text-red-500 hover:text-red-700 text-xs px-1"
                title="Remove this anchor"
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2 mb-6">
        <button
          onClick={addRow}
          className="text-sm text-blue-600 hover:underline"
        >
          + Add another anchor
        </button>
        <button
          onClick={handleEvaluate}
          disabled={!hasValidRow || isPending}
          className="ml-auto px-4 py-1.5 bg-blue-600 text-white text-sm rounded
                     hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPending ? 'Evaluating…' : 'Evaluate'}
        </button>
      </div>

      {results !== null && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">
            Evaluation Results
          </h3>
          {results.length === 0 ? (
            <p className="text-sm text-gray-500 italic">
              No consistent hypotheses found for the posited relationship(s).
              The anchors may conflict with the generational structure of the tree.
            </p>
          ) : (
            <div className="bg-white rounded border shadow-sm p-4">
              <HypothesesPanel hypotheses={results} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

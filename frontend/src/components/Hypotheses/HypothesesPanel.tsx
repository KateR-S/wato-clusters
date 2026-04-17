import { useState } from 'react';
import type { Hypothesis } from '../../types';

interface Props {
  hypotheses: Hypothesis[];
}

export const HypothesesPanel = ({ hypotheses }: Props) => {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (hypotheses.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No hypotheses generated yet.</p>
        <p className="text-sm mt-1">Add DNA matches and generate hypotheses from the tree page.</p>
      </div>
    );
  }

  const getLikelihoodColor = (percent: number) => {
    if (percent > 50) return 'bg-green-100 text-green-800';
    if (percent >= 20) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const sorted = [...hypotheses].sort((a, b) => b.likelihood_percent - a.likelihood_percent);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="px-4 py-2 border">Rank</th>
            <th className="px-4 py-2 border">Likelihood</th>
            <th className="px-4 py-2 border">Placements</th>
            <th className="px-4 py-2 border">Details</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((hyp) => (
            <>
              <tr key={hyp.rank} className="border-b hover:bg-gray-50">
                <td className="px-4 py-2 border font-medium">#{hyp.rank}</td>
                <td className="px-4 py-2 border">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getLikelihoodColor(hyp.likelihood_percent)}`}>
                    {hyp.likelihood_percent.toFixed(1)}%
                  </span>
                </td>
                <td className="px-4 py-2 border text-gray-600">
                  {hyp.placements.length} placement(s)
                </td>
                <td className="px-4 py-2 border">
                  <button
                    onClick={() => setExpanded(expanded === hyp.rank ? null : hyp.rank)}
                    className="text-blue-600 hover:underline text-xs"
                  >
                    {expanded === hyp.rank ? 'Hide' : 'Show'}
                  </button>
                </td>
              </tr>
              {expanded === hyp.rank && (
                <tr key={`${hyp.rank}-detail`}>
                  <td colSpan={4} className="px-4 py-3 bg-gray-50 border-b">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-gray-500">
                          <th className="text-left pb-1">Cluster Person</th>
                          <th className="text-left pb-1">Relationship</th>
                          <th className="text-left pb-1">Tree Person</th>
                          <th className="text-left pb-1">Observed cM</th>
                          <th className="text-left pb-1">Expected Range</th>
                        </tr>
                      </thead>
                      <tbody>
                        {hyp.placements.map((p, i) => (
                          <tr key={i} className="border-t">
                            <td className="py-1 pr-3">{p.cluster_person_name}</td>
                            <td className="py-1 pr-3 font-medium">{p.relationship}</td>
                            <td className="py-1 pr-3">{p.tree_person_name}</td>
                            <td className="py-1 pr-3">{p.cm_observed} cM</td>
                            <td className="py-1">{p.cm_min}–{p.cm_max} cM</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
};

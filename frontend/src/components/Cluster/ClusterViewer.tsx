import type { ClusterPerson, ClusterRelationship } from '../../types';

interface Props {
  people: ClusterPerson[];
  relationships: ClusterRelationship[];
}

export const ClusterViewer = ({ people, relationships }: Props) => {
  if (people.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 bg-gray-50 rounded border-2 border-dashed border-gray-300">
        <p className="text-gray-500">No people in this cluster yet.</p>
      </div>
    );
  }

  const getRelationships = (personId: number) =>
    relationships.filter(
      (r) => r.person1_id === personId || r.person2_id === personId
    );

  const getOtherPerson = (rel: ClusterRelationship, personId: number) => {
    const otherId = rel.person1_id === personId ? rel.person2_id : rel.person1_id;
    return people.find((p) => p.id === otherId);
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {people.map((person) => {
        const rels = getRelationships(person.id);
        return (
          <div key={person.id} className="bg-white rounded border shadow-sm p-4">
            <h4 className="font-semibold text-gray-800">{person.name}</h4>
            {person.birth_year && (
              <p className="text-gray-500 text-sm">b. {person.birth_year}</p>
            )}
            {rels.length > 0 && (
              <div className="mt-2">
                <p className="text-xs text-gray-500 font-medium uppercase">Relationships</p>
                <ul className="mt-1 space-y-1">
                  {rels.map((rel) => {
                    const other = getOtherPerson(rel, person.id);
                    return (
                      <li key={rel.id} className="text-sm text-gray-600">
                        <span className="font-medium">{rel.rel_type}</span> of{' '}
                        {other?.name ?? 'Unknown'}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

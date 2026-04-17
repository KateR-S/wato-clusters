import { useMemo, useRef, useEffect, useState } from 'react';
import Tree from 'react-d3-tree';
import type { RawNodeDatum, CustomNodeElementProps } from 'react-d3-tree';
import type { Person, Relationship } from '../../types';

interface Props {
  people: Person[];
  relationships: Relationship[];
  onPersonClick?: (person: Person) => void;
}

function buildHierarchy(people: Person[], relationships: Relationship[]): RawNodeDatum[] {
  if (people.length === 0) return [];

  const childIds = new Set<number>();
  relationships.forEach((r) => {
    if (r.rel_type === 'parent') {
      childIds.add(r.person2_id);
    }
  });

  const roots = people.filter((p) => !childIds.has(p.id));
  const rootList = roots.length > 0 ? roots : [people[0]];

  const visited = new Set<number>();

  function buildNode(person: Person): RawNodeDatum {
    visited.add(person.id);
    const sexIcon = person.sex === 'M' ? '♂' : person.sex === 'F' ? '♀' : '⚧';
    const childRels = relationships.filter(
      (r) => r.rel_type === 'parent' && r.person1_id === person.id
    );
    const children: RawNodeDatum[] = childRels
      .map((r) => people.find((p) => p.id === r.person2_id))
      .filter((p): p is Person => !!p && !visited.has(p.id))
      .map(buildNode);

    return {
      name: `${person.first_name} ${person.last_name}`,
      attributes: {
        'Birth Year': person.birth_year ?? '',
        Sex: sexIcon,
        id: person.id,
      },
      children,
    };
  }

  return rootList.map(buildNode);
}

const renderNode = ({ nodeDatum }: CustomNodeElementProps) => (
  <g>
    <circle r={20} fill="#3b82f6" stroke="#1d4ed8" strokeWidth={2} />
    <text fill="white" textAnchor="middle" dy={5} fontSize={12}>
      {String(nodeDatum.attributes?.Sex ?? '')}
    </text>
    <text fill="#1f2937" textAnchor="middle" dy={40} fontSize={11}>
      {nodeDatum.name}
    </text>
    {nodeDatum.attributes?.['Birth Year'] && (
      <text fill="#6b7280" textAnchor="middle" dy={55} fontSize={10}>
        b. {nodeDatum.attributes['Birth Year']}
      </text>
    )}
  </g>
);

export const TreeViewer = ({ people, relationships, onPersonClick }: Props) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth || 800,
        height: containerRef.current.offsetHeight || 500,
      });
    }
  }, []);

  const treeData = useMemo(() => buildHierarchy(people, relationships), [people, relationships]);

  if (people.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded border-2 border-dashed border-gray-300">
        <p className="text-gray-500">No people in this tree yet. Add someone to get started.</p>
      </div>
    );
  }

  const handleNodeClick = (nodeDatum: RawNodeDatum) => {
    if (onPersonClick && nodeDatum.attributes?.id) {
      const person = people.find((p) => p.id === Number(nodeDatum.attributes!.id));
      if (person) onPersonClick(person);
    }
  };

  return (
    <div ref={containerRef} className="w-full h-[500px] bg-white border rounded shadow-sm">
      <Tree
        data={treeData}
        dimensions={dimensions}
        translate={{ x: dimensions.width / 2, y: 60 }}
        renderCustomNodeElement={renderNode}
        onNodeClick={(node) => handleNodeClick(node.data)}
        orientation="vertical"
        separation={{ siblings: 2, nonSiblings: 2 }}
        nodeSize={{ x: 180, y: 120 }}
      />
    </div>
  );
};

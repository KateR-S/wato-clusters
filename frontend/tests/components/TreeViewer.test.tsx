import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TreeViewer } from '../../src/components/Tree/TreeViewer';
import type { Person, Relationship } from '../../src/types';

vi.mock('react-d3-tree', () => ({
  default: ({ data }: { data: { name: string }[] }) => (
    <div data-testid="tree-mock">
      {data.map((node: { name: string }, i: number) => (
        <div key={i}>{node.name}</div>
      ))}
    </div>
  ),
}));

const mockPeople: Person[] = [
  { id: 1, tree_id: 1, first_name: 'Alice', last_name: 'Smith', sex: 'F', birth_year: 1980 },
  { id: 2, tree_id: 1, first_name: 'Bob', last_name: 'Smith', sex: 'M', birth_year: 1950 },
];

const mockRelationships: Relationship[] = [
  { id: 1, tree_id: 1, person1_id: 2, person2_id: 1, rel_type: 'parent' },
];

describe('TreeViewer', () => {
  it('shows empty state when no people', () => {
    render(<TreeViewer people={[]} relationships={[]} />);
    expect(screen.getByText(/no people in this tree/i)).toBeInTheDocument();
  });

  it('renders tree when people are provided', () => {
    render(<TreeViewer people={mockPeople} relationships={mockRelationships} />);
    expect(screen.getByTestId('tree-mock')).toBeInTheDocument();
  });

  it('displays root person name in tree', () => {
    render(<TreeViewer people={mockPeople} relationships={mockRelationships} />);
    expect(screen.getByText(/Bob Smith/)).toBeInTheDocument();
  });
});

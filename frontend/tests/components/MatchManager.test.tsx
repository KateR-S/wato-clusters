import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MatchManager } from '../../src/components/Matches/MatchManager';
import type { Person, Match } from '../../src/types';

vi.mock('../../src/services/api', () => ({
  getMatches: vi.fn().mockResolvedValue([
    { id: 1, tree_id: 1, person_id: 1, cluster_person_id: 1, centimorgans: 350 },
  ] as Match[]),
  getClusters: vi.fn().mockResolvedValue([]),
  getCluster: vi.fn().mockResolvedValue({ id: 1, name: 'Test', people: [], relationships: [], created_at: '' }),
  addMatch: vi.fn(),
  deleteMatch: vi.fn(),
}));

const mockPeople: Person[] = [
  { id: 1, tree_id: 1, first_name: 'Alice', last_name: 'Smith', sex: 'F' },
];

const makeQueryClient = () => new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

describe('MatchManager', () => {
  it('renders without crashing', async () => {
    render(
      <QueryClientProvider client={makeQueryClient()}>
        <MatchManager treeId={1} people={mockPeople} />
      </QueryClientProvider>
    );
    await waitFor(() => {
      expect(screen.getByText(/DNA Matches/i)).toBeInTheDocument();
    });
  });

  it('shows Add Match button', async () => {
    render(
      <QueryClientProvider client={makeQueryClient()}>
        <MatchManager treeId={1} people={mockPeople} />
      </QueryClientProvider>
    );
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add match/i })).toBeInTheDocument();
    });
  });
});

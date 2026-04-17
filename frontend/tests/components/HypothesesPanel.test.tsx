import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { HypothesesPanel } from '../../src/components/Hypotheses/HypothesesPanel';
import type { Hypothesis } from '../../src/types';

const mockHypotheses: Hypothesis[] = [
  {
    rank: 1,
    likelihood_score: 0.8,
    likelihood_percent: 80,
    placements: [
      {
        cluster_person_id: 1,
        cluster_person_name: 'John Doe',
        tree_person_id: 1,
        tree_person_name: 'Jane Smith',
        relationship: 'cousin',
        cm_observed: 350,
        cm_min: 300,
        cm_max: 400,
        score: 0.9,
      },
    ],
  },
  {
    rank: 2,
    likelihood_score: 0.3,
    likelihood_percent: 30,
    placements: [
      {
        cluster_person_id: 2,
        cluster_person_name: 'Jane Doe',
        tree_person_id: 2,
        tree_person_name: 'John Smith',
        relationship: 'half-sibling',
        cm_observed: 800,
        cm_min: 700,
        cm_max: 900,
        score: 0.5,
      },
    ],
  },
];

describe('HypothesesPanel', () => {
  it('renders empty state when no hypotheses', () => {
    render(<HypothesesPanel hypotheses={[]} />);
    expect(screen.getByText(/no hypotheses generated/i)).toBeInTheDocument();
  });

  it('renders table with hypotheses data', () => {
    render(<HypothesesPanel hypotheses={mockHypotheses} />);
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('#2')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    expect(screen.getByText('30.0%')).toBeInTheDocument();
  });

  it('shows placements when expanded', () => {
    render(<HypothesesPanel hypotheses={mockHypotheses} />);
    const showButtons = screen.getAllByText('Show');
    fireEvent.click(showButtons[0]);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('cousin')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
  });

  it('colors hypotheses by likelihood', () => {
    render(<HypothesesPanel hypotheses={mockHypotheses} />);
    const greenBadge = screen.getByText('80.0%');
    expect(greenBadge).toHaveClass('bg-green-100');
    const yellowBadge = screen.getByText('30.0%');
    expect(yellowBadge).toHaveClass('bg-yellow-100');
  });
});

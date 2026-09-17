import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import KpiCards from '../KpiCards';

describe('KpiCards Component', () => {
  it('renders the six primary intelligence metrics without invented deltas', () => {
    const kpis = {
      total_mentions: 1250,
      positive_pct: 62.5,
      negative_pct: 21.0,
      neutral_pct: 10.0,
      mixed_pct: 6.5,
      viral_posts_count: 8,
      top_trending_topic: 'Pegasus 41 Launch',
      top_complaint: 'Pricing',
      top_positive_topic: 'Product Comfort',
    };

    render(<KpiCards kpis={kpis} loading={false} />);

    expect(screen.getByText('1,250')).toBeInTheDocument();
    expect(screen.getByText('62.5%')).toBeInTheDocument();
    expect(screen.getByText('21%')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('Pegasus 41 Launch')).toBeInTheDocument();
    expect(screen.getByText('Pricing')).toBeInTheDocument();
    expect(screen.getAllByTestId('kpi-card')).toHaveLength(6);
    expect(screen.queryByText('Product Comfort')).not.toBeInTheDocument();
    expect(screen.queryByText('+12% volume')).not.toBeInTheDocument();
  });
});

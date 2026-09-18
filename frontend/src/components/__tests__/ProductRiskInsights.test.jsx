import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import ProductRiskInsights from '../ProductRiskInsights';


describe('ProductRiskInsights', () => {
  it('shows product praise, complaints, attention and evidence-backed risks', () => {
    const onSelectProduct = vi.fn();
    render(
      <ProductRiskInsights
        products={[{
          product: 'Pegasus', mention_count: 18, positive_count: 9, negative_count: 6,
          top_praise: 'Comfort', top_complaint: 'Durability', average_attention: 72,
        }]}
        risks={[{
          id: 1, title: 'Pegasus durability concerns', product: 'Pegasus', aspect: 'Durability',
          mention_count: 6, unique_sources: 4, growth_pct: 80, attention_score: 76,
          risk_score: 68, risk_level: 'Elevated', confidence: 0.9,
        }]}
        onSelectProduct={onSelectProduct}
      />,
    );

    expect(screen.getByText('Product Intelligence')).toBeInTheDocument();
    expect(screen.getByText('Reputation Risks')).toBeInTheDocument();
    expect(screen.getByText('Comfort')).toBeInTheDocument();
    expect(screen.getAllByText('Durability').length).toBeGreaterThan(0);
    expect(screen.getByText('72 / 100')).toBeInTheDocument();
    expect(screen.getByText('Elevated')).toBeInTheDocument();
    expect(screen.getByText('4 independent sources')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /filter conversations for pegasus/i }));
    expect(onSelectProduct).toHaveBeenCalledWith('Pegasus');
  });

  it('wires alert, export and competitor actions', () => {
    const onOpenAlerts = vi.fn();
    const onSelectCompetitor = vi.fn();
    render(
      <ProductRiskInsights
        brandId={7}
        competitors={[{ competitor: 'Puma', mention_count: 2, positive_count: 1, negative_count: 0, top_topics: ['Running'] }]}
        onOpenAlerts={onOpenAlerts}
        onSelectCompetitor={onSelectCompetitor}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /manage alerts/i }));
    fireEvent.click(screen.getByRole('button', { name: /puma/i }));
    expect(onOpenAlerts).toHaveBeenCalledTimes(1);
    expect(onSelectCompetitor).toHaveBeenCalledWith('Puma');
    expect(screen.getByRole('link', { name: /export csv/i })).toHaveAttribute('href', '/api/intelligence/export.csv?brand_id=7');
    expect(screen.getByRole('link', { name: /export pdf/i })).toHaveAttribute('href', '/api/intelligence/export.pdf?brand_id=7');
  });

  it('offers to analyze existing conversations when product intelligence is empty', () => {
    const onRebuild = vi.fn();
    render(<ProductRiskInsights onRebuild={onRebuild} />);

    fireEvent.click(screen.getByRole('button', { name: /analyze existing conversations/i }));
    expect(onRebuild).toHaveBeenCalledTimes(1);
  });
});

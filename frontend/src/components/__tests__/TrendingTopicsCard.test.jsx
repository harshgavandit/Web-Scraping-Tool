import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import TrendingTopicsCard from '../TrendingTopicsCard';

describe('TrendingTopicsCard', () => {
  it('toggles topic and competitor filters with accessible pressed state', () => {
    const onSelectTopic = vi.fn();
    const onSelectCompetitor = vi.fn();
    const { rerender } = render(
      <TrendingTopicsCard
        topics={[{ topic: 'Pricing & Value', pct_change: 20 }]}
        competitors={['Adidas']}
        onSelectTopic={onSelectTopic}
        onSelectCompetitor={onSelectCompetitor}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /pricing & value/i }));
    fireEvent.click(screen.getByRole('button', { name: /vs adidas/i }));
    expect(onSelectTopic).toHaveBeenCalledWith('Pricing & Value');
    expect(onSelectCompetitor).toHaveBeenCalledWith('Adidas');

    rerender(
      <TrendingTopicsCard
        topics={[{ topic: 'Pricing & Value', pct_change: 20 }]}
        competitors={['Adidas']}
        activeTopic="Pricing & Value"
        activeCompetitor="Adidas"
        onSelectTopic={onSelectTopic}
        onSelectCompetitor={onSelectCompetitor}
      />
    );
    expect(screen.getByRole('button', { name: /pricing & value/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /vs adidas/i })).toHaveAttribute('aria-pressed', 'true');
  });
});

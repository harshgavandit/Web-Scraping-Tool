import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import FilterBar from '../FilterBar';

describe('FilterBar Component', () => {
  it('handles search and viral toggles', () => {
    const handleChange = vi.fn();
    const handleReset = vi.fn();

    const filters = {
      brand_id: 1,
      source: 'all',
      sentiment: 'all',
      product: 'all',
      competitor: 'all',
      virality_level: 'all',
      viral: false,
      search: '',
      sort_by: 'newest',
    };

    render(
      <FilterBar
        filters={filters}
        onChange={handleChange}
        onReset={handleReset}
        brands={[{ id: 1, name: 'Nike' }]}
        competitors={['Adidas', 'Puma']}
        products={['Pegasus', 'Air Max']}
      />
    );

    // Toggle Viral Only
    const viralBtn = screen.getByRole('button', { name: /viral only/i });
    fireEvent.click(viralBtn);
    expect(handleChange).toHaveBeenCalledWith(
      expect.objectContaining({ viral: true })
    );

    // Change Sort
    const sortSelect = screen.getByDisplayValue('Newest First');
    fireEvent.change(sortSelect, { target: { value: 'highest_virality' } });
    expect(handleChange).toHaveBeenCalledWith(
      expect.objectContaining({ sort_by: 'highest_virality' })
    );
  });

  it('keeps advanced filters behind a compact disclosure', () => {
    const filters = {
      brand_id: 1,
      source: 'all', sentiment: 'all', topic: 'all', product: 'all',
      competitor: 'all', virality_level: 'all', viral: false,
      search: '', sort_by: 'newest',
    };

    render(
      <FilterBar
        filters={filters}
        onChange={vi.fn()}
        onReset={vi.fn()}
        brands={[{ id: 1, name: 'Nike' }]}
        competitors={['Adidas']}
        products={['Pegasus']}
      />
    );

    expect(screen.queryByLabelText('Filter by source')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /more filters/i }));
    expect(screen.getByLabelText('Filter by source')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Publisher RSS / Atom' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /hide filters/i })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.queryByRole('option', { name: /twitter/i })).not.toBeInTheDocument();
  });

  it('makes every quick filter actionable and clears all filters through reset', () => {
    const onChange = vi.fn();
    const onReset = vi.fn();
    const filters = {
      brand_id: 1,
      source: 'web', sentiment: 'all', topic: 'Pricing', product: 'Pegasus',
      competitor: 'all', virality_level: 'High', viral: false,
      search: 'comfort', sort_by: 'newest', page: 3,
    };

    render(
      <FilterBar
        filters={filters}
        onChange={onChange}
        onReset={onReset}
        brands={[{ id: 1, name: 'Nike' }]}
        competitors={['Adidas', 'Puma']}
        products={['Pegasus']}
      />
    );

    expect(screen.getByRole('button', { name: 'All' })).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(screen.getByRole('button', { name: 'Negative' }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ sentiment: 'Negative', page: 1 }));

    fireEvent.click(screen.getByRole('button', { name: 'Positive' }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ sentiment: 'Positive', page: 1 }));

    fireEvent.click(screen.getByRole('button', { name: /competitors/i }));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ competitor: 'any', page: 1 }));

    fireEvent.click(screen.getByRole('button', { name: 'All' }));
    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it('wraps quick filters instead of clipping controls in a horizontal scroller', () => {
    render(
      <FilterBar
        filters={{ brand_id: 1, source: 'all', sentiment: 'all', topic: 'all', product: 'all', competitor: 'all', virality_level: 'all', viral: false, search: '', sort_by: 'newest' }}
        onChange={vi.fn()}
        onReset={vi.fn()}
        competitors={['Adidas', 'Puma']}
      />
    );

    expect(screen.getByLabelText('Quick filters')).toHaveClass('flex-wrap');
    expect(screen.getByLabelText('Quick filters')).not.toHaveClass('overflow-x-auto');
  });
});

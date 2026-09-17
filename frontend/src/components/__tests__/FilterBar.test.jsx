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
    expect(screen.getByRole('button', { name: /hide filters/i })).toHaveAttribute('aria-expanded', 'true');
  });

});

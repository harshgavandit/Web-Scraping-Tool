import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SavedViewsDropdown from '../SavedViewsDropdown';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    getSavedViews: vi.fn(),
    createSavedView: vi.fn(),
    deleteSavedView: vi.fn(),
  },
}));

describe('SavedViewsDropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders saved views and allows applying a view', async () => {
    api.getSavedViews.mockResolvedValue([
      {
        id: 1,
        name: 'Running Complaints',
        team: 'category',
        filters: { sentiment: 'Negative', topic: 'Product Comfort & Fit' },
      },
    ]);

    const onApplyView = vi.fn();
    render(
      <SavedViewsDropdown
        brandId={1}
        currentFilters={{ source: 'all', sentiment: 'all' }}
        onApplyView={onApplyView}
      />
    );

    const toggleButton = screen.getByRole('button', { name: /saved views/i });
    expect(toggleButton).toBeInTheDocument();

    fireEvent.click(toggleButton);

    await waitFor(() => {
      expect(screen.getByText('Running Complaints')).toBeInTheDocument();
      expect(screen.getByText(/category team/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Running Complaints'));
    expect(onApplyView).toHaveBeenCalledWith({
      sentiment: 'Negative',
      topic: 'Product Comfort & Fit',
    });
  });

  it('allows saving current filters as a new saved view', async () => {
    api.getSavedViews.mockResolvedValue([]);
    api.createSavedView.mockResolvedValue({
      id: 2,
      name: 'Executive Daily',
      team: 'executive',
      filters: { viral: true },
    });

    render(
      <SavedViewsDropdown
        brandId={1}
        currentFilters={{ source: 'all', viral: true, search: 'Pegasus' }}
        onApplyView={() => {}}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /saved views/i }));

    await waitFor(() => {
      expect(screen.getByText(/save current filters as view/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/save current filters as view/i));

    const input = screen.getByPlaceholderText(/view name/i);
    fireEvent.change(input, { target: { value: 'Executive Daily' } });

    const saveButton = screen.getByRole('button', { name: /save view/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(api.createSavedView).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Executive Daily',
          brand_id: 1,
        })
      );
    });
  });
});

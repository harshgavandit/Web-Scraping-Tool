import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import BrandSettingsModal from '../BrandSettingsModal';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    addKeyword: vi.fn(),
    addCompetitor: vi.fn(),
    deleteKeyword: vi.fn(),
    deleteCompetitor: vi.fn(),
  },
}));

const brand = {
  id: 1,
  name: 'Nike',
  competitors: [{ id: 11, brand_id: 1, name: 'Adidas' }],
  keywords: [{ id: 21, brand_id: 1, keyword: 'Pegasus', category: 'product', active: true }],
};

describe('BrandSettingsModal', () => {
  beforeEach(() => vi.clearAllMocks());

  it('adds configuration and removes existing chips through the API', async () => {
    api.addCompetitor.mockResolvedValue({ id: 12, brand_id: 1, name: 'Puma' });
    api.addKeyword.mockResolvedValue({ id: 22, brand_id: 1, keyword: 'Vomero', category: 'product', active: true });
    api.deleteCompetitor.mockResolvedValue(undefined);
    api.deleteKeyword.mockResolvedValue(undefined);
    const onRefresh = vi.fn().mockResolvedValue(undefined);

    render(<BrandSettingsModal brand={brand} onClose={vi.fn()} onRefresh={onRefresh} />);

    fireEvent.change(screen.getByPlaceholderText(/add competitor/i), { target: { value: 'Puma' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Add' })[0]);
    await waitFor(() => expect(api.addCompetitor).toHaveBeenCalledWith(1, { name: 'Puma' }));

    fireEvent.change(screen.getByPlaceholderText(/add keyword or product/i), { target: { value: 'Vomero' } });
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'product' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Add' })[1]);
    await waitFor(() => expect(api.addKeyword).toHaveBeenCalledWith(1, {
      keyword: 'Vomero', category: 'product', active: true,
    }));

    fireEvent.click(screen.getByRole('button', { name: /remove adidas/i }));
    await waitFor(() => expect(api.deleteCompetitor).toHaveBeenCalledWith(1, 11));

    fireEvent.click(screen.getByRole('button', { name: /remove pegasus/i }));
    await waitFor(() => expect(api.deleteKeyword).toHaveBeenCalledWith(1, 21));
    expect(onRefresh).toHaveBeenCalledTimes(4);
    expect(screen.getByRole('status')).toHaveTextContent(/removed/i);
  });
});

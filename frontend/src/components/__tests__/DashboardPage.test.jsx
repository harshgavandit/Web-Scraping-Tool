import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DashboardPage from '../../pages/DashboardPage';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    getBrands: vi.fn(),
    getBrand: vi.fn(),
    getDashboardSummary: vi.fn(),
    getPosts: vi.fn(),
  },
}));

describe('DashboardPage Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('keeps compact, accessible header actions on narrow screens', async () => {
    api.getBrands.mockResolvedValue([{ id: 1, name: 'Nike' }]);
    api.getBrand.mockResolvedValue({ id: 1, name: 'Nike', keywords: [], competitors: [] });
    api.getDashboardSummary.mockResolvedValue({ kpis: {}, executive_summary: null });
    api.getPosts.mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0, pages: 1 });

    render(<DashboardPage />);

    const collectButton = await screen.findByRole('button', { name: /collect chatter/i });
    const configureButton = screen.getByRole('button', { name: /configure brand/i });
    const menuButton = screen.getByRole('button', { name: /open mobile menu/i });

    expect(collectButton.querySelector('span')).toHaveClass('hidden', 'xl:inline');
    expect(configureButton.querySelector('span')).toHaveClass('hidden', 'xl:inline');
    expect(menuButton).toHaveClass('lg:hidden');
    expect(screen.getByText('Understand what customers are saying across the web.')).toHaveClass('hidden', 'sm:block');
    expect(screen.queryByText('Sarah Chen')).not.toBeInTheDocument();
    expect(screen.queryByText('Live Listening')).not.toBeInTheDocument();
  });

  it('displays error alert banner when API call fails', async () => {
    api.getBrands.mockRejectedValueOnce(new Error('Network error'));
    api.getDashboardSummary.mockResolvedValueOnce({ kpis: {}, executive_summary: null });
    api.getPosts.mockResolvedValueOnce({ items: [], page: 1, page_size: 25, total: 0, pages: 1 });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByTestId('api-error-banner')).toBeInTheDocument();
    });

    expect(screen.getByText(/Unable to load the latest conversations/i)).toBeInTheDocument();
    expect(screen.getByText(/Unable to connect to backend server/i)).toBeInTheDocument();
  });

  it('allows user to retry and recovers cleanly when API resolves', async () => {
    api.getBrands
      .mockRejectedValueOnce(new Error('Server unavailable'))
      .mockResolvedValueOnce([{ id: 1, name: 'Nike' }]);
    api.getBrand.mockResolvedValue({ id: 1, name: 'Nike', keywords: [], competitors: [] });
    api.getDashboardSummary.mockResolvedValue({ kpis: {}, executive_summary: null });
    api.getPosts.mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0, pages: 1 });

    render(<DashboardPage />);

    // Wait for error banner
    await waitFor(() => {
      expect(screen.getByTestId('api-error-banner')).toBeInTheDocument();
    });

    // Click Retry
    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);

    // Error banner should disappear after successful fetch
    await waitFor(() => {
      expect(screen.queryByTestId('api-error-banner')).not.toBeInTheDocument();
    });
  });
});

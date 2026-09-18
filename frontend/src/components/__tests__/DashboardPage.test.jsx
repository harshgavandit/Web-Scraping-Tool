import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import DashboardPage from '../../pages/DashboardPage';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    getBrands: vi.fn(),
    getBrand: vi.fn(),
    getDashboardSummary: vi.fn(),
    getTrendingTopics: vi.fn(),
    getPosts: vi.fn(),
    getIntelligenceOverview: vi.fn(),
    getAlerts: vi.fn(),
    getSavedViews: vi.fn(),
  },
}));

describe('DashboardPage Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getTrendingTopics.mockResolvedValue([]);
    api.getIntelligenceOverview.mockResolvedValue({ products: [], risks: [], praises: [], competitors: [] });
    api.getAlerts.mockResolvedValue([]);
    api.getSavedViews.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('applies the selected analysis window to summary, trends, and conversations', async () => {
    vi.spyOn(Date, 'now').mockReturnValue(new Date('2026-09-17T12:00:00.000Z').getTime());
    api.getBrands.mockResolvedValue([{ id: 1, name: 'Nike' }]);
    api.getBrand.mockResolvedValue({ id: 1, name: 'Nike', keywords: [], competitors: [] });
    api.getDashboardSummary.mockResolvedValue({ kpis: {}, executive_summary: null });
    api.getPosts.mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0, pages: 1 });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(api.getDashboardSummary).toHaveBeenCalledWith(1, 30, false);
      expect(api.getTrendingTopics).toHaveBeenCalledWith(1, 30);
      expect(api.getPosts).toHaveBeenCalledWith(expect.objectContaining({
        date_from: '2026-08-18T12:00:00.000Z',
      }));
    });
    expect(screen.getByText('Prior 30 days')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/analysis window/i), { target: { value: '7' } });

    await waitFor(() => {
      expect(api.getDashboardSummary).toHaveBeenLastCalledWith(1, 7, false);
      expect(api.getTrendingTopics).toHaveBeenLastCalledWith(1, 7);
      expect(api.getPosts).toHaveBeenLastCalledWith(expect.objectContaining({
        date_from: '2026-09-10T12:00:00.000Z',
      }));
    });
    expect(screen.getByText('Prior 7 days')).toBeInTheDocument();
  });

  it('keeps compact, accessible header actions on narrow screens', async () => {
    api.getBrands.mockResolvedValue([{ id: 1, name: 'Nike' }]);
    api.getBrand.mockResolvedValue({ id: 1, name: 'Nike', keywords: [], competitors: [] });
    api.getDashboardSummary.mockResolvedValue({ kpis: {}, executive_summary: null });
    api.getPosts.mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0, pages: 1 });

    render(<DashboardPage />);

    const collectButton = await screen.findByRole('button', { name: /collect live intelligence/i });
    const configureButton = screen.getByRole('button', { name: /configure brand/i });
    const menuButton = screen.getByRole('button', { name: /open mobile menu/i });

    expect(collectButton.querySelector('span')).toHaveClass('hidden', 'xl:inline');
    expect(configureButton.querySelector('span')).toHaveClass('hidden', 'xl:inline');
    expect(menuButton).toHaveClass('lg:hidden');
    expect(screen.getByText('Live signals, source evidence, and decision-ready guidance.')).toHaveClass('hidden', 'sm:block');
    expect(screen.queryByText('Sarah Chen')).not.toBeInTheDocument();
    expect(screen.queryByText('Live Listening')).not.toBeInTheDocument();
  });

  it('presents the dashboard as an accessible intelligence command center', async () => {
    api.getBrands.mockResolvedValue([{ id: 1, name: 'Nike' }]);
    api.getBrand.mockResolvedValue({ id: 1, name: 'Nike', keywords: [], competitors: [] });
    api.getDashboardSummary.mockResolvedValue({ kpis: {}, executive_summary: null });
    api.getPosts.mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0, pages: 1 });

    render(<DashboardPage />);

    expect(await screen.findByRole('main', { name: /nike intelligence command center/i })).toBeInTheDocument();
    expect(screen.getByText(/brand intelligence workspace/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /collect live intelligence/i })).toBeInTheDocument();
  });

  it('routes quick filters and sidebar destinations into server-side post queries', async () => {
    Element.prototype.scrollIntoView = vi.fn();
    api.getBrands.mockResolvedValue([{ id: 1, name: 'Nike' }]);
    api.getBrand.mockResolvedValue({
      id: 1,
      name: 'Nike',
      keywords: [{ id: 1, keyword: 'Pegasus', category: 'product', active: true }],
      competitors: [{ id: 1, name: 'Adidas' }],
    });
    api.getDashboardSummary.mockResolvedValue({ kpis: {}, executive_summary: null });
    api.getTrendingTopics.mockResolvedValue([{ topic: 'Pricing & Value', pct_change: 20 }]);
    api.getPosts.mockResolvedValue({ items: [], page: 1, page_size: 25, total: 0, pages: 1 });

    render(<DashboardPage />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Negative' })).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: 'Negative' }));
    await waitFor(() => expect(api.getPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ sentiment: 'Negative' })
    ));

    fireEvent.click(screen.getByRole('button', { name: /viral only/i }));
    await waitFor(() => expect(api.getPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ viral: true, sort_by: 'highest_virality' })
    ));

    fireEvent.click(screen.getAllByRole('button', { name: 'Competitors' })[0]);
    await waitFor(() => expect(api.getPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ competitor: 'any' })
    ));

    fireEvent.click(screen.getByRole('button', { name: 'Topics' }));
    await waitFor(() => expect(api.getPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ topic: 'Pricing & Value' })
    ));

    fireEvent.click(screen.getByRole('button', { name: 'Conversations' }));
    await waitFor(() => expect(api.getPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ viral: undefined, sentiment: undefined, competitor: undefined, topic: undefined })
    ));

    fireEvent.click(screen.getByRole('button', { name: 'Dashboard' }));
    await waitFor(() => expect(api.getPosts).toHaveBeenLastCalledWith(
      expect.objectContaining({ viral: undefined, sentiment: undefined, competitor: undefined, topic: undefined })
    ));
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

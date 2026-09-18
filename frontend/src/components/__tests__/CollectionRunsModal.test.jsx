import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import CollectionRunsModal from '../CollectionRunsModal';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    getCollectionRuns: vi.fn(),
    getDiscoveryHealth: vi.fn(),
    triggerCollection: vi.fn(),
  },
}));

describe('CollectionRunsModal', () => {
  it('offers Google and curated publisher feed sources and presents collection coverage', async () => {
    api.getCollectionRuns.mockResolvedValue([]);
    api.getDiscoveryHealth.mockResolvedValue({
      configured_queries: 17,
      successful_query_runs: 16,
      failed_query_runs: 1,
      discovered_results: 109,
      unique_domains: 42,
      last_successful_discovery: '2026-09-17T12:00:00Z',
    });

    render(<CollectionRunsModal brandId={1} onClose={() => {}} />);

    await waitFor(() => expect(screen.getByText('109')).toBeInTheDocument());
    expect(screen.getByRole('option', { name: 'Google News' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Google Search' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Publisher RSS / Atom' })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: /Reddit/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('option', { name: /Facebook/i })).not.toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('17')).toBeInTheDocument();
  });
});

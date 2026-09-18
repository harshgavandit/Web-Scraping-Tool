import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AuditTrailModal from '../AuditTrailModal';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({ api: { getAuditTrail: vi.fn() } }));

describe('AuditTrailModal', () => {
  beforeEach(() => {
    api.getAuditTrail.mockResolvedValue({
      source_runs: [{ id: 1, provider: 'google_search', query: 'Nike reviews', category: 'customer_feedback', status: 'completed', results_found: 4, results_new: 2 }],
      ai_analyses: [{ id: 2, provider: 'gemini', model: 'gemini-3.8-flash', status: 'completed', title: 'Nike review', source_url: 'https://example.org/nike' }],
    });
  });

  it('shows source and AI provenance', async () => {
    render(<AuditTrailModal isOpen brandId={1} onClose={vi.fn()} />);

    expect(await screen.findByText('Source & AI Audit Trail')).toBeInTheDocument();
    expect(screen.getByText('Nike reviews')).toBeInTheDocument();
    expect(screen.getByText('gemini-3.8-flash')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /open source/i })).toHaveAttribute('href', 'https://example.org/nike');
    await waitFor(() => expect(api.getAuditTrail).toHaveBeenCalledWith(1));
  });
});

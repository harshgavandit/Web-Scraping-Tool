import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AlertsModal from '../AlertsModal';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    getAlerts: vi.fn(),
    updateAlert: vi.fn(),
  },
}));

describe('AlertsModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders open alerts and allows acknowledging an alert', async () => {
    api.getAlerts.mockResolvedValue([
      {
        id: 101,
        severity: 'Critical',
        title: 'Pegasus Sole Separation Spikes',
        message: 'Unusually high concentration of complaints across reviews and Reddit.',
        status: 'open',
        evidence_count: 14,
        created_at: '2026-09-17T12:00:00Z',
      },
    ]);
    api.updateAlert.mockResolvedValue({ id: 101, status: 'acknowledged' });

    const onAlertStatusChanged = vi.fn();
    const onClose = vi.fn();

    render(
      <AlertsModal
        isOpen={true}
        onClose={onClose}
        brandId={1}
        onAlertStatusChanged={onAlertStatusChanged}
      />
    );

    expect(screen.getByText('Reputation Risk Alerts')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('Pegasus Sole Separation Spikes')).toBeInTheDocument();
      expect(screen.getByText('Critical')).toBeInTheDocument();
      expect(screen.getByText(/14 evidence mentions/i)).toBeInTheDocument();
    });

    const ackButton = screen.getByRole('button', { name: /^acknowledge$/i });
    fireEvent.click(ackButton);

    await waitFor(() => {
      expect(api.updateAlert).toHaveBeenCalledWith(101, { status: 'acknowledged' });
      expect(onAlertStatusChanged).toHaveBeenCalled();
    });
  });

  it('does not render when isOpen is false', () => {
    render(<AlertsModal isOpen={false} onClose={() => {}} brandId={1} />);
    expect(screen.queryByText('Reputation Risk Alerts')).not.toBeInTheDocument();
  });
});

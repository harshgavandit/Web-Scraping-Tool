import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Sidebar from '../Sidebar';

describe('Sidebar', () => {
  it('provides an accessible close control for tablet and mobile navigation', () => {
    const onClose = vi.fn();
    render(<Sidebar isMobileOpen onCloseMobile={onClose} onSelectView={vi.fn()} />);
    fireEvent.click(screen.getAllByRole('button', { name: /close navigation/i })[0]);
    expect(onClose).toHaveBeenCalled();
  });
});

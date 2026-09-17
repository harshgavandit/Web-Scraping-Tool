import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ViralityBadge from '../ViralityBadge';

describe('ViralityBadge', () => {
  it('explains viral status using only available engagement evidence', () => {
    render(<ViralityBadge score={91} level="Viral" isViral velocity={220} comments={180} shares={70} showOutOfHundred />);
    const badge = screen.getByTitle(/rapid engagement growth/i);
    expect(badge).toHaveAttribute('title', expect.stringMatching(/high comment activity/i));
    expect(badge.getAttribute('title')).not.toMatch(/cross-platform/i);
  });

  it('uses the complete Medium label', () => {
    render(<ViralityBadge score={52} level="Medium" />);
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });
});

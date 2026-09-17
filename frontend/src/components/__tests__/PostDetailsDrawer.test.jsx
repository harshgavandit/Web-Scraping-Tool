import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PostDetailsDrawer from '../PostDetailsDrawer';

const post = {
  id: 9,
  source: 'reddit',
  title: 'Pegasus pricing discussion',
  content: 'Comfort is excellent, but the latest price feels too high.',
  author: 'u/runner',
  published_at: '2026-05-10T12:00:00Z',
  likes: 450,
  comments: 80,
  shares: 12,
  engagement_count: 542,
  engagement_velocity: 72,
  analysis: {
    sentiment: 'Mixed', sentiment_score: 0.1, topic: 'Pricing', product: 'Pegasus',
    competitor: 'Adidas', summary: 'Customers like comfort but question the price.',
    key_positive: 'Comfort', key_negative: 'Price', virality_score: 87,
    virality_level: 'Viral', is_viral: true,
    recommendation: 'Strengthen value-for-money messaging.',
  },
};

describe('PostDetailsDrawer', () => {
  it('presents evidence, explanation and action in an accessible dialog', () => {
    const onClose = vi.fn();
    render(<PostDetailsDrawer post={post} onClose={onClose} />);

    expect(screen.getByRole('dialog', { name: /conversation intelligence/i })).toBeInTheDocument();
    expect(screen.getByText('Original Post')).toBeInTheDocument();
    expect(screen.getByText('Why')).toBeInTheDocument();
    expect(screen.getByText('Key Positive')).toBeInTheDocument();
    expect(screen.getByText('Key Negative')).toBeInTheDocument();
    expect(screen.getByText('Recommended Action')).toBeInTheDocument();
    expect(screen.getByText(/rapid engagement growth/i)).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });
});

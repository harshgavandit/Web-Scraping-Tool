import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PostDetailsDrawer from '../PostDetailsDrawer';
import { api } from '../../services/api';

vi.mock('../../services/api', () => ({
  api: {
    refreshPostAnalysis: vi.fn(),
    getPostDetail: vi.fn(),
  },
}));

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
    analysis_provider: 'gemini', analysis_status: 'completed', model_used: 'gemini-3.8-flash',
  },
  document: {
    content_status: 'fetched',
    source_type: 'product_review',
    publisher: 'Runner Evidence',
    author: 'Alex Runner',
    domain: 'reviews.example.org',
    language: 'en',
    fetched_at: '2026-05-10T12:05:00Z',
    snapshots: [{
      id: 1,
      content_text: 'Comfort is excellent, but the latest price feels too high.',
      created_at: '2026-05-10T12:05:00Z',
      extracted_data: {
        product_data: { name: 'Nike Pegasus 41', rating_value: 4.2, review_count: 45 },
      },
    }],
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
    expect(screen.getByText('Original Source Evidence')).toBeInTheDocument();
    expect(screen.getByText('Runner Evidence')).toBeInTheDocument();
    expect(screen.getByText('4.2 / 5')).toBeInTheDocument();
    expect(screen.getByText('45 reviews')).toBeInTheDocument();
    expect(screen.getByText(/rapid engagement growth/i)).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('replaces fallback content with a live Gemini analysis when opened', async () => {
    const fallbackPost = {
      ...post,
      analysis: {
        ...post.analysis,
        summary: 'General brand chatter discussing brand discussion with neutral reception.',
        analysis_provider: 'local_heuristic',
        analysis_status: 'fallback',
        model_used: 'vader_heuristic',
      },
    };
    const livePost = {
      ...fallbackPost,
      analysis: {
        ...fallbackPost.analysis,
        summary: 'This Pegasus article focuses on comfort gains while questioning the higher launch price.',
        analysis_provider: 'gemini',
        analysis_status: 'completed',
        model_used: 'gemini-3.8-flash',
      },
    };
    api.refreshPostAnalysis.mockResolvedValue(livePost);
    const onPostUpdated = vi.fn();

    render(<React.StrictMode><PostDetailsDrawer post={fallbackPost} onClose={vi.fn()} onPostUpdated={onPostUpdated} /></React.StrictMode>);

    await waitFor(() => expect(api.refreshPostAnalysis).toHaveBeenCalledWith(9));
    expect(api.refreshPostAnalysis).toHaveBeenCalledTimes(1);
    expect(await screen.findByText(livePost.analysis.summary)).toBeInTheDocument();
    expect(onPostUpdated).toHaveBeenCalledWith(livePost);
    expect(screen.getByText('completed')).toBeInTheDocument();
    expect(screen.queryByText(/general brand chatter/i)).not.toBeInTheDocument();
  });
});

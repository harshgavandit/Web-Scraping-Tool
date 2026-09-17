import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ChatterTable from '../ChatterTable';

const mockPosts = [
  {
    id: 1,
    source: 'reddit',
    published_at: '2026-05-10T12:00:00Z',
    title: 'Nike Pegasus 41 honest review',
    content: 'Nike Pegasus is extremely comfortable for running.',
    author: 'u/Runner1',
    url: 'https://reddit.com/r/running/1',
    likes: 500,
    comments: 40,
    shares: 10,
    engagement_count: 635,
    engagement_velocity: 52.0,
    analysis: {
      sentiment: 'Positive',
      sentiment_score: 0.75,
      topic: 'Running Shoes / Comfort',
      product: 'Pegasus',
      competitor: null,
      summary: 'Users praise Pegasus for running comfort.',
      recommendation: 'Highlight comfort in running ads.',
      virality_score: 45.0,
      virality_level: 'Medium',
      is_viral: false,
    },
  },
  {
    id: 2,
    source: 'twitter',
    published_at: '2026-05-10T14:00:00Z',
    title: 'Nike pricing issue',
    content: 'Prices are way too high for Air Max.',
    author: '@SneakerFan',
    url: 'https://twitter.com/fan/1',
    likes: 8000,
    comments: 1200,
    shares: 400,
    engagement_count: 12400,
    engagement_velocity: 820.0,
    analysis: {
      sentiment: 'Negative',
      sentiment_score: -0.65,
      topic: 'Pricing',
      product: 'Air Max',
      competitor: 'Adidas',
      summary: 'Users complain about Air Max prices.',
      recommendation: 'Emphasize value proposition.',
      virality_score: 89.0,
      virality_level: 'Viral',
      is_viral: true,
    },
  },
];

describe('ChatterTable Component', () => {
  it('renders loading state correctly', () => {
    render(
      <ChatterTable
        posts={[]}
        loading={true}
        pagination={{ page: 1, page_size: 25, total: 0, pages: 1 }}
        onPageChange={vi.fn()}
        onSelectPost={vi.fn()}
      />
    );
    expect(screen.getByLabelText(/loading brand conversations/i)).toBeInTheDocument();
    expect(screen.queryByText(/loading social listening chatter/i)).not.toBeInTheDocument();
  });

  it('renders empty state correctly', () => {
    render(
      <ChatterTable
        posts={[]}
        loading={false}
        pagination={{ page: 1, page_size: 25, total: 0, pages: 1 }}
        onPageChange={vi.fn()}
        onSelectPost={vi.fn()}
      />
    );
    expect(screen.getByText(/no conversations found/i)).toBeInTheDocument();
  });

  it('renders table columns and post data', () => {
    render(
      <ChatterTable
        posts={mockPosts}
        loading={false}
        pagination={{ page: 1, page_size: 25, total: 2, pages: 1 }}
        onPageChange={vi.fn()}
        onSelectPost={vi.fn()}
      />
    );

    // Verify headers
    expect(screen.getByText('Conversation')).toBeInTheDocument();
    expect(screen.getByText('Context')).toBeInTheDocument();
    expect(screen.getByText('Sentiment')).toBeInTheDocument();
    expect(screen.getByText('Impact')).toBeInTheDocument();
    expect(screen.getByText('Intelligence')).toBeInTheDocument();
    expect(screen.queryByText('Brand')).not.toBeInTheDocument();

    // Verify post 1 data
    expect(screen.getByText('Nike Pegasus 41 honest review')).toBeInTheDocument();
    expect(screen.getByText('Users praise Pegasus for running comfort.')).toBeInTheDocument();

    // Verify post 2 viral post
    expect(screen.getByText('Nike pricing issue')).toBeInTheDocument();
    expect(screen.getByText('Viral')).toBeInTheDocument();
  });

  it('triggers onSelectPost when a row is clicked', () => {
    const handleSelect = vi.fn();
    render(
      <ChatterTable
        posts={mockPosts}
        loading={false}
        pagination={{ page: 1, page_size: 25, total: 2, pages: 1 }}
        onPageChange={vi.fn()}
        onSelectPost={handleSelect}
      />
    );

    fireEvent.click(screen.getByText('Nike Pegasus 41 honest review'));
    expect(handleSelect).toHaveBeenCalledWith(mockPosts[0]);
  });

  it('opens a conversation with the keyboard', () => {
    const handleSelect = vi.fn();
    render(
      <ChatterTable
        posts={mockPosts.slice(0, 1)}
        loading={false}
        pagination={{ page: 1, page_size: 25, total: 1, pages: 1 }}
        onPageChange={vi.fn()}
        onSelectPost={handleSelect}
      />
    );

    fireEvent.keyDown(screen.getByRole('row', { name: /nike pegasus 41 honest review/i }), { key: 'Enter' });
    expect(handleSelect).toHaveBeenCalledWith(mockPosts[0]);
  });

  it('renders the selected brand instead of a hardcoded brand', () => {
    render(
      <ChatterTable
        posts={mockPosts.slice(0, 1)}
        brandName="Jordan"
        loading={false}
        pagination={{ page: 1, page_size: 25, total: 1, pages: 1 }}
        onPageChange={vi.fn()}
        onSelectPost={vi.fn()}
      />
    );
    expect(screen.getByText('Jordan')).toBeInTheDocument();
  });

  it('does not render unsafe external post URLs as links', () => {
    const unsafePost = { ...mockPosts[0], url: 'javascript:alert(1)' };
    render(
      <ChatterTable
        posts={[unsafePost]}
        brandName="Nike"
        loading={false}
        pagination={{ page: 1, page_size: 25, total: 1, pages: 1 }}
        onPageChange={vi.fn()}
        onSelectPost={vi.fn()}
      />
    );
    expect(screen.queryByTitle('Open Original Discussion')).not.toBeInTheDocument();
  });
});

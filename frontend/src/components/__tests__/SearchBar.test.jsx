import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SearchBar from '../SearchBar';

describe('SearchBar', () => {
  it('debounces search requests while keeping typing responsive', () => {
    vi.useFakeTimers();
    const onChange = vi.fn();
    render(<SearchBar value="" onChange={onChange} />);

    const input = screen.getByRole('searchbox');
    fireEvent.change(input, { target: { value: 'pegasus' } });
    expect(input).toHaveValue('pegasus');
    expect(onChange).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(349));
    expect(onChange).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(1));
    expect(onChange).toHaveBeenCalledWith('pegasus');
    vi.useRealTimers();
  });
});

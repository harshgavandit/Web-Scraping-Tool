import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});

if (!global.fetch || !global.fetch._isMocked) {
  const originalFetch = global.fetch;
  const mockFetch = async (url, options) => {
    try {
      if (originalFetch) {
        return await originalFetch(url, options);
      }
    } catch (_) {}
    return {
      ok: true,
      status: 200,
      json: async () => ([]),
    };
  };
  mockFetch._isMocked = true;
  global.fetch = mockFetch;
}

const API_BASE = '/api';

export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch (_) {}
    throw new Error(`API Error [${response.status}]: ${errorDetail}`);
  }

  return response.json();
}

export const api = {
  // Health
  getHealth: () => fetchApi('/health'),

  // Brands
  getBrands: () => fetchApi('/brands'),
  createBrand: (data) => fetchApi('/brands', { method: 'POST', body: JSON.stringify(data) }),
  getBrand: (id) => fetchApi(`/brands/${id}`),
  addKeyword: (brandId, data) => fetchApi(`/brands/${brandId}/keywords`, { method: 'POST', body: JSON.stringify(data) }),
  addCompetitor: (brandId, data) => fetchApi(`/brands/${brandId}/competitors`, { method: 'POST', body: JSON.stringify(data) }),

  // Posts
  getPosts: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val);
      }
    });
    return fetchApi(`/posts?${query.toString()}`);
  },
  getPostDetail: (postId) => fetchApi(`/posts/${postId}`),
  getViralPosts: (brandId = 1, limit = 10) => fetchApi(`/posts/viral?brand_id=${brandId}&limit=${limit}`),

  // Dashboard & Trends
  getDashboardSummary: (brandId = 1, days = 30, refresh = false) =>
    fetchApi(`/dashboard/summary?brand_id=${brandId}&days=${days}&refresh=${refresh}`),
  getTrendingTopics: (brandId = 1, days = 7) =>
    fetchApi(`/topics?brand_id=${brandId}&days=${days}`),

  // Pipeline / Collection
  triggerCollection: (payload = { source: 'all', brand_id: 1 }) =>
    fetchApi('/collection/run', { method: 'POST', body: JSON.stringify(payload) }),
  getCollectionRuns: () => fetchApi('/collection/runs'),

  // Analysis
  triggerAnalysis: (brandId = 1, forceAll = false) =>
    fetchApi(`/analysis/run?brand_id=${brandId}&force_all=${forceAll}`, { method: 'POST' }),
};

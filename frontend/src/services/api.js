const API_BASE = '/api';

export async function fetchApi(endpoint, options = {}) {
  let url = `${API_BASE}${endpoint}`;
  if (typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null' && !url.startsWith('http')) {
    url = `${window.location.origin}${url}`;
  }
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

  if (response.status === 204) return null;
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
  deleteKeyword: (brandId, keywordId) => fetchApi(`/brands/${brandId}/keywords/${keywordId}`, { method: 'DELETE' }),
  deleteCompetitor: (brandId, competitorId) => fetchApi(`/brands/${brandId}/competitors/${competitorId}`, { method: 'DELETE' }),

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
  getIntelligenceOverview: (brandId = 1, days = 30) =>
    fetchApi(`/intelligence/overview?brand_id=${brandId}&days=${days}`),
  rebuildIntelligence: (brandId = 1) =>
    fetchApi(`/intelligence/rebuild?brand_id=${brandId}`, { method: 'POST' }),

  // Pipeline / Collection
  triggerCollection: (payload = { source: 'all', brand_id: 1 }) =>
    fetchApi('/collection/run', { method: 'POST', body: JSON.stringify(payload) }),
  getCollectionRuns: () => fetchApi('/collection/runs'),
  getDiscoveryHealth: (brandId = 1) => fetchApi(`/collection/health?brand_id=${brandId}`),

  // Analysis
  triggerAnalysis: (brandId = 1, forceAll = false, limit = 200) =>
    fetchApi(`/analysis/run?brand_id=${brandId}&force_all=${forceAll}&limit=${limit}`, { method: 'POST' }),
  refreshPostAnalysis: (postId) =>
    fetchApi(`/analysis/posts/${postId}/refresh`, { method: 'POST' }),

  // Enterprise Alerts
  getAlerts: (brandId = 1, status = 'open') =>
    fetchApi(`/alerts?brand_id=${brandId}${status ? `&status=${status}` : ''}`),
  updateAlert: (id, data) =>
    fetchApi(`/alerts/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Saved Views
  getSavedViews: (brandId = 1, team = null) =>
    fetchApi(`/saved-views?brand_id=${brandId}${team ? `&team=${team}` : ''}`),
  createSavedView: (data) =>
    fetchApi('/saved-views', { method: 'POST', body: JSON.stringify(data) }),
  deleteSavedView: (id) =>
    fetchApi(`/saved-views/${id}`, { method: 'DELETE' }),

  // Export
  getIntelligenceCsvUrl: (brandId = 1) => `/api/intelligence/export.csv?brand_id=${brandId}`,
  getAuditTrail: (brandId = 1) => fetchApi(`/audit?brand_id=${brandId}`),
};

/**
 * FinCrew Authenticated API Client
 * Centralizes all communication with backend endpoints (/api/*)
 * Enforces Bearer JWT token injection, error handling, and file downloads.
 */

export function getAuthToken() {
  return localStorage.getItem('fincrew_token') || '';
}

export function setAuthSession(token, user) {
  if (token) localStorage.setItem('fincrew_token', token);
  if (user) localStorage.setItem('fincrew_user', JSON.stringify(user));
}

export function clearAuthSession() {
  localStorage.removeItem('fincrew_token');
  localStorage.removeItem('fincrew_user');
}

export async function fetchWithAuth(url, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearAuthSession();
    window.dispatchEvent(new CustomEvent('fincrew-session-expired'));
  }

  return response;
}

export const api = {
  // Auth
  async getMe() {
    const res = await fetchWithAuth('/api/auth/me');
    if (!res.ok) throw new Error('Failed to fetch user profile');
    return res.json();
  },

  async logout() {
    try {
      await fetchWithAuth('/api/auth/logout', { method: 'POST' });
    } finally {
      clearAuthSession();
    }
  },

  // Research Analytics
  async getWorkspaceAnalytics() {
    const res = await fetchWithAuth('/api/research/analytics/summary');
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch analytics summary');
    }
    return res.json();
  },

  // Research Sessions
  async listSessions(limit = 50, offset = 0) {
    const res = await fetchWithAuth(`/api/research/sessions?limit=${limit}&offset=${offset}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch research sessions');
    }
    return res.json();
  },

  async getSession(sessionId) {
    const res = await fetchWithAuth(`/api/research/sessions/${sessionId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch session ${sessionId}`);
    }
    return res.json();
  },

  async getReport(sessionId) {
    const res = await fetchWithAuth(`/api/research/sessions/${sessionId}/report`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch report for session ${sessionId}`);
    }
    return res.json();
  },

  async startAnalysis(ticker, runSync = false) {
    const res = await fetchWithAuth(`/api/research/analyze?run_sync=${runSync}`, {
      method: 'POST',
      body: JSON.stringify({ ticker: ticker.trim().toUpperCase() }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      let msg = 'Failed to initiate research analysis';
      if (typeof err.detail === 'string') msg = err.detail;
      else if (Array.isArray(err.detail)) msg = err.detail.map((e) => e.msg).join(', ');
      throw new Error(msg);
    }
    return res.json();
  },

  async retrySession(sessionId, runSync = false) {
    const res = await fetchWithAuth(`/api/research/sessions/${sessionId}/start?run_sync=${runSync}`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to restart research session');
    }
    return res.json();
  },

  async deleteSession(sessionId) {
    const res = await fetchWithAuth(`/api/research/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to delete session ${sessionId}`);
    }
    return res.json();
  },

  // Comparative Analysis
  async compareStocks(sessionIds) {
    const res = await fetchWithAuth('/api/research/compare', {
      method: 'POST',
      body: JSON.stringify({ session_ids: sessionIds }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Comparative analysis failed');
    }
    return res.json();
  },

  // Report Export File Download
  async downloadReport(sessionId, format = 'pdf', ticker = 'REPORT') {
    const token = getAuthToken();
    const url = `/api/research/sessions/${sessionId}/export?format=${format}`;
    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Export failed for format ${format}`);
    }

    // Determine filename
    let filename = `${ticker}_research_${sessionId}.${format === 'markdown' ? 'md' : format}`;
    const disposition = res.headers.get('content-disposition');
    if (disposition && disposition.includes('filename=')) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }

    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    return true;
  },
};

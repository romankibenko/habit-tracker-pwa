/**
 * Тонкая обёртка над fetch — авто-добавляет JWT, парсит JSON, кидает ошибки.
 */

const TOKEN_KEY = 'habit_tracker_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // 204 No Content
  if (response.status === 204) return null;

  let payload = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    payload = await response.json();
  }

  if (!response.ok) {
    const message = payload?.detail || `Ошибка ${response.status}`;
    throw new ApiError(message, response.status, payload);
  }

  return payload;
}

export const api = {
  // Auth
  register: (email, password) =>
    request('/api/auth/register', { method: 'POST', body: { email, password }, auth: false }),
  login: (email, password) =>
    request('/api/auth/login', { method: 'POST', body: { email, password }, auth: false }),

  // Habits
  listHabits: () => request('/api/habits'),
  createHabit: (data) => request('/api/habits', { method: 'POST', body: data }),
  updateHabit: (id, data) => request(`/api/habits/${id}`, { method: 'PATCH', body: data }),
  deleteHabit: (id) => request(`/api/habits/${id}`, { method: 'DELETE' }),

  // Checkins
  createCheckin: (data) => request('/api/checkins', { method: 'POST', body: data }),
  deleteCheckin: (id) => request(`/api/checkins/${id}`, { method: 'DELETE' }),
  listCheckins: (habitId, days = 90) =>
    request(`/api/habits/${habitId}/checkins?days=${days}`),
  habitStats: (habitId) => request(`/api/habits/${habitId}/stats`),

  // Push
  vapidPublicKey: () => request('/api/push/public-key'),
  pushSubscribe: (subscription) =>
    request('/api/push/subscribe', { method: 'POST', body: subscription }),
  pushTest: (body) => request('/api/push/test', { method: 'POST', body }),
};

export { ApiError };

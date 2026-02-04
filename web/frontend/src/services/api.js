export const API_BASE = '/api';

export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);

        // Handle 401 Unauthorized globally if needed, but Context will handle check-auth
        if (response.status === 401) {
            throw new ApiError('Unauthorized', 401);
        }

        const data = await response.json();

        if (!response.ok) {
            throw new ApiError(data.error || 'API Error', response.status);
        }

        return data;
    } catch (error) {
        throw error;
    }
}

export const api = {
    get: (endpoint) => request(endpoint, { method: 'GET' }),
    post: (endpoint, body) => request(endpoint, { method: 'POST', body: JSON.stringify(body) }),

    // Specific methods
    checkAuth: () => request('/check-auth', { method: 'GET' }),
    login: (password) => request('/login', { method: 'POST', body: JSON.stringify({ password }) }),
    logout: () => request('/logout', { method: 'POST' }),
    setup: (password) => request('/setup', { method: 'POST', body: JSON.stringify({ password }) }),

    getStatus: () => request('/status', { method: 'GET' }),
    getSystemStats: () => request('/system', { method: 'GET' }),
    getConfig: () => request('/config', { method: 'GET' }),
    saveConfig: (config) => request('/config', { method: 'POST', body: JSON.stringify(config) }),
};

/**
 * API service — centralised HTTP calls to the backend.
 * 
 * For mobile APK: set VITE_API_URL in .env to your server URL
 * e.g. VITE_API_URL=https://yourserver.com
 */

// Server base URL — configurable for mobile vs web
const SERVER_URL = import.meta.env.VITE_API_URL || '';
const API_BASE = `${SERVER_URL}/api`;

// Export for WebSocket connection
export const getServerUrl = () => SERVER_URL || window.location.origin;

/**
 * Get the stored JWT token.
 */
export function getToken() {
    return localStorage.getItem('sf_token');
}

/**
 * Store the JWT token.
 */
export function setToken(token) {
    localStorage.setItem('sf_token', token);
}

/**
 * Remove the token (logout).
 */
export function clearToken() {
    localStorage.removeItem('sf_token');
}

/**
 * Generic fetch wrapper with auth headers.
 */
async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true', // Bypass ngrok free tier warning page
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
    };

    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const error = new Error(body.detail || `HTTP ${res.status}`);
        error.status = res.status;
        throw error;
    }

    return res.json();
}

// ---- Auth ----
export async function register(data) {
    return apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function login(username, password) {
    const data = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
    });
    setToken(data.access_token);
    return data;
}

export async function getMe() {
    return apiFetch('/auth/me');
}

// ---- Rooms ----
export async function createRoom(name, maxParticipants = 10) {
    return apiFetch('/rooms/', {
        method: 'POST',
        body: JSON.stringify({ name, max_participants: maxParticipants }),
    });
}

export async function listRooms() {
    return apiFetch('/rooms/');
}

export async function joinRoom(roomCode, languageMode = 'hi_to_en') {
    return apiFetch('/rooms/join', {
        method: 'POST',
        body: JSON.stringify({ room_code: roomCode, language_mode: languageMode }),
    });
}

export async function getRoomDetail(roomCode) {
    return apiFetch(`/rooms/${roomCode}`);
}

export async function leaveRoom(roomCode) {
    return apiFetch(`/rooms/${roomCode}/leave`, { method: 'POST' });
}

export async function endRoom(roomCode) {
    return apiFetch(`/rooms/${roomCode}/end`, { method: 'POST' });
}

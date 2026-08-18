const API_BASE = '/api/v1';

export class ApiClient {
  static getToken() {
    return localStorage.getItem('xyz_auth_token');
  }

  static setToken(token) {
    localStorage.setItem('xyz_auth_token', token);
  }

  static clearToken() {
    localStorage.removeItem('xyz_auth_token');
  }

  static getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
  }

  static async login(email, password = 'School@123') {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  static async register(payload) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  static async sendOTP(email, name = 'User', purpose = 'registration') {
    const res = await fetch(`${API_BASE}/auth/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, name, purpose })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to send OTP');
    }
    return res.json();
  }

  static async verifyOTP(email, otp_code, purpose = 'registration') {
    const res = await fetch(`${API_BASE}/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp_code, purpose })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Invalid or expired OTP');
    }
    return res.json();
  }

  static async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch profile');
    return res.json();
  }

  static async sendMessage(message, conversationId = null, languagePref = null) {
    const res = await fetch(`${API_BASE}/chat/message`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ message, conversation_id: conversationId, language_pref: languagePref })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to send message');
    }
    return res.json();
  }

  static async sendVoiceTurn(speechText, confidenceScore = 0.95, conversationId = null, languagePref = null) {
    const res = await fetch(`${API_BASE}/voice/turn`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ speech_text: speechText, confidence_score: confidenceScore, conversation_id: conversationId, language_pref: languagePref })
    });
    if (!res.ok) throw new Error('Voice turn failed');
    return res.json();
  }

  static async getDashboard() {
    const res = await fetch(`${API_BASE}/portal/dashboard`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Dashboard fetch failed');
    return res.json();
  }

  static async getLanguages() {
    const res = await fetch(`${API_BASE}/portal/languages`);
    if (!res.ok) throw new Error('Failed to fetch languages');
    return res.json();
  }

  static async confirmEscalation(ticketId, notes = '') {
    const res = await fetch(`${API_BASE}/escalations/${ticketId}/confirm`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ notes })
    });
    if (!res.ok) throw new Error('Failed to confirm escalation');
    return res.json();
  }

  static async getAuditLogs(limit = 25) {
    const res = await fetch(`${API_BASE}/audit/logs?limit=${limit}`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    return res.json();
  }

  static async approveTeacher(userId) {
    const res = await fetch(`${API_BASE}/portal/admin/teachers/${userId}/approve`, {
      method: 'POST',
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error('Failed to approve teacher');
    return res.json();
  }
}

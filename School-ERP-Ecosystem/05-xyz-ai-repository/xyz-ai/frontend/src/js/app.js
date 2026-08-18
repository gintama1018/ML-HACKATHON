import { ApiClient } from './api.js';
import { AvatarRenderer } from './avatar.js';
import { VoiceController } from './voice.js';
import { DashboardRenderer } from './dashboards.js';

// Role accent palette (matches DESIGN.MD)
const ROLE_ACCENTS = {
  student:   { accent: '#FF9F43', light: 'rgba(255,159,67,0.10)' },
  parent:    { accent: '#58B19F', light: 'rgba(88,177,159,0.10)' },
  teacher:   { accent: '#54A0FF', light: 'rgba(84,160,255,0.10)' },
  principal: { accent: '#2C3E50', light: 'rgba(44,62,80,0.10)' }
};

class SchoolApp {
  constructor() {
    this.currentUser = null;
    this.currentConversationId = null;
    this.currentLanguage = 'en';
    this.avatar = null;
    this.voice = null;
    this.miniChartInstances = {};  // track Chart.js instances in bubbles

    this.init();
  }

  async init() {
    this.avatar = new AvatarRenderer('avatarCanvas');
    this.voice = new VoiceController(this.avatar);

    this.bindEvents();
    await this.loadLanguages();

    // Try restore existing session
    try {
      if (ApiClient.getToken()) {
        const userData = await ApiClient.getMe();
        this.currentUser = userData;
        this.showApp();
        this.onUserLoggedIn();
      } else {
        this.showAuth();
      }
    } catch (e) {
      ApiClient.clearToken();
      this.showAuth();
    }
  }

  // ---------------------------------------------------------------------------
  // SCREEN MANAGEMENT
  // ---------------------------------------------------------------------------
  showAuth() {
    document.getElementById('authScreen').classList.add('active');
    document.getElementById('appContent').classList.remove('active');
  }

  showApp() {
    document.getElementById('authScreen').classList.remove('active');
    document.getElementById('appContent').classList.add('active');
  }

  // ---------------------------------------------------------------------------
  // AUTH EVENTS (Login / Register)
  // ---------------------------------------------------------------------------
  bindEvents() {
    // LOGIN FORM
    document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value;
      await this.handleLogin(email, password);
    });

    // REGISTER FORM
    document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleRegister();
    });

    // Role-conditional fields
    document.getElementById('regRole')?.addEventListener('change', (e) => {
      const role = e.target.value;
      const studentFields = document.getElementById('regStudentFields');
      const parentFields = document.getElementById('regParentFields');

      studentFields?.classList.toggle('visible', role === 'student');
      studentFields?.classList.toggle('hidden', role !== 'student');
      parentFields?.classList.toggle('visible', role === 'parent');
      parentFields?.classList.toggle('hidden', role !== 'parent');
    });

    // Show register form
    document.getElementById('showRegister')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.switchAuthMode('register');
    });

    // Show login form
    document.getElementById('showLogin')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.switchAuthMode('login');
    });

    // Demo account quick-select (both auth screen + role modal)
    document.querySelectorAll('.role-select-card[data-email]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const email = btn.getAttribute('data-email');
        const password = btn.getAttribute('data-password') || 'School@123';
        await this.handleLogin(email, password);
      });
    });

    // Role Modal
    document.getElementById('btnSwitchRole')?.addEventListener('click', () => this.openRoleModal());
    document.getElementById('btnCloseRoleModal')?.addEventListener('click', () => this.closeRoleModal());
    document.getElementById('roleModal')?.addEventListener('click', (e) => {
      if (e.target === document.getElementById('roleModal')) this.closeRoleModal();
    });

    // Logout
    document.getElementById('btnLogout')?.addEventListener('click', () => {
      ApiClient.clearToken();
      this.currentUser = null;
      this.currentConversationId = null;
      this.showAuth();
      this.switchAuthMode('login');
    });

    // CHAT form
    const chatInput = document.getElementById('chatInput');
    document.getElementById('chatForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;
      chatInput.value = '';
      chatInput.style.height = 'auto';
      await this.handleUserMessage(text);
    });

    // Auto-resize textarea
    chatInput?.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });

    // Mic
    const micBtn = document.getElementById('btnVoiceRecord');
    micBtn?.addEventListener('click', () => {
      if (this.voice.isRecording) {
        this.voice.stopListening();
        micBtn.classList.remove('recording');
      } else {
        micBtn.classList.add('recording');
        this.voice.startListening(
          async (transcript, conf) => {
            micBtn.classList.remove('recording');
            await this.handleVoiceMessage(transcript, conf);
          },
          (err) => {
            micBtn.classList.remove('recording');
            console.warn('Voice error:', err);
          },
          this.currentLanguage
        );
      }
    });

    // Language selector
    document.getElementById('langSelect')?.addEventListener('change', (e) => {
      this.currentLanguage = e.target.value;
    });

    // Quick suggestion chips
    document.querySelectorAll('.suggestion-chip[data-msg]').forEach(chip => {
      chip.addEventListener('click', () => {
        this.handleUserMessage(chip.getAttribute('data-msg'));
      });
    });

    // Staff console
    document.getElementById('btnOpenStaffConsole')?.addEventListener('click', () => this.openStaffConsole());
    document.getElementById('btnCloseStaffModal')?.addEventListener('click', () => this.closeStaffConsole());
    document.getElementById('staffConsoleModal')?.addEventListener('click', (e) => {
      if (e.target === document.getElementById('staffConsoleModal')) this.closeStaffConsole();
    });

    // Console tabs
    document.querySelectorAll('.console-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.console-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.console-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        const panel = document.getElementById(`panel${tab.dataset.tab.charAt(0).toUpperCase() + tab.dataset.tab.slice(1)}`);
        panel?.classList.add('active');
      });
    });
  }

  // ---------------------------------------------------------------------------
  // AUTH HELPERS
  // ---------------------------------------------------------------------------
  switchAuthMode(mode) {
    const isLogin = mode === 'login';
    document.getElementById('loginForm').classList.toggle('hidden', !isLogin);
    document.getElementById('registerForm').classList.toggle('hidden', isLogin);
    document.getElementById('loginSwitchLink').classList.toggle('hidden', !isLogin);
    document.getElementById('registerSwitchLink').classList.toggle('hidden', isLogin);
    document.getElementById('authTitle').textContent = isLogin ? 'Welcome Back' : 'Create Account';
    document.getElementById('authSubtitle').textContent = isLogin ? 'Sign in to your school account' : 'Register as a student, parent, or teacher';
    this.clearAuthError();
  }

  showAuthError(msg) {
    const el = document.getElementById('authError');
    el.textContent = msg;
    el.classList.add('visible');
  }

  clearAuthError() {
    const el = document.getElementById('authError');
    el.textContent = '';
    el.classList.remove('visible');
  }

  async handleLogin(email, password) {
    this.clearAuthError();
    const btn = document.getElementById('loginSubmitBtn');
    if (btn) { btn.textContent = 'Signing in…'; btn.disabled = true; }
    try {
      const data = await ApiClient.login(email, password);
      this.currentUser = data.user;
      this.currentConversationId = null;
      this.showApp();
      this.onUserLoggedIn();
      this.closeRoleModal();
    } catch (err) {
      this.showAuthError(err.message || 'Login failed. Check your credentials.');
    } finally {
      if (btn) { btn.textContent = 'Sign In'; btn.disabled = false; }
    }
  }

  async handleRegister() {
    this.clearAuthError();
    const btn = document.getElementById('registerSubmitBtn');
    if (btn) { btn.textContent = 'Creating…'; btn.disabled = true; }
    try {
      const role = document.getElementById('regRole').value;
      const payload = {
        name: document.getElementById('regName').value.trim(),
        email: document.getElementById('regEmail').value.trim(),
        password: document.getElementById('regPassword').value,
        role,
        language_pref: this.currentLanguage || 'en'
      };
      if (role === 'student') {
        payload.class_name = document.getElementById('regClass').value;
        payload.section = document.getElementById('regSection').value;
        payload.roll_no = document.getElementById('regRoll').value.trim();
      } else if (role === 'parent') {
        payload.child_email = document.getElementById('regChildEmail').value.trim();
      }
      const data = await ApiClient.register(payload);
      this.currentUser = data.user;
      this.currentConversationId = null;
      this.showApp();
      this.onUserLoggedIn();
    } catch (err) {
      this.showAuthError(err.message || 'Registration failed. Please try again.');
    } finally {
      if (btn) { btn.textContent = 'Create Account'; btn.disabled = false; }
    }
  }

  // ---------------------------------------------------------------------------
  // LANGUAGES
  // ---------------------------------------------------------------------------
  async loadLanguages() {
    try {
      const langs = await ApiClient.getLanguages();
      const select = document.getElementById('langSelect');
      if (select && langs) {
        select.innerHTML = langs.map(l =>
          `<option value="${l.code}">${l.native_name} (${l.name})${l.deep_tested ? ' ★' : ''}</option>`
        ).join('');
      }
    } catch (e) { console.warn('Language load failed:', e); }
  }

  // ---------------------------------------------------------------------------
  // POST-LOGIN SETUP
  // ---------------------------------------------------------------------------
  applyRoleTheme(role) {
    const p = ROLE_ACCENTS[role] || ROLE_ACCENTS.teacher;
    document.documentElement.style.setProperty('--current-accent', p.accent);
    document.documentElement.style.setProperty('--current-light', p.light);
  }

  onUserLoggedIn() {
    if (!this.currentUser) return;
    const { name, role, is_verified } = this.currentUser;

    // Theme
    this.applyRoleTheme(role);

    // Header
    const nameEl = document.getElementById('headerUserName');
    const pillEl = document.getElementById('headerRolePill');
    const miniEl = document.getElementById('headerAvatarMini');
    const logoEl = document.getElementById('headerLogo');
    if (nameEl) nameEl.textContent = name;
    if (pillEl) pillEl.textContent = role;
    if (miniEl) miniEl.textContent = name.charAt(0).toUpperCase();
    if (logoEl) logoEl.textContent = 'XYZ';

    // Chat header strip
    const strip = document.getElementById('chatHeaderStrip');
    const accent = ROLE_ACCENTS[role]?.accent || '#54A0FF';
    if (strip) strip.style.background = accent;

    // Avatar persona
    if (this.avatar) this.avatar.setPersona(role);

    // Staff console button visibility
    const staffCard = document.getElementById('staffConsoleCard');
    const isStaff = role === 'teacher' || role === 'principal';
    if (staffCard) staffCard.style.display = isStaff ? 'block' : 'none';

    // Pending approval banner (unverified teacher)
    const banner = document.getElementById('pendingApprovalBanner');
    if (banner) {
      const showBanner = role === 'teacher' && is_verified === false;
      banner.classList.toggle('hidden', !showBanner);
    }

    // Reset chat
    const msgContainer = document.getElementById('chatMessages');
    if (msgContainer) {
      msgContainer.innerHTML = '';
      this.appendAiBubble({
        response: `Hello **${name}**! I'm your XYZ AI School Assistant. How may I help you today?`
      });
    }

    // Update quick chips based on role
    this.updateQuickChips(role);

    // Refresh dashboard
    this.refreshDashboard();
  }

  updateQuickChips(role) {
    const wrap = document.getElementById('quickChips');
    if (!wrap) return;
    const chips = {
      student:   [['📊 My Attendance', "What is my attendance percentage?"], ['📞 Talk to Teacher', "I want to connect with my teacher."], ['📖 Study Tips', "Help me with homework study tips."], ['📈 Full Report', "Generate attendance report."]],
      parent:    [['📊 Child\'s Attendance', "What is my child's attendance?"], ['📞 Contact Teacher', "I want to connect with my child's teacher."], ['📈 Monthly Report', "Generate monthly attendance report."], ['🔔 Alerts', "Any attendance alerts for my child?"]],
      teacher:   [['✅ Mark Present', "Mark all students present for today."], ['📊 Class Analytics', "Show class attendance analytics."], ['📝 Roster', "Show today's class roster."], ['⚠️ Absentees', "Who was absent this week?"]],
      principal: [['🏫 School Summary', "Show school-wide attendance analytics."], ['📊 Class Breakdown', "Show class-wise attendance breakdown."], ['⚠️ Low Attendance', "Which classes have low attendance?"], ['📋 Escalations', "Show recent escalation tickets."]]
    };
    const roleChips = chips[role] || chips.student;
    wrap.innerHTML = roleChips.map(([label, msg]) =>
      `<button class="suggestion-chip" data-msg="${msg}">${label}</button>`
    ).join('');
    wrap.querySelectorAll('.suggestion-chip[data-msg]').forEach(chip => {
      chip.addEventListener('click', () => this.handleUserMessage(chip.getAttribute('data-msg')));
    });
  }

  async refreshDashboard() {
    try {
      const data = await ApiClient.getDashboard();
      DashboardRenderer.render(data, 'dashboardContainer', (action, payload) => {
        if (action === 'chat_prompt') this.handleUserMessage(payload);
        if (action === 'approve_teacher') this.approveTeacher(payload);
      });
    } catch (e) { console.warn('Dashboard refresh error:', e); }
  }

  async approveTeacher(userId) {
    try {
      await ApiClient.approveTeacher(userId);
      await this.refreshDashboard();
    } catch (e) { console.warn('Approve teacher error:', e); }
  }

  // ---------------------------------------------------------------------------
  // CHAT
  // ---------------------------------------------------------------------------
  async handleUserMessage(text) {
    this.appendUserBubble(text);
    this.avatar?.setState('thinking');
    const typingId = this.appendTypingIndicator();

    try {
      const result = await ApiClient.sendMessage(text, this.currentConversationId, this.currentLanguage);
      this.currentConversationId = result.conversation_id;
      this.removeTypingIndicator(typingId);
      this.appendAiBubble(result);

      this.voice?.speak(result.response, [], 2.5, this.currentLanguage, () => this.avatar?.setState('idle'));

      if (result.tool_executions?.length > 0) await this.refreshDashboard();
    } catch (e) {
      this.removeTypingIndicator(typingId);
      this.appendAiBubble({ response: e.message, security_flag: e.message.includes('Security') || e.message.includes('prohibited') });
      this.avatar?.setState('idle');
    }
  }

  async handleVoiceMessage(speechText, confidenceScore) {
    this.appendUserBubble(`🎤 ${speechText}`);
    this.avatar?.setState('thinking');
    const typingId = this.appendTypingIndicator();

    try {
      const result = await ApiClient.sendVoiceTurn(speechText, confidenceScore, this.currentConversationId, this.currentLanguage);
      this.currentConversationId = result.conversation_id;
      this.removeTypingIndicator(typingId);
      this.appendAiBubble(result);

      if (result.tts) {
        this.voice?.speak(result.response, result.tts.visemes || [], result.tts.duration_seconds || 2.5, result.language || this.currentLanguage, () => this.avatar?.setState('idle'));
      } else {
        this.avatar?.setState('idle');
      }

      if (result.tool_executions?.length > 0) await this.refreshDashboard();
    } catch (e) {
      this.removeTypingIndicator(typingId);
      this.appendAiBubble({ response: `Voice note: ${e.message}`, security_flag: true });
      this.avatar?.setState('idle');
    }
  }

  // ---------------------------------------------------------------------------
  // BUBBLE RENDERING
  // ---------------------------------------------------------------------------
  appendUserBubble(text) {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    const bubble = document.createElement('div');
    bubble.className = 'bubble bubble-user';
    bubble.textContent = text;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }

  appendTypingIndicator() {
    const container = document.getElementById('chatMessages');
    if (!container) return null;
    const id = 'typing-' + Date.now();
    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = 'typing-bubble';
    bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return id;
  }

  removeTypingIndicator(id) {
    if (id) document.getElementById(id)?.remove();
  }

  appendAiBubble(data) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const bubble = document.createElement('div');
    bubble.className = `bubble ${data.security_flag ? 'bubble-security' : 'bubble-ai'}`;

    // Tool execution badges
    let toolBadgesHtml = '';
    if (data.tool_executions?.length > 0) {
      toolBadgesHtml = data.tool_executions.map(t =>
        `<div class="tool-badge">✓ ${t.tool.replace(/_/g,' ')} <span style="opacity:0.7">(${t.result_status})</span></div>`
      ).join('');
    }

    // Format response text (markdown-lite)
    const formattedText = (data.response || '')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');

    bubble.innerHTML = `${toolBadgesHtml}<div>${formattedText}</div>`;

    // --- Rich tool result cards ---
    if (data.tool_executions?.length > 0) {
      for (const toolExec of data.tool_executions) {
        // Attendance result → donut card
        if (toolExec.tool === 'get_attendance' && toolExec.output) {
          const card = this.buildAttendanceCard(toolExec.output);
          if (card) bubble.appendChild(card);
        }

        // Escalation created → two-option card
        if (toolExec.tool === 'create_escalation' && toolExec.output) {
          const optionCard = this.buildEscalationOptionsCard();
          bubble.appendChild(optionCard);
        }
      }
    }

    // Escalation confirmation buttons (check response text)
    if (data.response?.includes('confirm and dispatch this request')) {
      const confirmDiv = document.createElement('div');
      confirmDiv.className = 'esc-confirm-card';
      confirmDiv.innerHTML = `
        <button class="btn btn-primary btn-sm" id="btnConfirmEsc">✓ Confirm &amp; Send</button>
        <button class="btn btn-ghost btn-sm" id="btnCancelEsc">✕ Cancel</button>
      `;
      bubble.appendChild(confirmDiv);
      confirmDiv.querySelector('#btnConfirmEsc')?.addEventListener('click', () => {
        this.handleUserMessage('Yes, please confirm and submit this request.');
      });
      confirmDiv.querySelector('#btnCancelEsc')?.addEventListener('click', () => {
        this.handleUserMessage('No, cancel this request.');
      });
    }

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }

  buildAttendanceCard(output) {
    const summary = output.summary || output;
    const pct = summary.attendance_percentage ?? 0;
    const present = summary.present_days ?? 0;
    const absent = summary.absent_days ?? 0;
    const late = summary.late_days ?? 0;
    const total = summary.total_school_days ?? (present + absent + late);

    const card = document.createElement('div');
    card.className = 'att-result-card';

    const canvasId = 'att-donut-' + Date.now();
    card.innerHTML = `
      <div class="att-donut-wrap">
        <canvas id="${canvasId}" class="att-donut-canvas" width="80" height="80"></canvas>
        <div>
          <div class="att-pct">${pct.toFixed(1)}%</div>
          <div class="att-pct-label">Attendance</div>
        </div>
      </div>
      <div class="att-stats">
        <div class="att-stat"><span class="att-stat-val" style="color:var(--success)">${present}</span><span class="att-stat-key">Present</span></div>
        <div class="att-stat"><span class="att-stat-val" style="color:var(--error)">${absent}</span><span class="att-stat-key">Absent</span></div>
        <div class="att-stat"><span class="att-stat-val" style="color:var(--warning)">${late}</span><span class="att-stat-key">Late</span></div>
      </div>
    `;

    // Draw donut after DOM insertion
    requestAnimationFrame(() => {
      const canvas = document.getElementById(canvasId);
      if (canvas && window.Chart) {
        const accent = getComputedStyle(document.documentElement).getPropertyValue('--current-accent').trim() || '#54A0FF';
        new window.Chart(canvas, {
          type: 'doughnut',
          data: {
            datasets: [{
              data: [present, absent, late],
              backgroundColor: [accent, '#ffdad6', '#ffdcc2'],
              borderWidth: 0,
              hoverOffset: 4
            }]
          },
          options: {
            cutout: '72%',
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            animation: { duration: 600, easing: 'easeInOutQuart' }
          }
        });
      }
    });

    return card;
  }

  buildEscalationOptionsCard() {
    const wrap = document.createElement('div');
    wrap.className = 'escalation-options';
    wrap.innerHTML = `
      <button class="esc-option-card" data-choice="teacher">
        <span class="esc-option-icon">👩‍🏫</span>
        <div class="esc-option-text">
          <strong>Talk to Teacher</strong>
          <span>Connect directly with your class teacher</span>
        </div>
      </button>
      <button class="esc-option-card" data-choice="management">
        <span class="esc-option-icon">🏫</span>
        <div class="esc-option-text">
          <strong>Contact School Management</strong>
          <span>Escalate to the principal's office</span>
        </div>
      </button>
    `;
    wrap.querySelectorAll('.esc-option-card').forEach(btn => {
      btn.addEventListener('click', () => {
        const choice = btn.getAttribute('data-choice');
        this.handleUserMessage(
          choice === 'teacher'
            ? "Yes, please connect me with my teacher."
            : "Yes, please contact school management."
        );
        // Disable options after pick
        wrap.querySelectorAll('.esc-option-card').forEach(b => b.disabled = true);
      });
    });
    return wrap;
  }

  // ---------------------------------------------------------------------------
  // MODALS
  // ---------------------------------------------------------------------------
  openRoleModal() {
    document.getElementById('roleModal')?.classList.add('active');
  }

  closeRoleModal() {
    document.getElementById('roleModal')?.classList.remove('active');
  }

  async openStaffConsole() {
    const modal = document.getElementById('staffConsoleModal');
    if (!modal) return;
    modal.classList.add('active');

    // Load audit logs
    const tableBody = document.getElementById('auditLogTableBody');
    if (tableBody) {
      tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--on-surface-muted);">Loading…</td></tr>';
      try {
        const logs = await ApiClient.getAuditLogs(25);
        tableBody.innerHTML = logs.map(l => `
          <tr>
            <td><small>${l.timestamp.split('T')[1]?.slice(0, 8) || ''}</small></td>
            <td><strong>${l.user_name || '–'}</strong></td>
            <td><code style="font-size:0.72rem;background:var(--surface-low);padding:2px 6px;border-radius:4px;">${l.action}</code></td>
            <td><span class="chip ${l.result === 'allowed' ? 'chip-present' : 'chip-absent'}">${l.result}</span></td>
          </tr>
        `).join('');
      } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="4" style="color:var(--error);">Error: ${e.message}</td></tr>`;
      }
    }

    // Load teacher approvals
    await this.loadTeacherApprovals();

    // Bind attack demo buttons
    document.querySelectorAll('.btn-run-attack').forEach(btn => {
      btn.onclick = () => {
        this.closeStaffConsole();
        this.handleUserMessage(btn.getAttribute('data-attack'));
      };
    });
  }

  async loadTeacherApprovals() {
    const container = document.getElementById('teacherApprovalsList');
    if (!container || this.currentUser?.role !== 'principal') return;
    try {
      const data = await ApiClient.getDashboard();
      const pending = data.pending_teacher_approvals || [];
      if (pending.length === 0) {
        container.innerHTML = '<p style="font-size:0.82rem;color:var(--on-surface-muted);">No pending teacher approvals.</p>';
        return;
      }
      container.innerHTML = pending.map(t => `
        <div class="approval-card" id="approval-${t.user_id}">
          <div class="approval-info">
            <div class="approval-name">📚 ${t.name}</div>
            <div class="approval-email">${t.email}</div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="window.app.approveTeacher('${t.user_id}').then(()=>{ document.getElementById('approval-${t.user_id}').remove(); })">
            Approve
          </button>
        </div>
      `).join('');
    } catch (e) {
      container.innerHTML = '<p style="color:var(--error);font-size:0.82rem;">Could not load approvals.</p>';
    }
  }

  closeStaffConsole() {
    document.getElementById('staffConsoleModal')?.classList.remove('active');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new SchoolApp();
});

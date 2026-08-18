import { ApiClient } from './api.js';
import { AvatarRenderer } from './avatar.js';
import { VoiceController } from './voice.js';
import { DashboardRenderer } from './dashboards.js';

// Role accent palette (strictly from DESIGN.MD)
const ROLE_ACCENTS = {
  student:   { accent: '#FF9F43', light: 'rgba(255, 159, 67, 0.12)' },
  parent:    { accent: '#58B19F', light: 'rgba(88, 177, 159, 0.12)' },
  teacher:   { accent: '#54A0FF', light: 'rgba(84, 160, 255, 0.12)' },
  principal: { accent: '#2C3E50', light: 'rgba(44, 62, 80, 0.10)' }
};

class SchoolApp {
  constructor() {
    this.currentUser = null;
    this.currentConversationId = null;
    this.currentLanguage = 'en';
    this.avatar = null;
    this.voice = null;

    this.init();
  }

  async init() {
    this.avatar = new AvatarRenderer('avatarCanvas');
    this.voice = new VoiceController(this.avatar);

    this.bindEvents();
    await this.loadLanguages();

    // Check for stored session
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
  // SCREEN VISIBILITY
  // ---------------------------------------------------------------------------
  showAuth() {
    document.getElementById('authScreen').classList.add('active');
    const app = document.getElementById('appContent');
    app.classList.add('hidden');
    app.style.display = 'none';
  }

  showApp() {
    document.getElementById('authScreen').classList.remove('active');
    const app = document.getElementById('appContent');
    app.classList.remove('hidden');
    app.style.display = 'flex';
  }

  // ---------------------------------------------------------------------------
  // EVENT WIRING
  // ---------------------------------------------------------------------------
  bindEvents() {
    // LOGIN
    document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value;
      await this.handleLogin(email, password);
    });

    // REGISTER
    document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleRegister();
    });

    // Dynamic Role-conditional fields in registration
    document.getElementById('regRole')?.addEventListener('change', (e) => {
      const role = e.target.value;
      const studentFields = document.getElementById('regStudentFields');
      const parentFields = document.getElementById('regParentFields');

      if (studentFields) studentFields.classList.toggle('hidden', role !== 'student');
      if (parentFields) parentFields.classList.toggle('hidden', role !== 'parent');
    });

    // Switch between Login and Register views
    document.getElementById('showRegister')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.switchAuthMode('register');
    });

    document.getElementById('showLogin')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.switchAuthMode('login');
    });

    // One-click demo account buttons
    document.querySelectorAll('.demo-account-pill[data-email]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const email = btn.getAttribute('data-email');
        const password = btn.getAttribute('data-password') || 'School@123';
        await this.handleLogin(email, password);
      });
    });

    // Role modal
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

    // Chat form submit
    const chatInput = document.getElementById('chatInput');
    document.getElementById('chatForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;
      chatInput.value = '';
      chatInput.style.height = 'auto';
      await this.handleUserMessage(text);
    });

    // Auto-grow chat textarea
    chatInput?.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
    });

    // Enter key submits (Shift+Enter for newline)
    chatInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('chatForm')?.requestSubmit();
      }
    });

    // Mic Voice STT
    const micBtn = document.getElementById('btnVoiceRecord');
    micBtn?.addEventListener('click', () => {
      if (this.voice.isRecording) {
        this.voice.stopListening();
        micBtn.classList.remove('recording');
        this.avatar?.setState('idle');
      } else {
        micBtn.classList.add('recording');
        this.avatar?.setState('listening');
        this.voice.startListening(
          async (transcript, conf) => {
            micBtn.classList.remove('recording');
            await this.handleVoiceMessage(transcript, conf);
          },
          (err) => {
            micBtn.classList.remove('recording');
            this.avatar?.setState('idle');
            console.warn('Voice recognition error:', err);
          },
          this.currentLanguage
        );
      }
    });

    // Language dropdown
    document.getElementById('langSelect')?.addEventListener('change', (e) => {
      this.currentLanguage = e.target.value;
    });

    // Quick suggestion chips
    document.querySelectorAll('.suggestion-chip[data-msg]').forEach(chip => {
      chip.addEventListener('click', () => {
        this.handleUserMessage(chip.getAttribute('data-msg'));
      });
    });

    // Staff security console modal
    document.getElementById('btnOpenStaffConsole')?.addEventListener('click', () => this.openStaffConsole());
    document.getElementById('btnCloseStaffModal')?.addEventListener('click', () => this.closeStaffConsole());
    document.getElementById('staffConsoleModal')?.addEventListener('click', (e) => {
      if (e.target === document.getElementById('staffConsoleModal')) this.closeStaffConsole();
    });

    // Console tabs
    document.querySelectorAll('#staffConsoleModal .btn[data-tab]').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('#staffConsoleModal .btn[data-tab]').forEach(t => {
          t.style.borderBottomColor = 'transparent';
        });
        tab.style.borderBottomColor = 'var(--current-accent)';

        const tabName = tab.dataset.tab;
        document.getElementById('panelAudit')?.classList.toggle('hidden', tabName !== 'audit');
        document.getElementById('panelAttacks')?.classList.toggle('hidden', tabName !== 'attacks');
        document.getElementById('panelApprovals')?.classList.toggle('hidden', tabName !== 'approvals');
      });
    });
  }

  // ---------------------------------------------------------------------------
  // AUTH LOGIC
  // ---------------------------------------------------------------------------
  switchAuthMode(mode) {
    const isLogin = mode === 'login';
    document.getElementById('loginForm').classList.toggle('hidden', !isLogin);
    document.getElementById('registerForm').classList.toggle('hidden', isLogin);
    document.getElementById('loginSwitchLink').classList.toggle('hidden', !isLogin);
    document.getElementById('registerSwitchLink').classList.toggle('hidden', isLogin);
    document.getElementById('authTitle').textContent = isLogin ? 'Welcome to XYZ AI' : 'Create School Account';
    document.getElementById('authSubtitle').textContent = isLogin ? 'Your empathetic school companion & ERP assistant' : 'Register as a student, parent, or teacher';
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
    if (btn) { btn.textContent = 'Signing in...'; btn.disabled = true; }
    try {
      const data = await ApiClient.login(email, password);
      this.currentUser = data.user;
      this.currentConversationId = null;
      this.showApp();
      this.onUserLoggedIn();
      this.closeRoleModal();
    } catch (err) {
      this.showAuthError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      if (btn) { btn.textContent = 'Sign In to Portal'; btn.disabled = false; }
    }
  }

  async handleRegister() {
    this.clearAuthError();
    const btn = document.getElementById('registerSubmitBtn');
    if (btn) { btn.textContent = 'Creating Account...'; btn.disabled = true; }
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
    } catch (e) {
      console.warn('Language list load error:', e);
    }
  }

  // ---------------------------------------------------------------------------
  // ROLE & THEME BOOTSTRAP
  // ---------------------------------------------------------------------------
  applyRoleTheme(role) {
    const p = ROLE_ACCENTS[role] || ROLE_ACCENTS.student;
    document.documentElement.style.setProperty('--current-accent', p.accent);
    document.documentElement.style.setProperty('--current-light', p.light);
  }

  onUserLoggedIn() {
    if (!this.currentUser) return;
    const { name, role, is_verified } = this.currentUser;

    // Apply role-based accent
    this.applyRoleTheme(role);

    // Update Header UI
    const nameEl = document.getElementById('headerUserName');
    const pillEl = document.getElementById('headerRolePill');
    const miniEl = document.getElementById('headerAvatarMini');
    if (nameEl) nameEl.textContent = name;
    if (pillEl) pillEl.textContent = role;
    if (miniEl) miniEl.textContent = name.charAt(0).toUpperCase();

    // Update Avatar Persona
    if (this.avatar) this.avatar.setPersona(role);

    // Toggle Staff Console for Teacher & Principal
    const staffCard = document.getElementById('staffConsoleCard');
    const isStaff = role === 'teacher' || role === 'principal';
    if (staffCard) staffCard.style.display = isStaff ? 'block' : 'none';

    // Unverified teacher banner
    const banner = document.getElementById('pendingApprovalBanner');
    if (banner) {
      const showBanner = role === 'teacher' && is_verified === false;
      banner.classList.toggle('hidden', !showBanner);
    }

    // Reset Chat Stream with persona greeting
    const msgContainer = document.getElementById('chatMessages');
    if (msgContainer) {
      msgContainer.innerHTML = '';
      const greetings = {
        student:   `Hello **${name}**! I'm here to help you check attendance, track classes, and stay on top of your studies. What can I do for you today?`,
        parent:    `Namaste **${name}**! I'm here to help you monitor your child's attendance, review school updates, and connect with teachers whenever needed.`,
        teacher:   `Good day, **${name}**! Ready to assist with attendance marking, roster analytics, and class inquiries for your assigned students.`,
        principal: `Welcome, **${name}**. Executive school attendance analytics, class-wise performance reports, and the escalation audit queue are ready.`
      };
      this.appendAiBubble({
        response: greetings[role] || `Hello **${name}**! How can I assist you with XYZ School today?`
      });
    }

    // Update role suggestion chips
    this.updateQuickChips(role);

    // Render Role Dashboard
    this.refreshDashboard();
  }

  updateQuickChips(role) {
    const wrap = document.getElementById('quickChips');
    if (!wrap) return;
    const chips = {
      student:   [['📊 My Attendance', "What is my attendance percentage?"], ['📞 Talk to Teacher', "I want to connect with my teacher."], ['📖 Study Tips', "Can you share effective homework study strategies?"], ['📈 Full Report', "Generate attendance report."]],
      parent:    [['📊 Child\'s Attendance', "What is my child's attendance?"], ['📞 Contact Teacher', "I want to connect with my child's teacher."], ['📈 Monthly Report', "Generate monthly attendance report."], ['🔔 Attendance Status', "Show attendance records for this month."]],
      teacher:   [['✅ Mark Present', "Mark all students present for today in Class 10 Section A."], ['📊 Class Analytics', "Show class attendance analytics."], ['📝 Class Roster', "Show today's class roster."], ['⚠️ Absentees', "Who was absent this week?"]],
      principal: [['🏫 School Overview', "Show school-wide attendance analytics."], ['📊 Class Breakdown', "Show class-wise attendance breakdown."], ['⚠️ Low Attendance Alerts', "Which classes have low attendance?"], ['📋 Escalation Queue', "Show recent escalation tickets."]]
    };
    const roleChips = chips[role] || chips.student;
    wrap.innerHTML = `<span>Suggestions:</span>` + roleChips.map(([label, msg]) =>
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
    } catch (e) {
      console.warn('Dashboard refresh error:', e);
    }
  }

  async approveTeacher(userId) {
    try {
      await ApiClient.approveTeacher(userId);
      await this.refreshDashboard();
      await this.loadTeacherApprovals();
    } catch (e) {
      console.warn('Approve teacher error:', e);
    }
  }

  // ---------------------------------------------------------------------------
  // CHAT INTERACTION
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
      this.appendAiBubble({
        response: e.message,
        security_flag: e.message.includes('Security') || e.message.includes('prohibited') || e.message.includes('Forbidden')
      });
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
        this.voice?.speak(
          result.response,
          result.tts.visemes || [],
          result.tts.duration_seconds || 2.5,
          result.language || this.currentLanguage,
          () => this.avatar?.setState('idle')
        );
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
  // CHAT BUBBLE RENDERING & INLINE DATA CARDS
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
        `<div class="tool-badge">✓ ${t.tool.replace(/_/g, ' ')} <span style="opacity:0.7">(${t.result_status})</span></div>`
      ).join('');
    }

    // Markdown-lite formatting
    const formattedText = (data.response || '')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');

    bubble.innerHTML = `${toolBadgesHtml}<div>${formattedText}</div>`;

    // 1. Render Inline Attendance Progress Ring Card
    if (data.tool_executions?.length > 0) {
      for (const toolExec of data.tool_executions) {
        if (toolExec.tool === 'get_attendance' && toolExec.output) {
          const card = this.buildInlineAttendanceCard(toolExec.output);
          if (card) bubble.appendChild(card);
        }

        // 2. Render Escalation Option Cards
        if (toolExec.tool === 'create_escalation' && toolExec.output) {
          const optionCard = this.buildEscalationOptionsCard();
          bubble.appendChild(optionCard);
        }
      }
    }

    // 3. Proactive Escalation Trigger in Text (e.g. Dissatisfaction)
    if (data.response?.includes('connect you with your teacher, or with school management') ||
        data.response?.includes('Would you like me to connect you with your teacher')) {
      const optionCard = this.buildEscalationOptionsCard();
      bubble.appendChild(optionCard);
    }

    // 4. Escalation Confirmation Card Gate
    if (data.response?.includes('confirm and dispatch this request') ||
        data.response?.includes('Please confirm by replying')) {
      const confirmCard = this.buildEscalationConfirmationCard();
      bubble.appendChild(confirmCard);
    }

    // 5. Parent Multi-Child Disambiguation Cards
    if (data.requires_disambiguation && this.currentUser?.linked_students) {
      const disambigCard = this.buildDisambiguationCards(this.currentUser.linked_students);
      bubble.appendChild(disambigCard);
    }

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }

  // --- Inline Data Card Builders ---

  buildInlineAttendanceCard(output) {
    const summary = output.summary || output;
    const pct = summary.attendance_percentage ?? 0;
    const present = summary.present_days ?? 0;
    const absent = summary.absent_days ?? 0;
    const late = summary.late_days ?? 0;

    const radius = 30;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (pct / 100) * circumference;
    const strokeColor = pct >= 85 ? '#006b5c' : pct >= 75 ? '#8f4e00' : '#ba1a1a';

    const card = document.createElement('div');
    card.className = 'att-inline-card';
    card.innerHTML = `
      <div class="att-ring-row">
        <div class="att-ring-wrap">
          <svg class="att-ring-svg" width="76" height="76">
            <circle stroke="var(--surface-container-highest)" stroke-width="6" fill="transparent" r="${radius}" cx="38" cy="38"/>
            <circle stroke="${strokeColor}" stroke-width="6" stroke-linecap="round" fill="transparent" r="${radius}" cx="38" cy="38"
              style="stroke-dasharray:${circumference}; stroke-dashoffset:${strokeDashoffset}; transition: stroke-dashoffset 0.8s ease;"/>
          </svg>
          <div class="att-ring-text">${pct.toFixed(0)}%</div>
        </div>
        <div style="flex:1;">
          <div style="font-family:var(--font-display);font-weight:700;font-size:1.05rem;color:var(--on-surface);">Verified Attendance</div>
          <div style="font-size:0.75rem;color:var(--on-surface-muted);">Real-time SQL system record</div>
        </div>
      </div>
      <div class="att-counts-grid">
        <div class="att-count-pill"><span class="num" style="color:var(--status-present);">${present}</span><span class="lbl">Present</span></div>
        <div class="att-count-pill"><span class="num" style="color:var(--status-absent);">${absent}</span><span class="lbl">Absent</span></div>
        <div class="att-count-pill"><span class="num" style="color:var(--status-late);">${late}</span><span class="lbl">Late</span></div>
      </div>
    `;
    return card;
  }

  buildEscalationOptionsCard() {
    const wrap = document.createElement('div');
    wrap.className = 'escalation-options-container';
    wrap.innerHTML = `
      <button class="esc-choice-card" data-choice="teacher">
        <span class="icon">👩‍🏫</span>
        <div>
          <span class="title">Talk to Teacher</span>
          <span class="desc">Connect directly with the class teacher</span>
        </div>
      </button>
      <button class="esc-choice-card" data-choice="management">
        <span class="icon">🏫</span>
        <div>
          <span class="title">Contact School Management</span>
          <span class="desc">Escalate inquiry to the Principal's office</span>
        </div>
      </button>
    `;

    wrap.querySelectorAll('.esc-choice-card').forEach(btn => {
      btn.addEventListener('click', () => {
        const choice = btn.getAttribute('data-choice');
        this.handleUserMessage(
          choice === 'teacher'
            ? "I want to connect with my teacher regarding questions."
            : "I want to contact school management."
        );
        wrap.querySelectorAll('.esc-choice-card').forEach(b => b.disabled = true);
      });
    });
    return wrap;
  }

  buildEscalationConfirmationCard() {
    const box = document.createElement('div');
    box.className = 'esc-confirm-box';
    box.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <span style="font-weight:600;font-size:0.875rem;color:var(--on-surface);">Escalation Request</span>
        <span class="esc-badge-pending">Status: Pending</span>
      </div>
      <div style="font-size:0.8125rem;color:var(--on-surface-muted);">
        A confirmation is required before this request is formally dispatched to school staff.
      </div>
      <div style="display:flex;gap:8px;">
        <button class="btn btn-primary btn-sm" id="btnConfirmEscAction">✓ Confirm &amp; Dispatch</button>
        <button class="btn btn-ghost btn-sm" id="btnCancelEscAction">✕ Cancel</button>
      </div>
    `;

    box.querySelector('#btnConfirmEscAction')?.addEventListener('click', () => {
      this.handleUserMessage("Yes, please confirm and submit this request.");
      box.querySelector('.esc-badge-pending').className = 'esc-badge-confirmed';
      box.querySelector('.esc-badge-confirmed').textContent = 'Status: Confirmed';
      box.querySelectorAll('button').forEach(b => b.disabled = true);
    });

    box.querySelector('#btnCancelEscAction')?.addEventListener('click', () => {
      this.handleUserMessage("No, cancel this request.");
      box.querySelectorAll('button').forEach(b => b.disabled = true);
    });

    return box;
  }

  buildDisambiguationCards(kids) {
    const wrap = document.createElement('div');
    wrap.style.display = 'flex';
    wrap.style.flexDirection = 'column';
    wrap.style.gap = '8px';
    wrap.style.marginTop = '10px';

    kids.forEach(k => {
      const btn = document.createElement('button');
      btn.className = 'child-profile-card';
      btn.innerHTML = `
        <div class="child-photo-circle">${(k.name || 'C').charAt(0)}</div>
        <div style="text-align:left;">
          <div class="child-meta-name">${k.name}</div>
          <div class="child-meta-class">Class ${k.class_name}-${k.section} · Roll ${k.roll_no}</div>
        </div>
      `;
      btn.addEventListener('click', () => {
        this.handleUserMessage(`Check attendance for ${k.name}`);
        wrap.querySelectorAll('button').forEach(b => b.disabled = true);
      });
      wrap.appendChild(btn);
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

    // Load Audit Logs
    const tableBody = document.getElementById('auditLogTableBody');
    if (tableBody) {
      tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:16px;color:var(--on-surface-muted);">Loading audit logs...</td></tr>';
      try {
        const logs = await ApiClient.getAuditLogs(25);
        tableBody.innerHTML = logs.map(l => `
          <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:8px 6px;"><small>${l.timestamp.split('T')[1]?.slice(0, 8) || ''}</small></td>
            <td style="padding:8px 6px;"><strong>${l.user_name || '–'}</strong></td>
            <td style="padding:8px 6px;"><code style="font-size:0.75rem;background:var(--surface-container-low);padding:2px 6px;border-radius:4px;">${l.action}</code></td>
            <td style="padding:8px 6px;"><span class="chip ${l.result === 'allowed' ? 'chip-present' : 'chip-absent'}">${l.result}</span></td>
          </tr>
        `).join('');
      } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="4" style="color:var(--status-absent);padding:12px;">Error: ${e.message}</td></tr>`;
      }
    }

    // Load Teacher Approvals
    await this.loadTeacherApprovals();

    // Red-team attack demo buttons
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
        container.innerHTML = '<p style="font-size:0.875rem;color:var(--on-surface-muted);">No pending teacher approval requests.</p>';
        return;
      }
      container.innerHTML = pending.map(t => `
        <div class="roster-item" id="approval-${t.user_id}" style="margin-bottom:8px;">
          <div class="roster-avatar-circle">📚</div>
          <div class="roster-student-info">
            <div class="name">${t.name}</div>
            <div class="roll">${t.email}</div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="window.app.approveTeacher('${t.user_id}').then(()=>{ document.getElementById('approval-${t.user_id}').remove(); })">
            Approve
          </button>
        </div>
      `).join('');
    } catch (e) {
      container.innerHTML = '<p style="color:var(--status-absent);font-size:0.875rem;">Unable to load approvals.</p>';
    }
  }

  closeStaffConsole() {
    document.getElementById('staffConsoleModal')?.classList.remove('active');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new SchoolApp();
});

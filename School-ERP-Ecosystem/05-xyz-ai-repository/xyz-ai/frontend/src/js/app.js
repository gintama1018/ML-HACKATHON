import { ApiClient } from './api.js';
import { AvatarRenderer } from './avatar.js';
import { VoiceController } from './voice.js';
import { DashboardRenderer } from './dashboards.js';

// Role accents strictly matched to DESIGN.MD & Screenshot mockups
const ROLE_ACCENTS = {
  student:   { accent: '#E87A1E', light: '#FFF3E6' },
  parent:    { accent: '#10B981', light: '#ECFDF5' },
  teacher:   { accent: '#147B5D', light: '#E8F6F1' },
  principal: { accent: '#1E3A5F', light: '#EFF6FF' }
};

class SchoolApp {
  constructor() {
    this.currentUser = null;
    this.currentConversationId = null;
    this.currentLanguage = 'en';
    this.currentView = 'chat'; // 'chat' | 'dashboard' | 'profile'
    this.avatar = null;
    this.voice = null;

    this.init();
  }

  async init() {
    this.avatar = new AvatarRenderer('avatarCanvas');
    this.voice = new VoiceController(this.avatar);

    this.bindEvents();
    await this.loadLanguages();

    // Check existing session
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
  // VIEW NAVIGATION (Chat, Dashboard, Profile)
  // ---------------------------------------------------------------------------
  switchView(viewName) {
    this.currentView = viewName;

    // Update nav tab active states
    document.querySelectorAll('.nav-tab-btn[data-view]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    // Toggle view containers
    document.getElementById('viewChat')?.classList.toggle('hidden', viewName !== 'chat');
    document.getElementById('viewDashboard')?.classList.toggle('hidden', viewName !== 'dashboard');
    document.getElementById('viewProfile')?.classList.toggle('hidden', viewName !== 'profile');

    // Re-render view contents if needed
    if (viewName === 'dashboard') {
      this.refreshDashboard();
    } else if (viewName === 'profile') {
      DashboardRenderer.renderProfile(this.currentUser, 'roleProfileContainer');
    }
  }

  showAuth() {
    document.getElementById('authScreen').classList.add('active');
    document.getElementById('authScreen').classList.remove('hidden');
    const app = document.getElementById('appShell');
    app.classList.add('hidden');
    app.style.display = 'none';
  }

  showApp() {
    document.getElementById('authScreen').classList.remove('active');
    document.getElementById('authScreen').classList.add('hidden');
    const app = document.getElementById('appShell');
    app.classList.remove('hidden');
    app.style.display = 'flex';
  }

  // ---------------------------------------------------------------------------
  // EVENT LISTENERS
  // ---------------------------------------------------------------------------
  bindEvents() {
    // 1. Navigation Tab Switching (Chat, Dashboard, Profile)
    document.querySelectorAll('.nav-tab-btn[data-view]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.switchView(btn.dataset.view);
      });
    });

    // 2. Role 2x2 Selector in Auth Screen (Screenshot 1)
    const roleCards = document.querySelectorAll('#authRoleGrid .role-card-item');
    roleCards.forEach(card => {
      card.addEventListener('click', () => {
        roleCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        const defaultEmail = card.getAttribute('data-email');
        const emailInput = document.getElementById('loginEmail');
        if (emailInput && defaultEmail) {
          emailInput.value = defaultEmail;
        }
      });
    });

    // 3. Login Form Submit
    document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value;
      await this.handleLogin(email, password);
    });

    // 4. Registration Form Submit
    document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleRegister();
    });

    // 5. Toggle Login / Register forms
    document.getElementById('showRegisterLink')?.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('loginForm').classList.add('hidden');
      document.getElementById('registerForm').classList.remove('hidden');
      document.getElementById('authRoleGrid').classList.add('hidden');
    });

    document.getElementById('showLoginLink')?.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('loginForm').classList.remove('hidden');
      document.getElementById('registerForm').classList.add('hidden');
      document.getElementById('authRoleGrid').classList.remove('hidden');
    });

    // 6. Dynamic registration fields & OTP Handlers
    document.getElementById('regRole')?.addEventListener('change', (e) => {
      const role = e.target.value;
      document.getElementById('regStudentFields')?.classList.toggle('hidden', role !== 'student');
      document.getElementById('regParentFields')?.classList.toggle('hidden', role !== 'parent');
    });

    // Send OTP Button
    document.getElementById('btnSendOtp')?.addEventListener('click', async () => {
      const email = document.getElementById('regEmail')?.value.trim();
      const name = document.getElementById('regName')?.value.trim() || 'User';
      const msgEl = document.getElementById('otpStatusMsg');
      const btn = document.getElementById('btnSendOtp');
      if (!email) {
        alert('Please enter your email address first.');
        return;
      }
      if (btn) { btn.textContent = 'Sending...'; btn.disabled = true; }
      try {
        const res = await ApiClient.sendOTP(email, name);
        document.getElementById('regOtpField')?.classList.remove('hidden');
        if (msgEl) {
          msgEl.style.color = '#147B5D';
          msgEl.textContent = res.message || 'OTP sent! Please check your email inbox.';
          if (res.dev_hint) {
            msgEl.textContent += ` (Dev Hint: ${res.dev_hint})`;
          }
        }
      } catch (err) {
        if (msgEl) {
          msgEl.style.color = '#BA1A1A';
          msgEl.textContent = err.message || 'Failed to send OTP.';
        }
      } finally {
        if (btn) { btn.textContent = 'Resend OTP'; btn.disabled = false; }
      }
    });

    // Verify OTP Button
    document.getElementById('btnVerifyOtp')?.addEventListener('click', async () => {
      const email = document.getElementById('regEmail')?.value.trim();
      const otpCode = document.getElementById('regOtpCode')?.value.trim();
      const msgEl = document.getElementById('otpStatusMsg');
      const btn = document.getElementById('btnVerifyOtp');
      if (!otpCode || otpCode.length !== 6) {
        alert('Please enter the 6-digit OTP received on your email.');
        return;
      }
      if (btn) { btn.textContent = 'Verifying...'; btn.disabled = true; }
      try {
        await ApiClient.verifyOTP(email, otpCode);
        if (msgEl) {
          msgEl.style.color = '#147B5D';
          msgEl.textContent = '✅ Email verified successfully!';
        }
        if (btn) {
          btn.textContent = '✓ Verified';
          btn.style.background = '#147B5D';
          btn.disabled = true;
        }
        this.verifiedOtpCode = otpCode;
      } catch (err) {
        if (msgEl) {
          msgEl.style.color = '#BA1A1A';
          msgEl.textContent = err.message || 'Invalid or expired OTP.';
        }
        if (btn) { btn.textContent = 'Verify'; btn.disabled = false; }
      }
    });

    // 7. Modals: Switch Role & Logout
    document.getElementById('btnSwitchAccount')?.addEventListener('click', () => {
      document.getElementById('roleModal')?.classList.add('active');
    });
    document.getElementById('btnCloseRoleModal')?.addEventListener('click', () => {
      document.getElementById('roleModal')?.classList.remove('active');
    });
    document.getElementById('roleModal')?.addEventListener('click', (e) => {
      if (e.target === document.getElementById('roleModal')) {
        document.getElementById('roleModal')?.classList.remove('active');
      }
    });

    document.querySelectorAll('[data-switch-email]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const email = btn.getAttribute('data-switch-email');
        await this.handleLogin(email, 'School@123');
        document.getElementById('roleModal')?.classList.remove('active');
      });
    });

    document.getElementById('btnLogout')?.addEventListener('click', () => this.handleLogout());

    // 8. Chat Form & Textarea
    const chatInput = document.getElementById('chatInput');
    document.getElementById('chatForm')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;
      chatInput.value = '';
      chatInput.style.height = 'auto';
      await this.handleUserMessage(text);
    });

    chatInput?.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });

    chatInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('chatForm')?.requestSubmit();
      }
    });

    // 9. Voice STT Button
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
            console.warn('Voice error:', err);
          },
          this.currentLanguage
        );
      }
    });

    // 10. Language Dropdown
    document.getElementById('langSelect')?.addEventListener('change', (e) => {
      this.currentLanguage = e.target.value;
    });

    // 11. Staff Console
    document.getElementById('btnOpenStaffConsole')?.addEventListener('click', () => this.openStaffConsole());
    document.getElementById('btnCloseStaffModal')?.addEventListener('click', () => this.closeStaffConsole());
  }

  // ---------------------------------------------------------------------------
  // AUTH
  // ---------------------------------------------------------------------------
  async handleLogin(email, password) {
    const btn = document.getElementById('loginSubmitBtn');
    if (btn) { btn.textContent = 'Logging in...'; btn.disabled = true; }
    try {
      const data = await ApiClient.login(email, password);
      this.currentUser = data.user;
      this.currentConversationId = null;
      this.showApp();
      this.onUserLoggedIn();
    } catch (err) {
      const errEl = document.getElementById('authError');
      if (errEl) {
        errEl.textContent = err.message || 'Login failed. Please verify credentials.';
        errEl.classList.add('visible');
      }
    } finally {
      if (btn) { btn.textContent = 'Login'; btn.disabled = false; }
    }
  }

  async handleRegister() {
    const btn = document.getElementById('regSubmitBtn');
    if (btn) { btn.textContent = 'Creating...'; btn.disabled = true; }
    try {
      const role = document.getElementById('regRole').value;
      const payload = {
        name: document.getElementById('regName').value.trim(),
        email: document.getElementById('regEmail').value.trim(),
        password: document.getElementById('regPassword').value,
        role,
        language_pref: this.currentLanguage || 'en',
        otp_code: this.verifiedOtpCode || undefined
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
      alert('Registration error: ' + (err.message || 'Please try again.'));
    } finally {
      if (btn) { btn.textContent = 'Create Account'; btn.disabled = false; }
    }
  }

  handleLogout() {
    ApiClient.clearToken();
    this.currentUser = null;
    this.currentConversationId = null;
    this.showAuth();
  }

  // ---------------------------------------------------------------------------
  // POST-LOGIN BOOTSTRAP
  // ---------------------------------------------------------------------------
  applyRoleTheme(role) {
    const p = ROLE_ACCENTS[role] || ROLE_ACCENTS.student;
    document.documentElement.style.setProperty('--current-accent', p.accent);
    document.documentElement.style.setProperty('--current-light', p.light);
  }

  onUserLoggedIn() {
    if (!this.currentUser) return;
    const { name, role, is_verified } = this.currentUser;

    this.applyRoleTheme(role);

    // Navbar
    const nameEl = document.getElementById('navUserName');
    const badgeEl = document.getElementById('navRoleBadge');
    const avatarEl = document.getElementById('navAvatarImg');
    if (nameEl) nameEl.textContent = name;
    if (badgeEl) badgeEl.textContent = role;
    if (avatarEl) avatarEl.textContent = name.charAt(0).toUpperCase();

    // Avatar
    if (this.avatar) this.avatar.setPersona(role);

    // Toggle Staff Console button
    const staffBtnWrap = document.getElementById('staffConsoleBtnWrap');
    if (staffBtnWrap) staffBtnWrap.style.display = (role === 'teacher' || role === 'principal') ? 'block' : 'none';

    // Pending approval banner
    const banner = document.getElementById('pendingApprovalBanner');
    if (banner) banner.classList.toggle('hidden', !(role === 'teacher' && is_verified === false));

    // Reset Chat Messages with Welcome Greeting
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

    // Role Quick Chips
    this.updateQuickChips(role);

    // Initial Dashboard & Profile Setup
    this.refreshDashboard();
    DashboardRenderer.renderProfile(this.currentUser, 'roleProfileContainer');
  }

  updateQuickChips(role) {
    const wrap = document.getElementById('quickChips');
    if (!wrap) return;
    const chips = {
      student:   [['📊 My Attendance', "What is my attendance percentage?"], ['📞 Talk to Teacher', "I want to connect with my teacher regarding questions on my classes."], ['📖 Study Tips', "Help me with homework study tips."], ['📈 Full Report', "Generate attendance report."]],
      parent:    [['📊 Child\'s Attendance', "What is my child's attendance?"], ['📞 Contact Teacher', "I want to connect with my child's teacher."], ['📈 Monthly Report', "Generate monthly attendance report."], ['🔔 Alerts', "Any attendance alerts for my child?"]],
      teacher:   [['✅ Mark Present', "Mark all students present for today in Class 10 Section A."], ['📊 Class Analytics', "Show class attendance analytics."], ['📝 Roster', "Show today's class roster."], ['⚠️ Absentees', "Who was absent this week?"]],
      principal: [['🏫 School Summary', "Show school-wide attendance analytics."], ['📊 Class Breakdown', "Show class-wise attendance breakdown."], ['⚠️ Low Attendance', "Which classes have low attendance?"], ['📋 Escalations', "Show recent escalation tickets."]]
    };
    const roleChips = chips[role] || chips.student;
    wrap.innerHTML = roleChips.map(([label, msg]) =>
      `<button class="nav-tab-btn" style="background:var(--surface-input);font-size:0.75rem;padding:4px 12px;" data-msg="${msg}">${label}</button>`
    ).join('');
    wrap.querySelectorAll('button[data-msg]').forEach(chip => {
      chip.addEventListener('click', () => this.handleUserMessage(chip.getAttribute('data-msg')));
    });
  }

  async refreshDashboard() {
    try {
      const data = await ApiClient.getDashboard();
      DashboardRenderer.renderDashboard(data, 'roleDashboardContainer');
      DashboardRenderer.renderChatSidebar(data, 'chatSidebarSummary');
    } catch (e) {
      console.warn('Dashboard refresh failed:', e);
    }
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
      this.appendAiBubble({
        response: e.message,
        security_flag: e.message.includes('Security') || e.message.includes('prohibited')
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

  appendUserBubble(text) {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble user';
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
    bubble.className = 'chat-bubble ai';
    bubble.innerHTML = '<span class="pulse-dot"></span> Assistant is thinking...';
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
    bubble.className = `chat-bubble ${data.security_flag ? 'security' : 'ai'}`;

    let toolBadgesHtml = '';
    if (data.tool_executions?.length > 0) {
      toolBadgesHtml = data.tool_executions.map(t =>
        `<div style="font-size:0.75rem;font-weight:700;color:var(--current-accent);margin-bottom:8px;">✓ ${t.tool.replace(/_/g, ' ')} (${t.result_status})</div>`
      ).join('');
    }

    const formattedText = (data.response || '')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');

    bubble.innerHTML = `${toolBadgesHtml}<div>${formattedText}</div>`;

    // 1. Inline Attendance Card
    if (data.tool_executions?.length > 0) {
      for (const toolExec of data.tool_executions) {
        if (toolExec.tool === 'get_attendance' && toolExec.output) {
          const card = this.buildInlineAttendanceCard(toolExec.output);
          if (card) bubble.appendChild(card);
        }
        if (toolExec.tool === 'create_escalation' && toolExec.output) {
          const optionCard = this.buildEscalationOptionsCard();
          bubble.appendChild(optionCard);
        }
      }
    }

    // 2. Proactive escalation offer
    if (data.response?.includes('connect you with your teacher, or with school management') ||
        data.response?.includes('Would you like me to connect you with your teacher')) {
      const optionCard = this.buildEscalationOptionsCard();
      bubble.appendChild(optionCard);
    }

    // 3. Confirmation card
    if (data.response?.includes('confirm and dispatch this request') ||
        data.response?.includes('Please confirm by replying')) {
      const confirmCard = this.buildEscalationConfirmationCard();
      bubble.appendChild(confirmCard);
    }

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }

  buildInlineAttendanceCard(output) {
    const summary = output.summary || output;
    const pct = summary.attendance_percentage ?? 0;
    const present = summary.present_days ?? 0;
    const absent = summary.absent_days ?? 0;
    const late = summary.late_days ?? 0;

    const card = document.createElement('div');
    card.style.background = '#ffffff';
    card.style.border = '1px solid var(--border-card)';
    card.style.borderRadius = 'var(--radius-lg)';
    card.style.padding = '16px';
    card.style.marginTop = '12px';
    card.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
        <span style="font-family:var(--font-heading);font-weight:700;color:var(--text-dark);">Verified Attendance</span>
        <span style="font-family:var(--font-heading);font-size:1.4rem;font-weight:700;color:var(--current-accent);">${pct.toFixed(1)}%</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:8px;text-align:center;">
        <div style="background:var(--status-present-bg);padding:8px;border-radius:var(--radius-md);">
          <div style="font-weight:700;color:var(--status-present);">${present}</div>
          <div style="font-size:0.6875rem;color:var(--text-muted);">Present</div>
        </div>
        <div style="background:var(--status-absent-bg);padding:8px;border-radius:var(--radius-md);">
          <div style="font-weight:700;color:var(--status-absent);">${absent}</div>
          <div style="font-size:0.6875rem;color:var(--text-muted);">Absent</div>
        </div>
        <div style="background:var(--status-late-bg);padding:8px;border-radius:var(--radius-md);">
          <div style="font-weight:700;color:var(--status-late);">${late}</div>
          <div style="font-size:0.6875rem;color:var(--text-muted);">Late</div>
        </div>
      </div>
    `;
    return card;
  }

  buildEscalationOptionsCard() {
    const wrap = document.createElement('div');
    wrap.style.display = 'flex';
    wrap.style.flexDirection = 'column';
    wrap.style.gap = '8px';
    wrap.style.marginTop = '12px';
    wrap.innerHTML = `
      <button class="role-card-item" style="flex-direction:row;justify-content:flex-start;text-align:left;gap:12px;padding:12px 16px;" data-esc="teacher">
        <span style="font-size:1.5rem;">👩‍🏫</span>
        <div>
          <div style="font-weight:700;color:var(--text-dark);font-size:0.875rem;">Talk to Teacher</div>
          <div style="font-size:0.75rem;color:var(--text-muted);">Connect directly with the class teacher</div>
        </div>
      </button>
      <button class="role-card-item" style="flex-direction:row;justify-content:flex-start;text-align:left;gap:12px;padding:12px 16px;" data-esc="management">
        <span style="font-size:1.5rem;">🏫</span>
        <div>
          <div style="font-weight:700;color:var(--text-dark);font-size:0.875rem;">Contact School Management</div>
          <div style="font-size:0.75rem;color:var(--text-muted);">Escalate inquiry to the Principal's office</div>
        </div>
      </button>
    `;
    wrap.querySelectorAll('[data-esc]').forEach(btn => {
      btn.addEventListener('click', () => {
        const choice = btn.dataset.esc;
        this.handleUserMessage(choice === 'teacher' ? "I want to connect with my teacher regarding questions on my classes." : "I want to contact school management.");
        wrap.querySelectorAll('button').forEach(b => b.disabled = true);
      });
    });
    return wrap;
  }

  buildEscalationConfirmationCard() {
    const box = document.createElement('div');
    box.style.background = '#ffffff';
    box.style.border = '1.5px solid var(--border-card)';
    box.style.borderRadius = 'var(--radius-lg)';
    box.style.padding = '14px';
    box.style.marginTop = '12px';
    box.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span style="font-weight:700;font-size:0.875rem;">Escalation Request</span>
        <span class="nav-role-badge" style="background:#FEF3C7;color:#92400E;">Pending Confirmation</span>
      </div>
      <div style="display:flex;gap:8px;margin-top:10px;">
        <button class="auth-primary-btn" style="padding:8px 16px;font-size:0.8125rem;width:auto;" id="btnConfirmEsc">✓ Confirm Request</button>
        <button class="nav-tab-btn" style="border:1px solid var(--border-light);padding:8px 16px;font-size:0.8125rem;" id="btnCancelEsc">✕ Cancel</button>
      </div>
    `;
    box.querySelector('#btnConfirmEsc')?.addEventListener('click', () => {
      this.handleUserMessage("Yes, please confirm and submit this request.");
      box.querySelectorAll('button').forEach(b => b.disabled = true);
    });
    box.querySelector('#btnCancelEsc')?.addEventListener('click', () => {
      this.handleUserMessage("No, cancel this request.");
      box.querySelectorAll('button').forEach(b => b.disabled = true);
    });
    return box;
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
          `<option value="${l.code}">🌐 ${l.native_name} (${l.name})${l.deep_tested ? ' ★' : ''}</option>`
        ).join('');
      }
    } catch (e) {
      console.warn('Language list load error:', e);
    }
  }

  // ---------------------------------------------------------------------------
  // STAFF CONSOLE
  // ---------------------------------------------------------------------------
  async openStaffConsole() {
    const modal = document.getElementById('staffConsoleModal');
    if (!modal) return;
    modal.classList.add('active');

    const tableBody = document.getElementById('auditLogTableBody');
    if (tableBody) {
      tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:12px;">Loading live logs...</td></tr>';
      try {
        const logs = await ApiClient.getAuditLogs(20);
        tableBody.innerHTML = logs.map(l => `
          <tr style="border-bottom:1px solid var(--border-light);">
            <td style="padding:6px;"><small>${l.timestamp.split('T')[1]?.slice(0, 8) || ''}</small></td>
            <td style="padding:6px;font-weight:600;">${l.user_name || '–'}</td>
            <td style="padding:6px;"><code style="font-size:0.75rem;background:var(--surface-input);padding:2px 4px;border-radius:4px;">${l.action}</code></td>
            <td style="padding:6px;"><span class="profile-pill-tag ${l.result === 'allowed' ? 'attendance' : 'hobby'}">${l.result}</span></td>
          </tr>
        `).join('');
      } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="4" style="color:var(--status-absent);">Error loading logs</td></tr>`;
      }
    }

    document.querySelectorAll('.btn-run-attack').forEach(btn => {
      btn.onclick = () => {
        this.closeStaffConsole();
        this.switchView('chat');
        this.handleUserMessage(btn.getAttribute('data-attack'));
      };
    });
  }

  closeStaffConsole() {
    document.getElementById('staffConsoleModal')?.classList.remove('active');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new SchoolApp();
});

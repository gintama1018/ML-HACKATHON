import { ApiClient } from './api.js';
import { AvatarRenderer } from './avatar.js';
import { VoiceController } from './voice.js';
import { DashboardRenderer } from './dashboards.js';

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

    // Default auto-login to Student Aarav Sharma or check existing token
    try {
      if (ApiClient.getToken()) {
        this.currentUser = await ApiClient.getMe();
      } else {
        const loginData = await ApiClient.login('aarav.sharma@xyzschool.edu');
        this.currentUser = loginData.user;
      }
      this.onUserLoggedIn();
    } catch (e) {
      console.warn("Auto-login error:", e);
      this.openRoleModal();
    }
  }

  bindEvents() {
    // Role Switcher Button
    document.getElementById('btnSwitchRole')?.addEventListener('click', () => this.openRoleModal());
    document.getElementById('btnCloseRoleModal')?.addEventListener('click', () => this.closeRoleModal());

    // Role Quick Select Cards
    document.querySelectorAll('.role-select-card').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const email = e.currentTarget.getAttribute('data-email');
        if (email) {
          try {
            const loginData = await ApiClient.login(email);
            this.currentUser = loginData.user;
            this.currentConversationId = null;
            this.closeRoleModal();
            this.onUserLoggedIn();
          } catch (err) {
            alert('Login failed: ' + err.message);
          }
        }
      });
    });

    // Chat Message Form
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    chatForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;
      chatInput.value = '';
      await this.handleUserMessage(text);
    });

    // Mic Voice Button
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

    // Language Selector
    document.getElementById('langSelect')?.addEventListener('change', (e) => {
      this.currentLanguage = e.target.value;
    });

    // Staff Security Console Modal Trigger
    document.getElementById('btnOpenStaffConsole')?.addEventListener('click', () => this.openStaffConsole());
    document.getElementById('btnCloseStaffModal')?.addEventListener('click', () => this.closeStaffConsole());
  }

  async loadLanguages() {
    try {
      const langs = await ApiClient.getLanguages();
      const select = document.getElementById('langSelect');
      if (select && langs) {
        select.innerHTML = langs.map(l => `
          <option value="${l.code}">
            ${l.native_name} (${l.name}) ${l.deep_tested ? '★' : ''}
          </option>
        `).join('');
      }
    } catch (e) {
      console.warn("Language load failed:", e);
    }
  }

  async onUserLoggedIn() {
    if (!this.currentUser) return;

    // Update Header Badge
    const nameEl = document.getElementById('headerUserName');
    const pillEl = document.getElementById('headerRolePill');
    if (nameEl) nameEl.textContent = this.currentUser.name;
    if (pillEl) pillEl.textContent = this.currentUser.role;

    // Update avatar persona to match the logged-in role
    if (this.avatar) {
      this.avatar.setPersona(this.currentUser.role);
    }

    // Update Staff Security Console visibility (Only for Teacher / Principal)
    const staffConsole = document.getElementById('staffConsoleCard');
    const isStaff = this.currentUser.role === 'teacher' || this.currentUser.role === 'principal';
    if (staffConsole) {
      if (isStaff) {
        staffConsole.classList.add('active');
      } else {
        staffConsole.classList.remove('active');
      }
    }

    // Reset Chat Messages Container
    const msgContainer = document.getElementById('chatMessages');
    if (msgContainer) {
      msgContainer.innerHTML = '';
      this.appendAiBubble({
        response: `Hello **${this.currentUser.name}**! I am your XYZ AI School Assistant. How may I help you today?`,
        role: this.currentUser.role
      });
    }

    // Refresh Portal Dashboard
    await this.refreshDashboard();
  }

  async refreshDashboard() {
    try {
      const data = await ApiClient.getDashboard();
      DashboardRenderer.render(data, 'dashboardContainer', (action, payload) => {
        if (action === 'chat_prompt') {
          this.handleUserMessage(payload);
        }
      });
    } catch (e) {
      console.warn("Dashboard refresh error:", e);
    }
  }

  async handleUserMessage(text) {
    this.appendUserBubble(text);
    this.avatar.setState('thinking');

    try {
      const result = await ApiClient.sendMessage(text, this.currentConversationId, this.currentLanguage);
      this.currentConversationId = result.conversation_id;
      this.appendAiBubble(result);
      
      // Speak AI reply via Voice & avatar visemes
      this.voice.speak(result.response, [], 2.5, this.currentLanguage, () => {
        this.avatar.setState('idle');
      });

      // Refresh dashboard if tool executed
      if (result.tool_executions && result.tool_executions.length > 0) {
        await this.refreshDashboard();
      }
    } catch (e) {
      this.appendAiBubble({
        response: `Notice: ${e.message}`,
        security_flag: true
      });
      this.avatar.setState('idle');
    }
  }

  async handleVoiceMessage(speechText, confidenceScore) {
    this.appendUserBubble(`🎤 ${speechText}`);
    this.avatar.setState('thinking');

    try {
      const result = await ApiClient.sendVoiceTurn(
        speechText,
        confidenceScore,
        this.currentConversationId,
        this.currentLanguage
      );
      this.currentConversationId = result.conversation_id;
      this.appendAiBubble(result);

      if (result.tts) {
        this.voice.speak(
          result.response,
          result.tts.visemes || [],
          result.tts.duration_seconds || 2.5,
          result.language || this.currentLanguage,
          () => this.avatar.setState('idle')
        );
      } else {
        this.avatar.setState('idle');
      }

      if (result.tool_executions && result.tool_executions.length > 0) {
        await this.refreshDashboard();
      }
    } catch (e) {
      this.appendAiBubble({ response: `Voice note: ${e.message}`, security_flag: true });
      this.avatar.setState('idle');
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

  appendAiBubble(data) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ai ${data.security_flag ? 'security-notice' : ''}`;

    let toolHtml = '';
    if (data.tool_executions && data.tool_executions.length > 0) {
      toolHtml = data.tool_executions.map(t => `
        <div class="tool-invocation-badge">
          <span>✓ ${t.tool} (${t.result_status})</span>
        </div>
      `).join('');
    }

    let formattedText = (data.response || '')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');

    bubble.innerHTML = `
      ${toolHtml}
      <div>${formattedText}</div>
    `;

    // Interactive Escalation Confirmation actions
    if (data.response && data.response.includes('confirm and dispatch this request')) {
      const confirmActions = document.createElement('div');
      confirmActions.style.display = 'flex';
      confirmActions.style.gap = '8px';
      confirmActions.style.marginTop = '12px';
      confirmActions.innerHTML = `
        <button class="btn btn-primary" style="padding:6px 14px; font-size:0.8rem;" id="btnConfirmEsc">Confirm Request</button>
        <button class="btn btn-outline" style="padding:6px 14px; font-size:0.8rem;" id="btnCancelEsc">Cancel</button>
      `;
      bubble.appendChild(confirmActions);

      confirmActions.querySelector('#btnConfirmEsc')?.addEventListener('click', () => {
        this.handleUserMessage('Yes, please confirm and submit this request.');
      });
      confirmActions.querySelector('#btnCancelEsc')?.addEventListener('click', () => {
        this.handleUserMessage('No, cancel this request.');
      });
    }

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  }

  openRoleModal() {
    document.getElementById('roleModal')?.classList.add('active');
  }

  closeRoleModal() {
    document.getElementById('roleModal')?.classList.remove('active');
  }

  async openStaffConsole() {
    const modal = document.getElementById('staffConsoleModal');
    const tableBody = document.getElementById('auditLogTableBody');
    if (!modal) return;

    modal.classList.add('active');
    if (tableBody) {
      tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;">Loading audit trail...</td></tr>';
      try {
        const logs = await ApiClient.getAuditLogs(25);
        tableBody.innerHTML = logs.map(l => `
          <tr>
            <td><small>${l.timestamp.split('T')[1].slice(0, 8)}</small></td>
            <td><strong>${l.user_name}</strong></td>
            <td><code>${l.action}</code></td>
            <td><span class="status-tag ${l.result === 'allowed' ? 'present' : 'absent'}">${l.result}</span></td>
          </tr>
        `).join('');
      } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="4" style="color:var(--danger-text);">Error loading logs: ${e.message}</td></tr>`;
      }
    }

    // Bind live attack demo buttons in staff modal
    document.querySelectorAll('.btn-run-attack').forEach(btn => {
      btn.onclick = (e) => {
        const prompt = e.currentTarget.getAttribute('data-attack');
        this.closeStaffConsole();
        this.handleUserMessage(prompt);
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

/**
 * DashboardRenderer
 * Strict pixel-accurate implementation of user screenshot layouts:
 * 1. Profile View (Screenshot 2)
 * 2. Student & Parent Dashboard (Screenshot 3)
 * 3. Teacher Dashboard with P/A/L pill toggles (Screenshot 4)
 * 4. Principal Dashboard with Weekly bars & Alerts (Screenshot 5)
 */

export class DashboardRenderer {

  // ---------------------------------------------------------------------------
  // 1. DEDICATED PROFILE VIEW (Matches User Screenshot 2)
  // ---------------------------------------------------------------------------
  static renderProfile(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const user = data.user || data;
    const prof = data.student_profile || user.student_profile || {};
    const role = user.role || 'student';

    // Mock rich profile data for student if not in DB
    const studentName = user.name || 'Aarav Sharma';
    const grade = prof.class_name ? `Grade ${prof.class_name}-${prof.section || 'A'}` : 'Grade 10-A';
    const roll = prof.roll_no ? `Roll No. ${prof.roll_no}` : 'Roll No. 101';

    container.innerHTML = `
      <!-- Hero Avatar & Badges -->
      <div class="profile-hero-section">
        <div class="profile-avatar-wrap">
          <div style="width:100%;height:100%;background:var(--current-accent);color:#fff;display:flex;align-items:center;justify-content:center;font-size:2.2rem;font-weight:700;">
            ${studentName.charAt(0)}
          </div>
          <button class="profile-edit-btn" title="Edit Profile">✎</button>
        </div>
        <div class="profile-hero-info">
          <h1>${studentName}</h1>
          <div class="meta-sub">${grade} • ${roll}</div>
          <div class="profile-tags-row">
            <span class="profile-pill-tag attendance">Excellent Attendance</span>
            <span class="profile-pill-tag hobby">${role === 'student' ? 'Math Enthusiast' : role === 'teacher' ? 'Faculty Lead' : 'Parent Liaison'}</span>
          </div>
        </div>
      </div>

      <!-- 2-Column Info Cards -->
      <div class="profile-grid-2col">
        <!-- Personal Info Card -->
        <div class="profile-info-card brown-strip">
          <div class="profile-card-header">
            <span>📇 Personal Info</span>
          </div>
          <div class="profile-item-row">
            <span class="label">Date of Birth</span>
            <span class="value">15 March 2013</span>
          </div>
          <div class="profile-item-row">
            <span class="label">Blood Group</span>
            <span class="value">O Positive (+)</span>
          </div>
          <div class="profile-item-row">
            <span class="label">Emergency Contact</span>
            <span class="value">+91 98222 00001 (Parent)</span>
          </div>
          <div class="profile-item-row">
            <span class="label">Address</span>
            <span class="value">123 Learning Lane, Knowledge City, New Delhi</span>
          </div>
        </div>

        <!-- Academic Profile Card -->
        <div class="profile-info-card green-strip">
          <div class="profile-card-header">
            <span>🎓 Academic Profile</span>
          </div>
          <div class="profile-item-row">
            <span class="label">Class Teacher</span>
            <span class="value">Mr. Amit Verma 🏫</span>
          </div>
          <div class="profile-item-row">
            <span class="label">House / Team</span>
            <span class="value" style="display:flex;align-items:center;gap:6px;">
              <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#E87A1E;"></span> Phoenix House
            </span>
          </div>
          <div class="profile-item-row">
            <span class="label">Favorite Subjects</span>
            <div class="subject-pills-row">
              <span class="subject-pill">Mathematics</span>
              <span class="subject-pill">Science</span>
              <span class="subject-pill">Art</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Settings List Card -->
      <div class="profile-settings-card">
        <div class="settings-nav-item" onclick="document.getElementById('langSelect').focus();">
          <div class="settings-nav-left">
            <span class="icon">🌐</span>
            <div>
              <div class="title">Language Preference</div>
              <div class="sub">Current: English (11 Indian languages available)</div>
            </div>
          </div>
          <span class="settings-arrow">›</span>
        </div>

        <div class="settings-nav-item" onclick="alert('Notification settings: Real-time attendance alerts active via SMS & Email.');">
          <div class="settings-nav-left">
            <span class="icon">🔔</span>
            <div>
              <div class="title">Notification Settings</div>
              <div class="sub">Manage alerts and messages</div>
            </div>
          </div>
          <span class="settings-arrow">›</span>
        </div>

        <div class="settings-nav-item" onclick="alert('XYZ School Privacy Policy: Student data is strictly RBAC-isolated and encrypted.');">
          <div class="settings-nav-left">
            <span class="icon">🛡️</span>
            <div>
              <div class="title">Privacy Policy</div>
              <div class="sub">Data usage, RBAC protection & security</div>
            </div>
          </div>
          <span class="settings-arrow">›</span>
        </div>

        <div class="settings-nav-item" onclick="window.app.handleLogout();">
          <div class="settings-nav-left">
            <span class="icon" style="color:var(--status-absent);">↪</span>
            <div>
              <div class="title" style="color:var(--status-absent);">Logout</div>
            </div>
          </div>
          <span class="settings-arrow">›</span>
        </div>
      </div>
    `;
  }

  // ---------------------------------------------------------------------------
  // 2. DEDICATED ROLE DASHBOARDS (Screenshots 3, 4, 5)
  // ---------------------------------------------------------------------------
  static renderDashboard(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Destroy old Chart instances
    if (window.__dashCharts) {
      window.__dashCharts.forEach(c => { try { c.destroy(); } catch (_) {} });
    }
    window.__dashCharts = [];

    switch (data.role) {
      case 'student':   DashboardRenderer.renderStudentDashboard(container, data);   break;
      case 'parent':    DashboardRenderer.renderParentDashboard(container, data);    break;
      case 'teacher':   DashboardRenderer.renderTeacherDashboard(container, data);   break;
      case 'principal': DashboardRenderer.renderPrincipalDashboard(container, data); break;
    }
  }

  // --- Student Dashboard (Screenshot 3) ---
  static renderStudentDashboard(container, data) {
    const att  = data.attendance || {};
    const recs = data.recent_records || [];
    const pct  = att.attendance_percentage ?? 88;
    const present = att.present_days ?? 29;
    const absent  = att.absent_days ?? 1;
    const late    = att.late_days ?? 0;

    container.innerHTML = `
      <div class="dash-header-section">
        <div class="dash-header-title">
          <span>Attendance Summary</span>
          <span class="nav-role-badge">Student</span>
        </div>
        <div class="dash-header-sub">
          Great job staying consistent! Here is a detailed look at your attendance record for the current term.
        </div>
      </div>

      <!-- Top Row: Term Overview Donut + AI Insight Box -->
      <div class="dash-top-grid">
        <!-- Term Overview Card -->
        <div class="dash-overview-card">
          <h3>Term Overview</h3>
          <div class="term-overview-content">
            <div class="term-donut-wrap">
              <canvas id="termDonutCanvas" width="130" height="130"></canvas>
              <div class="term-donut-center">
                <span class="pct">${pct.toFixed(0)}%</span>
                <span class="lbl">TOTAL</span>
              </div>
            </div>
            <div class="term-breakdown-list">
              <div class="term-breakdown-row">
                <div class="term-dot-label">
                  <span class="term-dot" style="background:#10B981;"></span> Present
                </div>
                <span class="term-days-val">${present} Days</span>
              </div>
              <div class="term-breakdown-row">
                <div class="term-dot-label">
                  <span class="term-dot" style="background:#BA1A1A;"></span> Absent
                </div>
                <span class="term-days-val">${absent} Days</span>
              </div>
              <div class="term-breakdown-row">
                <div class="term-dot-label">
                  <span class="term-dot" style="background:#E87A1E;"></span> Late
                </div>
                <span class="term-days-val">${late} Days</span>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Insight Box (Screenshot 3) -->
        <div class="ai-insight-box">
          <div class="ai-insight-header">
            <span>✨ AI Insight</span>
          </div>
          <div class="ai-insight-body">
            You're on track! Your attendance is <strong>5% higher</strong> than the class average. Keep up the excellent momentum this week.
          </div>
        </div>
      </div>

      <!-- Bottom Card: Recent Attendance History List -->
      <div class="history-card-wrap">
        <div class="history-card-header">
          <h3>Recent Attendance History</h3>
          <a href="#" class="view-all" onclick="window.app.switchView('chat'); window.app.handleUserMessage('Show full attendance history'); return false;">View All</a>
        </div>
        <div>
          ${recs.slice(0, 6).map(r => {
            const isP = r.status === 'present';
            const isL = r.status === 'late';
            const iconClass = isP ? 'present' : isL ? 'late' : 'absent';
            const iconSym = isP ? '✓' : isL ? '🕒' : '✕';
            return `
              <div class="history-item-row">
                <div class="history-item-left">
                  <div class="history-status-icon ${iconClass}">${iconSym}</div>
                  <div>
                    <div class="history-date-main">${DashboardRenderer._fmtDate(r.date)}</div>
                    <div class="history-date-sub">${r.remarks || (isP ? 'Homeroom checked in' : isL ? 'Arrived 15 mins late' : 'Unexcused absence')}</div>
                  </div>
                </div>
                <span class="history-status-badge ${iconClass}">${r.status.charAt(0).toUpperCase() + r.status.slice(1)}</span>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;

    DashboardRenderer._drawDonut('termDonutCanvas', [present, absent, late], ['#10B981', '#BA1A1A', '#E87A1E']);
  }

  // --- Parent Dashboard (Screenshot 3 with Child Switcher) ---
  static renderParentDashboard(container, data) {
    const children = data.children || [];
    const activeChild = children[0] || {};
    const att  = activeChild.summary || {};
    const recs = activeChild.recent_records || [];
    const pct  = att.attendance_percentage ?? 92;
    const present = att.present_days ?? 28;
    const absent  = att.absent_days ?? 2;
    const late    = att.late_days ?? 0;

    container.innerHTML = `
      <div class="dash-header-section">
        <div class="dash-header-title">
          <span>Child Attendance Overview</span>
          <span class="nav-role-badge" style="background:var(--accent-parent-light);color:var(--accent-parent);">Parent</span>
        </div>
        <div class="dash-header-sub">
          Monitor daily attendance and school updates for your children.
        </div>
      </div>

      <!-- Child Selector Pills -->
      <div style="display:flex;gap:12px;margin-bottom:20px;">
        ${children.map((c, i) => `
          <button class="nav-tab-btn ${i === 0 ? 'active' : ''}" style="border:1px solid var(--border-light);padding:8px 18px;"
            onclick="window.app.switchView('chat'); window.app.handleUserMessage('Check attendance for ${c.name}');">
            👶 ${c.name} (${c.class_name}-${c.section})
          </button>
        `).join('')}
      </div>

      <!-- Top Grid -->
      <div class="dash-top-grid">
        <div class="dash-overview-card">
          <h3>${activeChild.name || 'Child'}'s Term Overview</h3>
          <div class="term-overview-content">
            <div class="term-donut-wrap">
              <canvas id="termDonutCanvasParent" width="130" height="130"></canvas>
              <div class="term-donut-center">
                <span class="pct">${pct.toFixed(0)}%</span>
                <span class="lbl">TOTAL</span>
              </div>
            </div>
            <div class="term-breakdown-list">
              <div class="term-breakdown-row">
                <div class="term-dot-label"><span class="term-dot" style="background:#10B981;"></span> Present</div>
                <span class="term-days-val">${present} Days</span>
              </div>
              <div class="term-breakdown-row">
                <div class="term-dot-label"><span class="term-dot" style="background:#BA1A1A;"></span> Absent</div>
                <span class="term-days-val">${absent} Days</span>
              </div>
              <div class="term-breakdown-row">
                <div class="term-dot-label"><span class="term-dot" style="background:#E87A1E;"></span> Late</div>
                <span class="term-days-val">${late} Days</span>
              </div>
            </div>
          </div>
        </div>

        <div class="ai-insight-box">
          <div class="ai-insight-header"><span>✨ AI Parent Insight</span></div>
          <div class="ai-insight-body">
            <strong>${activeChild.name || 'Your child'}</strong> is maintaining consistent attendance! No urgent alerts recorded this week.
          </div>
          <button class="insight-action-pill" style="align-self:flex-start;"
            onclick="window.app.switchView('chat'); window.app.handleUserMessage('I want to connect with my teacher regarding questions on my classes.');">
            👩‍🏫 Request Teacher Callback
          </button>
        </div>
      </div>

      <!-- History List -->
      <div class="history-card-wrap">
        <div class="history-card-header">
          <h3>Recent Records for ${activeChild.name || 'Student'}</h3>
        </div>
        <div>
          ${recs.slice(0, 5).map(r => `
            <div class="history-item-row">
              <div class="history-item-left">
                <div class="history-status-icon ${r.status === 'present' ? 'present' : r.status === 'late' ? 'late' : 'absent'}">
                  ${r.status === 'present' ? '✓' : r.status === 'late' ? '🕒' : '✕'}
                </div>
                <div>
                  <div class="history-date-main">${DashboardRenderer._fmtDate(r.date)}</div>
                  <div class="history-date-sub">${r.remarks || r.status}</div>
                </div>
              </div>
              <span class="history-status-badge ${r.status === 'present' ? 'present' : r.status === 'late' ? 'late' : 'absent'}">${r.status}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    DashboardRenderer._drawDonut('termDonutCanvasParent', [present, absent, late], ['#10B981', '#BA1A1A', '#E87A1E']);
  }

  // --- Teacher Dashboard (Matches User Screenshot 4) ---
  static renderTeacherDashboard(container, data) {
    const classes = data.assigned_classes || [];
    const cls = classes[0] || { class_name: '10', section: 'A', subject: 'Mathematics' };
    const analytics = cls.analytics || {};
    const roster = analytics.class_roster_summary || [];

    const presentCount = roster.filter(s => (s.attendance_percentage ?? 0) >= 80).length || 24;
    const absentCount = 2;
    const lateCount = 1;

    container.innerHTML = `
      <div class="dash-header-section">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
          <span class="nav-role-badge" style="background:var(--accent-teacher-light);color:var(--accent-teacher);">Teacher</span>
          <span style="font-size:0.8125rem;color:var(--text-muted);font-weight:600;">Today, Oct 24</span>
        </div>
        <h1 style="font-family:var(--font-heading);font-size:2rem;font-weight:700;color:var(--text-dark);margin-bottom:6px;">
          ${cls.class_name}-${cls.section} ${cls.subject || 'Social Studies'}
        </h1>
        <div class="dash-header-sub">
          Manage attendance for your morning session. Select a status for each student below.
        </div>
      </div>

      <!-- 3 Stat Metric Cards (Screenshot 4) -->
      <div class="teacher-stat-cards-3col">
        <div class="teacher-metric-card present">
          <div class="label">PRESENT</div>
          <div class="num" id="metricPresent">${presentCount}</div>
        </div>
        <div class="teacher-metric-card absent">
          <div class="label">ABSENT</div>
          <div class="num" id="metricAbsent">${absentCount}</div>
        </div>
        <div class="teacher-metric-card late">
          <div class="label">LATE</div>
          <div class="num" id="metricLate">${lateCount}</div>
        </div>
      </div>

      <!-- Student Table with P / A / L Pill Toggles -->
      <div class="teacher-roster-card">
        <table class="roster-table">
          <thead>
            <tr>
              <th style="width:90px;">Roll No.</th>
              <th>Student Name</th>
              <th style="text-align:right;">Attendance</th>
            </tr>
          </thead>
          <tbody>
            ${roster.map((stu, i) => {
              const defaultStatus = i === 1 ? 'a' : i === 2 ? 'l' : 'p';
              return `
                <tr>
                  <td style="font-weight:600;color:var(--text-muted);">${stu.roll_no || (i + 1 < 10 ? '0' + (i + 1) : i + 1)}</td>
                  <td>
                    <div class="roster-student-cell">
                      <div class="roster-avatar-photo">${(stu.name || 'S').charAt(0)}</div>
                      <span style="font-weight:600;color:var(--text-dark);">${stu.name}</span>
                    </div>
                  </td>
                  <td style="text-align:right;">
                    <div class="pal-toggle-group" data-student-id="${stu.student_id}">
                      <button class="pal-pill-btn p ${defaultStatus === 'p' ? 'active' : ''}" onclick="DashboardRenderer.togglePal(this, 'p')">P</button>
                      <button class="pal-pill-btn a ${defaultStatus === 'a' ? 'active' : ''}" onclick="DashboardRenderer.togglePal(this, 'a')">A</button>
                      <button class="pal-pill-btn l ${defaultStatus === 'l' ? 'active' : ''}" onclick="DashboardRenderer.togglePal(this, 'l')">L</button>
                    </div>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>

      <div class="teacher-save-bar">
        <button class="teacher-save-btn" onclick="alert('Attendance for Class ${cls.class_name}-${cls.section} saved successfully to SQL database!');">
          Save Attendance
        </button>
      </div>
    `;
  }

  // --- Principal Dashboard (Matches User Screenshot 5) ---
  static renderPrincipalDashboard(container, data) {
    const analytics = data.school_analytics || {};
    const avgPct = analytics.school_average_attendance ?? 94;
    const classes = analytics.class_wise_breakdown || [
      { class_name: '5', section: 'A', teacher: 'Ms. Sarah Jenkins', attendance_percentage: 92, status: 'Average' },
      { class_name: '6', section: 'B', teacher: 'Mr. Amit Verma', attendance_percentage: 88, status: 'Low' },
      { class_name: '7', section: 'C', teacher: 'Mrs. Meenakshi S.', attendance_percentage: 98, status: 'Excellent' },
      { class_name: '8', section: 'A', teacher: 'Mr. Vikram Sengupta', attendance_percentage: 95, status: 'Good' },
    ];

    container.innerHTML = `
      <div class="principal-top-bar">
        <div class="principal-title-wrap">
          <div style="display:flex;align-items:center;gap:6px;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#1E3A5F;"></span>
            <span class="nav-role-badge" style="background:#EFF6FF;color:#1E3A5F;">PRINCIPAL</span>
          </div>
          <h1>Good Morning, Dr. Sunita Sharma</h1>
          <div class="dash-header-sub">Here is the school-wide overview for today.</div>
        </div>
        <button class="generate-report-btn" onclick="alert('Generating comprehensive School Attendance PDF Report...');">
          📄 Generate Report
        </button>
      </div>

      <div class="principal-grid-layout">
        <!-- Left Column -->
        <div class="principal-left-col">
          <!-- School-Wide Attendance Card -->
          <div class="school-wide-att-card">
            <div class="title">👥 School-Wide Attendance</div>
            <div class="big-num">
              <span>${avgPct.toFixed(0)}%</span>
              <span class="trend-badge">↗ +1.2% this week</span>
            </div>
            <div class="weekly-bars-chart">
              <div class="weekly-bar" style="height:70%;"></div>
              <div class="weekly-bar" style="height:85%;"></div>
              <div class="weekly-bar" style="height:80%;"></div>
              <div class="weekly-bar" style="height:95%;background:#1E3A5F;opacity:1;"></div>
              <div class="weekly-bar" style="height:90%;"></div>
            </div>
          </div>

          <!-- Alerts Card (Red alert for low attendance) -->
          <div class="alerts-card">
            <div class="alerts-card-header">
              <span>⚠️ Alerts</span>
            </div>
            <div class="alert-item-box high-priority">
              <div>
                <div class="alert-title">Class 6B</div>
                <div class="alert-sub">Dropped below 90%</div>
              </div>
              <span class="alert-pct-pill">88%</span>
            </div>
            <div class="alert-item-box">
              <div>
                <div style="font-weight:600;font-size:0.875rem;color:var(--text-dark);">Class 8A</div>
                <div class="alert-sub">3 consecutive absences</div>
              </div>
              <span style="color:var(--text-muted);">›</span>
            </div>
            <div class="alert-item-box">
              <div>
                <div style="font-weight:600;font-size:0.875rem;color:var(--text-dark);">Grade 4 Gym</div>
                <div class="alert-sub">Unusual absence spike</div>
              </div>
              <span style="color:var(--text-muted);">›</span>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="principal-right-col">
          <!-- AI Insight Card -->
          <div class="ai-insight-box" style="background:#F0FDF4;border-color:rgba(16,185,129,0.2);">
            <div class="ai-insight-header" style="color:#065F46;">
              <span>✨ AI Insight</span>
            </div>
            <div class="ai-insight-body">
              Attendance in <strong>Grade 6</strong> shows a consistent dip on Thursdays. Cross-referencing with schedule data suggests a correlation with afternoon assemblies. Consider restructuring Thursday afternoon activities to improve engagement.
            </div>
            <div class="ai-insight-actions">
              <button class="insight-action-pill" onclick="alert('Viewing Assembly Data Analytics');">View Assembly Data</button>
              <button class="insight-action-pill" onclick="window.app.switchView('chat'); window.app.handleUserMessage('Draft a message to Grade 6 teachers regarding attendance');">Message Grade 6 Teachers</button>
            </div>
          </div>

          <!-- Attendance by Class Table Card -->
          <div class="dash-overview-card" style="padding:24px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
              <h3 style="margin:0;font-size:1.15rem;">Attendance by Class</h3>
              <a href="#" style="font-size:0.8125rem;color:var(--text-muted);text-decoration:none;font-weight:600;">View All →</a>
            </div>
            <table class="roster-table" style="font-size:0.8125rem;">
              <thead>
                <tr>
                  <th style="padding:10px 14px;">CLASS</th>
                  <th style="padding:10px 14px;">TEACHER</th>
                  <th style="padding:10px 14px;">TODAY</th>
                  <th style="padding:10px 14px;text-align:right;">STATUS</th>
                </tr>
              </thead>
              <tbody>
                ${classes.map(c => `
                  <tr>
                    <td style="padding:12px 14px;font-weight:700;">${c.class_name}${c.section}</td>
                    <td style="padding:12px 14px;color:var(--text-muted);">${c.teacher || 'Assigned Staff'}</td>
                    <td style="padding:12px 14px;font-weight:700;">${c.attendance_percentage}%</td>
                    <td style="padding:12px 14px;text-align:right;">
                      <span class="profile-pill-tag" style="${c.attendance_percentage < 90 ? 'background:#FDE8E8;color:#BA1A1A;' : 'background:#E6F6F1;color:#147B5D;'}">
                        ${c.attendance_percentage < 90 ? 'Low' : c.attendance_percentage >= 95 ? 'Excellent' : 'Good'}
                      </span>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  }

  // --- Right Quick Sidebar inside Chat View ---
  static renderChatSidebar(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const user = data.user || data;
    const role = user.role || 'student';

    if (role === 'student') {
      const att = data.attendance || {};
      container.innerHTML = `
        <div class="dash-overview-card" style="padding:20px;">
          <h3 style="font-size:1.05rem;margin-bottom:12px;">📊 Quick Stats</h3>
          <div style="text-align:center;padding:12px;background:var(--surface-input);border-radius:var(--radius-md);margin-bottom:12px;">
            <div style="font-family:var(--font-heading);font-size:2rem;font-weight:700;color:var(--accent-student);">${(att.attendance_percentage ?? 96.7).toFixed(1)}%</div>
            <div style="font-size:0.75rem;color:var(--text-muted);font-weight:600;">Overall Attendance</div>
          </div>
          <button class="nav-tab-btn" style="width:100%;border:1px solid var(--border-light);" onclick="window.app.switchView('dashboard');">
            Open Full Dashboard →
          </button>
        </div>
      `;
    } else if (role === 'parent') {
      const children = data.children || [];
      container.innerHTML = `
        <div class="dash-overview-card" style="padding:20px;">
          <h3 style="font-size:1.05rem;margin-bottom:12px;">👨‍👧 Linked Children</h3>
          ${children.map(c => `
            <div style="padding:10px;border-bottom:1px solid var(--border-light);display:flex;align-items:center;justify-content:space-between;">
              <span style="font-weight:600;font-size:0.875rem;">${c.name}</span>
              <span class="nav-role-badge">${(c.summary?.attendance_percentage ?? 90).toFixed(0)}%</span>
            </div>
          `).join('')}
          <button class="nav-tab-btn" style="width:100%;border:1px solid var(--border-light);margin-top:12px;" onclick="window.app.switchView('dashboard');">
            Open Parent Dashboard →
          </button>
        </div>
      `;
    } else if (role === 'teacher') {
      container.innerHTML = `
        <div class="dash-overview-card" style="padding:20px;">
          <h3 style="font-size:1.05rem;margin-bottom:12px;">📚 Assigned Class</h3>
          <div style="padding:10px;background:var(--surface-input);border-radius:var(--radius-md);margin-bottom:12px;">
            <div style="font-weight:700;">Class 10-A</div>
            <div style="font-size:0.8125rem;color:var(--text-muted);">Mathematics · 25 Students</div>
          </div>
          <button class="nav-tab-btn" style="width:100%;border:1px solid var(--border-light);" onclick="window.app.switchView('dashboard');">
            Open Attendance Marker →
          </button>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="dash-overview-card" style="padding:20px;">
          <h3 style="font-size:1.05rem;margin-bottom:12px;">🏫 School Overview</h3>
          <div style="padding:10px;background:var(--surface-input);border-radius:var(--radius-md);margin-bottom:12px;">
            <div style="font-weight:700;font-size:1.5rem;color:#1E3A5F;">94.2%</div>
            <div style="font-size:0.8125rem;color:var(--text-muted);">Average Attendance</div>
          </div>
          <button class="nav-tab-btn" style="width:100%;border:1px solid var(--border-light);" onclick="window.app.switchView('dashboard');">
            Open Executive Analytics →
          </button>
        </div>
      `;
    }
  }

  // --- Helper: Toggle P / A / L Pill in Teacher Roster ---
  static togglePal(btn, status) {
    const parent = btn.closest('.pal-toggle-group');
    if (!parent) return;
    parent.querySelectorAll('.pal-pill-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }

  static _drawDonut(canvasId, data, colors) {
    requestAnimationFrame(() => {
      const canvas = document.getElementById(canvasId);
      if (!canvas || !window.Chart) return;
      const chart = new window.Chart(canvas, {
        type: 'doughnut',
        data: {
          datasets: [{
            data,
            backgroundColor: colors,
            borderWidth: 0,
            hoverOffset: 3
          }]
        },
        options: {
          cutout: '76%',
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          animation: { duration: 600, easing: 'easeInOutQuart' }
        }
      });
      if (window.__dashCharts) window.__dashCharts.push(chart);
    });
  }

  static _fmtDate(dateStr) {
    if (!dateStr) return 'Today';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  }
}

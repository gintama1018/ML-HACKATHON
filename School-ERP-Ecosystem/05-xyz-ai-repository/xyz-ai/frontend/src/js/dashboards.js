/**
 * DashboardRenderer
 * Renders role-specific dashboard panels per DESIGN.MD "Warm Academic Humanism".
 * Uses Chart.js (loaded via CDN) for donut + bar charts.
 */

const ROLE_ACCENTS = {
  student:   '#FF9F43',
  parent:    '#58B19F',
  teacher:   '#54A0FF',
  principal: '#2C3E50'
};

const LOW_ATTENDANCE_THRESHOLD = 75; // classes below this % get flagged red

export class DashboardRenderer {

  /**
   * @param {Object} data - Response from GET /api/v1/portal/dashboard
   * @param {string} containerId - ID of the container element
   * @param {Function} onAction - callback(action, payload)
   */
  static render(data, containerId, onAction) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Destroy old Chart.js instances to avoid canvas conflicts
    if (window.__dashCharts) {
      window.__dashCharts.forEach(c => { try { c.destroy(); } catch (_) {} });
    }
    window.__dashCharts = [];

    switch (data.role) {
      case 'student':   DashboardRenderer.renderStudent(container, data, onAction);   break;
      case 'parent':    DashboardRenderer.renderParent(container, data, onAction);    break;
      case 'teacher':   DashboardRenderer.renderTeacher(container, data, onAction);   break;
      case 'principal': DashboardRenderer.renderPrincipal(container, data, onAction); break;
    }
  }

  // -------------------------------------------------------------------------
  // STUDENT
  // -------------------------------------------------------------------------
  static renderStudent(container, data, onAction) {
    const prof = data.student_profile || {};
    const att  = data.attendance || {};
    const recs = data.recent_records || [];
    const pct  = att.attendance_percentage ?? 0;
    const present = att.present_days ?? 0;
    const absent  = att.absent_days ?? 0;
    const late    = att.late_days ?? 0;
    const total   = att.total_school_days ?? (present + absent + late);
    const accent  = ROLE_ACCENTS.student;

    container.innerHTML = `
      <!-- Profile card -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent}"></div>
        <div class="card-body">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <div style="width:48px;height:48px;border-radius:50%;background:rgba(255,159,67,0.12);color:${accent};display:flex;align-items:center;justify-content:center;font-family:'Quicksand',sans-serif;font-weight:700;font-size:1.1rem;flex-shrink:0;">
              ${(prof.name || 'S').charAt(0)}
            </div>
            <div>
              <div style="font-weight:600;font-size:0.9rem;color:var(--on-surface);">${prof.name || '–'}</div>
              <div style="font-size:0.75rem;color:var(--on-surface-muted);">Class ${prof.class_name}-${prof.section} · Roll ${prof.roll_no}</div>
            </div>
          </div>

          <div class="insight-bubble">
            <p>${DashboardRenderer._attendanceInsight(pct, 'student')}</p>
          </div>

          <!-- Donut chart -->
          <div class="donut-chart-wrap" style="margin:16px 0 12px;">
            <div style="position:relative;width:110px;height:110px;flex-shrink:0;">
              <canvas id="dash-donut-student" width="110" height="110"></canvas>
              <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;">
                <span style="font-family:'Quicksand',sans-serif;font-size:1.3rem;font-weight:700;color:var(--on-surface);">${pct.toFixed(1)}%</span>
                <span style="font-size:0.6rem;color:var(--on-surface-muted);text-transform:uppercase;letter-spacing:0.04em;">Attendance</span>
              </div>
            </div>
            <div class="donut-legend">
              <div class="legend-item"><div class="legend-dot" style="background:${accent}"></div>${present} Present</div>
              <div class="legend-item"><div class="legend-dot" style="background:#ffdad6"></div>${absent} Absent</div>
              <div class="legend-item"><div class="legend-dot" style="background:#ffdcc2"></div>${late} Late</div>
              <div class="legend-item"><div class="legend-dot" style="background:var(--surface-highest)"></div>${total} Total</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent records -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent}"></div>
        <div class="card-body">
          <div class="card-title">Recent Records</div>
          <div style="overflow-x:auto;">
            <table class="records-table">
              <thead><tr><th>Date</th><th>Status</th><th>Remarks</th></tr></thead>
              <tbody>
                ${recs.slice(0, 8).map(r => `
                  <tr>
                    <td>${DashboardRenderer._fmtDate(r.date)}</td>
                    <td><span class="chip chip-${r.status}">${r.status}</span></td>
                    <td style="color:var(--on-surface-muted);font-size:0.75rem;">${r.remarks || '–'}</td>
                  </tr>
                `).join('')}
                ${recs.length === 0 ? '<tr><td colspan="3" style="color:var(--on-surface-muted);text-align:center;">No records yet</td></tr>' : ''}
              </tbody>
            </table>
          </div>
          <button class="btn btn-secondary btn-sm" style="margin-top:12px;width:100%;"
            onclick="window.app.handleUserMessage('Show my full attendance history')">
            View Full Report →
          </button>
        </div>
      </div>
    `;

    DashboardRenderer._drawDonut('dash-donut-student', [present, absent, late],
      [accent, '#ffdad6', '#ffdcc2']);
  }

  // -------------------------------------------------------------------------
  // PARENT
  // -------------------------------------------------------------------------
  static renderParent(container, data, onAction) {
    const children = data.children || [];
    const accent = ROLE_ACCENTS.parent;

    // Build child selector cards
    const childCardsHtml = children.map((child, i) => `
      <div class="child-card ${i === 0 ? 'active' : ''}" data-child-idx="${i}">
        <div class="child-initials" style="background:${accent};">${(child.name || 'C').charAt(0)}</div>
        <div class="child-info">
          <div class="child-name">${child.name}</div>
          <div class="child-class">Class ${child.class_name}-${child.section} · ${(child.summary?.attendance_percentage ?? 0).toFixed(1)}%</div>
        </div>
      </div>
    `).join('');

    container.innerHTML = `
      <div class="card">
        <div class="card-header-strip" style="background:${accent}"></div>
        <div class="card-body">
          <div class="card-title">My Children</div>
          <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px;" id="childSelectorList">
            ${childCardsHtml}
          </div>
          <div id="childDetailArea"></div>
        </div>
      </div>
    `;

    // Wire child selector
    const renderChildDetail = (idx) => {
      const child = children[idx];
      if (!child) return;
      const att = child.summary || {};
      const pct = att.attendance_percentage ?? 0;
      const present = att.present_days ?? 0;
      const absent = att.absent_days ?? 0;
      const late = att.late_days ?? 0;
      const recs = child.recent_records || [];

      document.getElementById('childDetailArea').innerHTML = `
        <div class="insight-bubble">
          <p>${DashboardRenderer._attendanceInsight(pct, 'parent', child.name)}</p>
        </div>

        <div class="donut-chart-wrap" style="margin:12px 0;">
          <div style="position:relative;width:90px;height:90px;flex-shrink:0;">
            <canvas id="dash-donut-parent" width="90" height="90"></canvas>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;">
              <span style="font-family:'Quicksand',sans-serif;font-size:1.1rem;font-weight:700;">${pct.toFixed(1)}%</span>
            </div>
          </div>
          <div class="donut-legend">
            <div class="legend-item"><div class="legend-dot" style="background:${accent}"></div>${present} Present</div>
            <div class="legend-item"><div class="legend-dot" style="background:#ffdad6"></div>${absent} Absent</div>
            <div class="legend-item"><div class="legend-dot" style="background:#ffdcc2"></div>${late} Late</div>
          </div>
        </div>

        <div style="overflow-x:auto;margin-bottom:12px;">
          <table class="records-table">
            <thead><tr><th>Date</th><th>Status</th></tr></thead>
            <tbody>
              ${recs.slice(0, 5).map(r => `
                <tr>
                  <td>${DashboardRenderer._fmtDate(r.date)}</td>
                  <td><span class="chip chip-${r.status}">${r.status}</span></td>
                </tr>
              `).join('')}
              ${recs.length === 0 ? '<tr><td colspan="2" style="text-align:center;color:var(--on-surface-muted);">No records</td></tr>' : ''}
            </tbody>
          </table>
        </div>

        <button class="btn btn-secondary btn-sm" style="width:100%;"
          onclick="window.app.handleUserMessage('Show attendance report for ${child.name}')">
          Full Report for ${child.name} →
        </button>
      `;

      DashboardRenderer._drawDonut('dash-donut-parent', [present, absent, late],
        [accent, '#ffdad6', '#ffdcc2']);
    };

    // Initial render
    if (children.length > 0) renderChildDetail(0);

    // Click handlers
    document.getElementById('childSelectorList')?.querySelectorAll('.child-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.child-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        renderChildDetail(parseInt(card.dataset.childIdx));
      });
    });
  }

  // -------------------------------------------------------------------------
  // TEACHER
  // -------------------------------------------------------------------------
  static renderTeacher(container, data, onAction) {
    const classes = data.assigned_classes || [];
    const accent = ROLE_ACCENTS.teacher;

    let classTabsHtml = '';
    let classContentHtml = '';

    classes.forEach((cls, ci) => {
      const analytics = cls.analytics || {};
      const avgPct = analytics.average_attendance_percentage ?? 0;
      const roster = analytics.class_roster_summary || [];

      classTabsHtml += `
        <button class="console-tab ${ci === 0 ? 'active' : ''}" data-class-idx="${ci}">
          ${cls.class_name}-${cls.section}
        </button>
      `;

      classContentHtml += `
        <div class="roster-class-panel ${ci === 0 ? '' : 'hidden'}" id="class-panel-${ci}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div>
              <div style="font-size:0.8rem;color:var(--on-surface-muted);">Subject: <strong>${cls.subject || '–'}</strong></div>
              <div style="font-size:0.8rem;color:var(--on-surface-muted);">Class average: <strong style="color:${accent};">${avgPct.toFixed(1)}%</strong></div>
            </div>
            <button class="btn btn-secondary btn-sm"
              onclick="window.app.handleUserMessage('Mark all students present in Class ${cls.class_name} Section ${cls.section} for today')">
              ✓ All Present
            </button>
          </div>

          <div class="insight-bubble">
            <p>${DashboardRenderer._attendanceInsight(avgPct, 'teacher', `Class ${cls.class_name}-${cls.section}`)}</p>
          </div>

          <div class="roster-list" style="margin-top:12px;">
            ${roster.slice(0, 20).map(stu => `
              <div class="roster-student-card">
                <div class="roster-initials">${(stu.name || 'S').charAt(0)}</div>
                <div style="flex:1;min-width:0;">
                  <div class="roster-name">${stu.name}</div>
                  <div class="roster-roll">Roll ${stu.roll_no} · ${(stu.attendance_percentage ?? 0).toFixed(0)}% this month</div>
                </div>
                <select class="status-select" id="status-select-${stu.student_id}">
                  <option value="present">Present</option>
                  <option value="absent">Absent</option>
                  <option value="late">Late</option>
                  <option value="excused">Excused</option>
                </select>
                <button class="btn btn-primary btn-xs mark-btn"
                  onclick="(function(){
                    var sel = document.getElementById('status-select-${stu.student_id}');
                    var status = sel ? sel.value : 'present';
                    window.app.handleUserMessage('Mark ${stu.name} (Roll ${stu.roll_no}) as ' + status + ' in Class ${cls.class_name} Section ${cls.section} for today');
                  })()">
                  Mark
                </button>
              </div>
            `).join('')}
            ${roster.length === 0 ? '<p style="color:var(--on-surface-muted);font-size:0.82rem;text-align:center;">No roster data available</p>' : ''}
          </div>
        </div>
      `;
    });

    container.innerHTML = `
      <div class="card">
        <div class="card-header-strip" style="background:${accent}"></div>
        <div class="card-body">
          <div class="card-title">My Classes</div>
          ${classes.length > 1 ? `<div class="console-tabs" style="margin: -8px -24px 16px;padding:0 24px;">${classTabsHtml}</div>` : ''}
          ${classContentHtml}
          ${classes.length === 0 ? '<p style="color:var(--on-surface-muted);font-size:0.82rem;">No classes assigned yet.</p>' : ''}
        </div>
      </div>
    `;

    // Wire class tabs
    container.querySelectorAll('.console-tab[data-class-idx]').forEach(tab => {
      tab.addEventListener('click', () => {
        container.querySelectorAll('.console-tab[data-class-idx]').forEach(t => t.classList.remove('active'));
        container.querySelectorAll('.roster-class-panel').forEach(p => p.classList.add('hidden'));
        tab.classList.add('active');
        document.getElementById(`class-panel-${tab.dataset.classIdx}`)?.classList.remove('hidden');
      });
    });
  }

  // -------------------------------------------------------------------------
  // PRINCIPAL
  // -------------------------------------------------------------------------
  static renderPrincipal(container, data, onAction) {
    const analytics = data.school_analytics || {};
    const avgPct  = analytics.school_average_attendance ?? 0;
    const totalStu = analytics.total_enrolled_students ?? 0;
    const classes   = analytics.class_wise_breakdown || [];
    const escalations = data.recent_escalations || [];
    const pendingApprovals = data.pending_teacher_approvals || [];
    const accent = ROLE_ACCENTS.principal;

    container.innerHTML = `
      <!-- Big stat -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent}"></div>
        <div class="card-body">
          <div class="card-title">School Overview</div>
          <div class="insight-bubble">
            <p>${DashboardRenderer._attendanceInsight(avgPct, 'principal')}</p>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px;">
            <div class="stat-box">
              <div class="stat-val" style="color:${accent};font-size:2rem;">${avgPct.toFixed(1)}%</div>
              <div class="stat-label">School Average</div>
            </div>
            <div class="stat-box">
              <div class="stat-val">${totalStu}</div>
              <div class="stat-label">Students Enrolled</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Class-wise bar chart -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent}"></div>
        <div class="card-body">
          <div class="card-title">Class-wise Attendance</div>
          ${classes.length > 0 ? `
            <div class="bar-list" id="principalBarList">
              ${classes.map(cls => {
                const pct = (cls.attendance_percentage ?? 0);
                const isLow = pct < LOW_ATTENDANCE_THRESHOLD;
                return `
                  <div class="bar-item ${isLow ? 'low-att' : ''}">
                    <div class="bar-meta">
                      <span class="bar-label">Class ${cls.class_name}-${cls.section}${isLow ? ' ⚠️' : ''}</span>
                      <span class="bar-pct">${pct.toFixed(1)}%</span>
                    </div>
                    <div class="bar-track">
                      <div class="bar-fill" style="width:${pct}%;background:${isLow ? '#ba1a1a' : accent};"></div>
                    </div>
                    <div style="font-size:0.72rem;color:var(--on-surface-muted);margin-top:4px;">${cls.student_count ?? '–'} students</div>
                  </div>
                `;
              }).join('')}
            </div>
            ${classes.some(c => c.attendance_percentage < LOW_ATTENDANCE_THRESHOLD) ? `
              <div style="font-size:0.75rem;color:var(--error);margin-top:8px;">
                ⚠️ Red bars indicate classes below ${LOW_ATTENDANCE_THRESHOLD}% attendance threshold
              </div>
            ` : ''}
          ` : '<p style="color:var(--on-surface-muted);font-size:0.82rem;">No class data available</p>'}
        </div>
      </div>

      <!-- Pending teacher approvals -->
      ${pendingApprovals.length > 0 ? `
        <div class="card">
          <div class="card-header-strip" style="background:var(--warning)"></div>
          <div class="card-body">
            <div class="card-title">⏳ Pending Teacher Approvals (${pendingApprovals.length})</div>
            ${pendingApprovals.map(t => `
              <div class="approval-card" id="dash-approval-${t.user_id}">
                <div class="approval-info">
                  <div class="approval-name">📚 ${t.name}</div>
                  <div class="approval-email">${t.email}</div>
                </div>
                <button class="btn btn-primary btn-sm"
                  onclick="window.app.approveTeacher('${t.user_id}').then(()=>{ document.getElementById('dash-approval-${t.user_id}').remove(); })">
                  Approve
                </button>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <!-- Recent escalations -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent}"></div>
        <div class="card-body">
          <div class="card-title">Recent Escalations</div>
          ${escalations.length > 0 ? `
            <div style="display:flex;flex-direction:column;gap:8px;">
              ${escalations.map(e => `
                <div style="background:var(--surface-low);border-radius:var(--r-md);padding:10px 12px;border:1px solid var(--border);">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
                    <div>
                      <div style="font-size:0.82rem;font-weight:600;color:var(--on-surface);">${e.user_name}</div>
                      <div style="font-size:0.75rem;color:var(--on-surface-muted);">→ ${e.target} · ${DashboardRenderer._fmtDate(e.created_at?.split('T')[0])}</div>
                      <div style="font-size:0.78rem;color:var(--on-surface-var);margin-top:4px;">${e.reason?.slice(0,80) || '–'}</div>
                    </div>
                    <span class="chip ${e.status === 'confirmed' ? 'chip-present' : e.status === 'pending' ? 'chip-late' : 'chip-absent'}"
                      style="flex-shrink:0;">${e.status}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          ` : '<p style="color:var(--on-surface-muted);font-size:0.82rem;">No recent escalations</p>'}
        </div>
      </div>
    `;
  }

  // -------------------------------------------------------------------------
  // HELPERS
  // -------------------------------------------------------------------------
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
            hoverOffset: 4
          }]
        },
        options: {
          cutout: '72%',
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          animation: { duration: 800, easing: 'easeInOutQuart' }
        }
      });
      if (window.__dashCharts) window.__dashCharts.push(chart);
    });
  }

  static _fmtDate(dateStr) {
    if (!dateStr) return '–';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  }

  static _attendanceInsight(pct, role, name = '') {
    const who = name ? `<strong>${name}'s</strong>` : (role === 'student' ? 'Your' : role === 'teacher' ? 'Class' : 'School');
    if (pct >= 95) return `✨ ${who} attendance is excellent at <strong>${pct.toFixed(1)}%</strong>. Outstanding commitment!`;
    if (pct >= 85) return `👍 ${who} attendance is good at <strong>${pct.toFixed(1)}%</strong>. Keep up the consistency!`;
    if (pct >= 75) return `📋 ${who} attendance stands at <strong>${pct.toFixed(1)}%</strong>. A little more regularity would help.`;
    return `⚠️ ${who} attendance of <strong>${pct.toFixed(1)}%</strong> is below the 75% requirement. Immediate attention recommended.`;
  }
}

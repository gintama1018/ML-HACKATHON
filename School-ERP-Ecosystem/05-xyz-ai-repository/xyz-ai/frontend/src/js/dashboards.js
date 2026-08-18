/**
 * DashboardRenderer
 * Role-tailored live dashboards strictly implementing DESIGN.MD "Warm Academic Humanism".
 * Uses Chart.js (CDN) for donut charts and responsive SVG progress bars.
 */

const ROLE_ACCENTS = {
  student:   '#FF9F43',
  parent:    '#58B19F',
  teacher:   '#54A0FF',
  principal: '#2C3E50'
};

const LOW_ATTENDANCE_THRESHOLD = 75; // Flag red if attendance is below 75%

export class DashboardRenderer {

  /**
   * @param {Object} data - Response from GET /api/v1/portal/dashboard
   * @param {string} containerId - ID of the container element
   * @param {Function} onAction - callback(action, payload)
   */
  static render(data, containerId, onAction) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Clean up previous Chart instances to prevent canvas memory leaks
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
  // 1. STUDENT DASHBOARD
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
      <!-- Student Profile & Donut Chart Card -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent};"></div>
        <div class="card-body">
          <div style="display:flex;align-items:center;gap:14px;margin-bottom:16px;">
            <div style="width:52px;height:52px;border-radius:50%;background:rgba(255,159,67,0.15);color:${accent};display:flex;align-items:center;justify-content:center;font-family:'Quicksand',sans-serif;font-weight:700;font-size:1.25rem;flex-shrink:0;">
              ${(prof.name || 'S').charAt(0)}
            </div>
            <div>
              <div style="font-weight:700;font-size:1.05rem;color:var(--on-surface);">${prof.name || '–'}</div>
              <div style="font-size:0.8125rem;color:var(--on-surface-muted);">Class ${prof.class_name}-${prof.section} · Roll No. ${prof.roll_no}</div>
            </div>
          </div>

          <div class="insight-bubble">
            <p>${DashboardRenderer._attendanceInsight(pct, 'student')}</p>
          </div>

          <!-- Attendance Donut Chart -->
          <div class="donut-chart-container" style="margin:18px 0 12px;">
            <div style="position:relative;width:110px;height:110px;flex-shrink:0;">
              <canvas id="dash-donut-student" width="110" height="110"></canvas>
              <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;">
                <span style="font-family:'Quicksand',sans-serif;font-size:1.35rem;font-weight:700;color:var(--on-surface);">${pct.toFixed(0)}%</span>
                <span style="font-size:0.625rem;color:var(--on-surface-muted);text-transform:uppercase;letter-spacing:0.04em;font-weight:600;">Overall</span>
              </div>
            </div>
            <div class="donut-legend-list">
              <div class="donut-legend-item"><div class="dot" style="background:${accent};"></div>${present} Days Present</div>
              <div class="donut-legend-item"><div class="dot" style="background:#ba1a1a;"></div>${absent} Days Absent</div>
              <div class="donut-legend-item"><div class="dot" style="background:#8f4e00;"></div>${late} Days Late</div>
              <div class="donut-legend-item" style="color:var(--on-surface-muted);"><div class="dot" style="background:var(--surface-container-highest);"></div>${total} School Days</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Attendance Records Card -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent};"></div>
        <div class="card-body">
          <div class="card-title">📅 Recent Attendance History</div>
          <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:0.8125rem;">
              <thead>
                <tr style="text-align:left;border-bottom:1px solid var(--border);color:var(--on-surface-muted);">
                  <th style="padding:8px 6px;">Date</th>
                  <th style="padding:8px 6px;">Status</th>
                  <th style="padding:8px 6px;">Remarks</th>
                </tr>
              </thead>
              <tbody>
                ${recs.slice(0, 8).map(r => `
                  <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:8px 6px;font-weight:500;">${DashboardRenderer._fmtDate(r.date)}</td>
                    <td style="padding:8px 6px;"><span class="chip chip-${r.status}">${r.status}</span></td>
                    <td style="padding:8px 6px;color:var(--on-surface-muted);font-size:0.75rem;">${r.remarks || '–'}</td>
                  </tr>
                `).join('')}
                ${recs.length === 0 ? '<tr><td colspan="3" style="color:var(--on-surface-muted);text-align:center;padding:12px;">No attendance records found</td></tr>' : ''}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;

    DashboardRenderer._drawDonut('dash-donut-student', [present, absent, late], [accent, '#ffdad6', '#ffdcc2']);
  }

  // -------------------------------------------------------------------------
  // 2. PARENT DASHBOARD (Multi-Child Selector & Detail)
  // -------------------------------------------------------------------------
  static renderParent(container, data, onAction) {
    const children = data.children || [];
    const accent = ROLE_ACCENTS.parent;

    const childCardsHtml = children.map((child, i) => `
      <div class="child-profile-card ${i === 0 ? 'active' : ''}" data-child-idx="${i}">
        <div class="child-photo-circle" style="background:${accent};">${(child.name || 'C').charAt(0)}</div>
        <div style="flex:1;">
          <div class="child-meta-name">${child.name}</div>
          <div class="child-meta-class">Class ${child.class_name}-${child.section} · Roll ${child.roll_no}</div>
        </div>
        <span class="chip chip-present">${(child.summary?.attendance_percentage ?? 0).toFixed(0)}%</span>
      </div>
    `).join('');

    container.innerHTML = `
      <!-- Parent Children Selector Card -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent};"></div>
        <div class="card-body">
          <div class="card-title">👨‍👧 My Children (${children.length})</div>
          <div class="child-profile-grid" id="childSelectorList">
            ${childCardsHtml}
          </div>
          <div id="childDetailArea"></div>
        </div>
      </div>
    `;

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

        <div class="donut-chart-container" style="margin:14px 0;">
          <div style="position:relative;width:96px;height:96px;flex-shrink:0;">
            <canvas id="dash-donut-parent" width="96" height="96"></canvas>
            <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;">
              <span style="font-family:'Quicksand',sans-serif;font-size:1.15rem;font-weight:700;color:var(--on-surface);">${pct.toFixed(0)}%</span>
            </div>
          </div>
          <div class="donut-legend-list">
            <div class="donut-legend-item"><div class="dot" style="background:${accent};"></div>${present} Present</div>
            <div class="donut-legend-item"><div class="dot" style="background:#ba1a1a;"></div>${absent} Absent</div>
            <div class="donut-legend-item"><div class="dot" style="background:#8f4e00;"></div>${late} Late</div>
          </div>
        </div>

        <div style="overflow-x:auto;margin-top:12px;">
          <table style="width:100%;border-collapse:collapse;font-size:0.8125rem;">
            <thead>
              <tr style="text-align:left;border-bottom:1px solid var(--border);color:var(--on-surface-muted);">
                <th style="padding:6px;">Date</th>
                <th style="padding:6px;">Status</th>
                <th style="padding:6px;">Remarks</th>
              </tr>
            </thead>
            <tbody>
              ${recs.slice(0, 5).map(r => `
                <tr style="border-bottom:1px solid var(--border);">
                  <td style="padding:6px;">${DashboardRenderer._fmtDate(r.date)}</td>
                  <td style="padding:6px;"><span class="chip chip-${r.status}">${r.status}</span></td>
                  <td style="padding:6px;color:var(--on-surface-muted);font-size:0.75rem;">${r.remarks || '–'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <button class="btn btn-secondary btn-sm" style="width:100%;margin-top:14px;"
          onclick="window.app.handleUserMessage('Show full attendance history for ${child.name}')">
          View Complete Report for ${child.name} →
        </button>
      `;

      DashboardRenderer._drawDonut('dash-donut-parent', [present, absent, late], [accent, '#ffdad6', '#ffdcc2']);
    };

    if (children.length > 0) renderChildDetail(0);

    document.getElementById('childSelectorList')?.querySelectorAll('.child-profile-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.child-profile-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        renderChildDetail(parseInt(card.dataset.childIdx));
      });
    });
  }

  // -------------------------------------------------------------------------
  // 3. TEACHER DASHBOARD (Class Roster & Quick Attendance Toggle)
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
        <button class="btn btn-ghost btn-sm ${ci === 0 ? 'active' : ''}" data-class-tab="${ci}"
          style="${ci === 0 ? `background:var(--teacher-light);color:${accent};border-color:${accent};` : ''}">
          Class ${cls.class_name}-${cls.section}
        </button>
      `;

      classContentHtml += `
        <div class="teacher-class-panel ${ci === 0 ? '' : 'hidden'}" id="teacher-panel-${ci}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;background:var(--surface-container-low);padding:12px 16px;border-radius:var(--r-lg);">
            <div>
              <div style="font-size:0.8125rem;color:var(--on-surface-muted);">Subject: <strong style="color:var(--on-surface);">${cls.subject || 'All'}</strong></div>
              <div style="font-size:0.8125rem;color:var(--on-surface-muted);">Class Average: <strong style="color:${accent};">${avgPct.toFixed(1)}%</strong></div>
            </div>
            <button class="btn btn-primary btn-xs"
              onclick="window.app.handleUserMessage('Mark all students present in Class ${cls.class_name} Section ${cls.section} for today')">
              ✓ All Present
            </button>
          </div>

          <div class="insight-bubble">
            <p>${DashboardRenderer._attendanceInsight(avgPct, 'teacher', `Class ${cls.class_name}-${cls.section}`)}</p>
          </div>

          <div class="card-title" style="margin-top:16px;font-size:0.9375rem;">📋 Student Roster &amp; Attendance Marker</div>
          <div class="roster-card-list">
            ${roster.map(stu => `
              <div class="roster-item">
                <div class="roster-avatar-circle">${(stu.name || 'S').charAt(0)}</div>
                <div class="roster-student-info">
                  <div class="name">${stu.name}</div>
                  <div class="roll">Roll ${stu.roll_no} · ${(stu.attendance_percentage ?? 0).toFixed(0)}% attendance</div>
                </div>
                <select class="roster-status-dropdown" id="status-sel-${stu.student_id}">
                  <option value="present">Present</option>
                  <option value="absent">Absent</option>
                  <option value="late">Late</option>
                  <option value="excused">Excused</option>
                </select>
                <button class="btn btn-primary btn-xs"
                  onclick="(function(){
                    var sel = document.getElementById('status-sel-${stu.student_id}');
                    var st = sel ? sel.value : 'present';
                    window.app.handleUserMessage('Mark ${stu.name} (Roll ${stu.roll_no}) as ' + st + ' in Class ${cls.class_name} Section ${cls.section} for today');
                  })()">
                  Mark
                </button>
              </div>
            `).join('')}
            ${roster.length === 0 ? '<p style="color:var(--on-surface-muted);font-size:0.875rem;text-align:center;padding:16px;">No students assigned to this class</p>' : ''}
          </div>
        </div>
      `;
    });

    container.innerHTML = `
      <div class="card">
        <div class="card-header-strip" style="background:${accent};"></div>
        <div class="card-body">
          <div class="card-title">📚 My Assigned Classes</div>
          ${classes.length > 1 ? `<div style="display:flex;gap:8px;margin-bottom:16px;">${classTabsHtml}</div>` : ''}
          ${classContentHtml}
        </div>
      </div>
    `;

    container.querySelectorAll('[data-class-tab]').forEach(tab => {
      tab.addEventListener('click', () => {
        const idx = tab.dataset.classTab;
        container.querySelectorAll('[data-class-tab]').forEach(t => {
          t.style.background = '';
          t.style.color = '';
          t.style.borderColor = '';
        });
        tab.style.background = 'var(--teacher-light)';
        tab.style.color = accent;
        tab.style.borderColor = accent;

        container.querySelectorAll('.teacher-class-panel').forEach(p => p.classList.add('hidden'));
        document.getElementById(`teacher-panel-${idx}`)?.classList.remove('hidden');
      });
    });
  }

  // -------------------------------------------------------------------------
  // 4. PRINCIPAL DASHBOARD (Executive School Analytics & Alerts)
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
      <!-- Executive School Overview -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent};"></div>
        <div class="card-body">
          <div class="card-title">🏫 School Executive Overview</div>
          <div class="insight-bubble">
            <p>${DashboardRenderer._attendanceInsight(avgPct, 'principal')}</p>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px;">
            <div class="stat-metric-card">
              <div class="value" style="color:${accent};">${avgPct.toFixed(1)}%</div>
              <div class="label">School Average</div>
            </div>
            <div class="stat-metric-card">
              <div class="value">${totalStu}</div>
              <div class="label">Enrolled Students</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Class-wise Attendance & Low-Attendance Alerts -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent};"></div>
        <div class="card-body">
          <div class="card-title">📊 Class-wise Attendance Breakdown</div>
          <div class="principal-bar-list">
            ${classes.map(cls => {
              const pct = cls.attendance_percentage ?? 0;
              const isLow = pct < LOW_ATTENDANCE_THRESHOLD;
              return `
                <div class="principal-bar-item ${isLow ? 'low-att' : ''}">
                  <div class="meta">
                    <span class="class-lbl">Class ${cls.class_name}-${cls.section} ${isLow ? '⚠️ <span style="font-size:0.75rem;color:var(--status-absent);font-weight:700;">Low Attendance</span>' : ''}</span>
                    <span class="pct-val">${pct.toFixed(1)}%</span>
                  </div>
                  <div class="progress-track">
                    <div class="progress-fill ${isLow ? 'alert' : ''}" style="width:${pct}%;"></div>
                  </div>
                  <div style="font-size:0.75rem;color:var(--on-surface-muted);margin-top:4px;">${cls.student_count ?? '–'} students registered</div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </div>

      <!-- Pending Teacher Approvals List -->
      ${pendingApprovals.length > 0 ? `
        <div class="card">
          <div class="card-header-strip" style="background:#8f4e00;"></div>
          <div class="card-body">
            <div class="card-title" style="color:#8f4e00;">⏳ Pending Teacher Approvals (${pendingApprovals.length})</div>
            ${pendingApprovals.map(t => `
              <div class="roster-item" id="dash-appr-${t.user_id}" style="margin-bottom:8px;">
                <div class="roster-avatar-circle">📚</div>
                <div class="roster-student-info">
                  <div class="name">${t.name}</div>
                  <div class="roll">${t.email}</div>
                </div>
                <button class="btn btn-primary btn-xs"
                  onclick="window.app.approveTeacher('${t.user_id}').then(()=>{ document.getElementById('dash-appr-${t.user_id}')?.remove(); })">
                  Approve
                </button>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <!-- Recent Escalation Queue -->
      <div class="card">
        <div class="card-header-strip" style="background:${accent};"></div>
        <div class="card-body">
          <div class="card-title">📋 Recent Escalations Queue</div>
          ${escalations.length > 0 ? `
            <div style="display:flex;flex-direction:column;gap:10px;">
              ${escalations.map(e => `
                <div style="background:var(--surface-container-low);border:1px solid var(--border);border-radius:var(--r-lg);padding:12px 16px;">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
                    <div>
                      <div style="font-weight:700;font-size:0.875rem;color:var(--on-surface);">${e.user_name}</div>
                      <div style="font-size:0.75rem;color:var(--on-surface-muted);">Target: <strong>${e.target}</strong> · ${DashboardRenderer._fmtDate(e.created_at?.split('T')[0])}</div>
                      <div style="font-size:0.8125rem;color:var(--on-surface-variant);margin-top:4px;">${e.reason || '–'}</div>
                    </div>
                    <span class="chip ${e.status === 'confirmed' ? 'chip-present' : e.status === 'pending' ? 'chip-late' : 'chip-excused'}">${e.status}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          ` : '<p style="color:var(--on-surface-muted);font-size:0.875rem;text-align:center;padding:12px;">No active escalation tickets</p>'}
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
            hoverOffset: 3
          }]
        },
        options: {
          cutout: '74%',
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          animation: { duration: 600, easing: 'easeInOutQuart' }
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
    if (pct >= 95) return `✨ ${who} attendance is exceptional at <strong>${pct.toFixed(1)}%</strong>. Outstanding consistency!`;
    if (pct >= 85) return `👍 ${who} attendance is healthy at <strong>${pct.toFixed(1)}%</strong>. Consistent regular attendance observed.`;
    if (pct >= 75) return `📋 ${who} attendance stands at <strong>${pct.toFixed(1)}%</strong>. Regular attendance recommended.`;
    return `⚠️ ${who} attendance of <strong>${pct.toFixed(1)}%</strong> is below the 75% threshold. Attention is required.`;
  }
}

export class DashboardRenderer {
  static render(data, containerId, onAction) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const role = data.role;
    if (role === 'student') {
      this.renderStudent(data, container, onAction);
    } else if (role === 'parent') {
      this.renderParent(data, container, onAction);
    } else if (role === 'teacher') {
      this.renderTeacher(data, container, onAction);
    } else if (role === 'principal') {
      this.renderPrincipal(data, container, onAction);
    }
  }

  static renderStudent(data, container, onAction) {
    const att = data.attendance || {};
    const prof = data.student_profile || {};
    
    container.innerHTML = `
      <div style="margin-bottom: 16px;">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">Student Overview</h4>
        <p style="font-size: 0.8rem; color: var(--text-muted);">Class ${prof.class_name ?? '—'}-${prof.section ?? '—'} • Roll #${prof.roll_no ?? '—'}</p>
      </div>

      <div class="stat-summary-grid">
        <div class="stat-box">
          <div class="stat-number">${att.attendance_percentage !== undefined ? att.attendance_percentage + '%' : '—'}</div>
          <div class="stat-caption">Attendance</div>
        </div>
        <div class="stat-box">
          <div class="stat-number" style="color: var(--text-secondary);">${att.present_days !== undefined && att.total_school_days !== undefined ? `${att.present_days}/${att.total_school_days}` : '—'}</div>
          <div class="stat-caption">Days Present</div>
        </div>
      </div>

      <div style="margin-top: 18px;">
        <h5 style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Recent Attendance</h5>
        <div style="max-height: 180px; overflow-y: auto;">
          <table class="clean-table">
            <thead>
              <tr><th>Date</th><th>Status</th><th>Note</th></tr>
            </thead>
            <tbody>
              ${(data.recent_records && data.recent_records.length > 0) ? data.recent_records.slice(0, 5).map(r => `
                <tr>
                  <td>${r.date}</td>
                  <td><span class="status-tag ${r.status}">${r.status}</span></td>
                  <td style="color: var(--text-muted);">${r.remarks || '—'}</td>
                </tr>
              `).join('') : '<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">No records found</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>

      <div style="margin-top: 18px;">
        <button class="btn btn-secondary" style="width: 100%; font-size: 0.82rem;" id="btnStudentHelp">
          Request Teacher Assistance
        </button>
      </div>
    `;

    document.getElementById('btnStudentHelp')?.addEventListener('click', () => {
      onAction('chat_prompt', 'I need help connecting with my teacher regarding questions on my classes.');
    });
  }

  static renderParent(data, container, onAction) {
    const children = data.children || [];

    const updateView = (idx) => {
      const child = children[idx] || {};
      const att = child.summary || {};

      container.innerHTML = `
        <div style="margin-bottom: 14px;">
          <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">Parent Portal</h4>
          <p style="font-size: 0.8rem; color: var(--text-muted);">${data.parent_name ?? 'Parent'} (${children.length} linked children)</p>
        </div>

        <div style="display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;">
          ${children.map((c, i) => `
            <button class="btn ${i === idx ? 'btn-primary' : 'btn-secondary'}" style="padding: 4px 12px; font-size: 0.78rem;" id="childTab_${i}">
              ${c.name} (${c.class_name}-${c.section})
            </button>
          `).join('')}
        </div>

        <div class="stat-summary-grid">
          <div class="stat-box">
            <div class="stat-number">${att.attendance_percentage !== undefined ? att.attendance_percentage + '%' : '—'}</div>
            <div class="stat-caption">Attendance Rate</div>
          </div>
          <div class="stat-box">
            <div class="stat-number" style="color: var(--danger-text);">${att.absent_days ?? '—'}</div>
            <div class="stat-caption">Absences</div>
          </div>
        </div>

        <div style="margin-top: 16px;">
          <h5 style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Recent Records for ${child.name || 'Child'}</h5>
          <div style="max-height: 160px; overflow-y: auto;">
            <table class="clean-table">
              <thead>
                <tr><th>Date</th><th>Status</th><th>Note</th></tr>
              </thead>
              <tbody>
                ${(child.recent_records && child.recent_records.length > 0) ? child.recent_records.slice(0, 5).map(r => `
                  <tr>
                    <td>${r.date}</td>
                    <td><span class="status-tag ${r.status}">${r.status}</span></td>
                    <td style="color: var(--text-muted);">${r.remarks || '—'}</td>
                  </tr>
                `).join('') : '<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">No records found</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>

        <div style="margin-top: 16px;">
          <button class="btn btn-secondary" style="width: 100%; font-size: 0.82rem;" id="btnParentEscalate">
            Request Call with ${child.name || 'Child'}'s Teacher
          </button>
        </div>
      `;

      children.forEach((_, i) => {
        document.getElementById(`childTab_${i}`)?.addEventListener('click', () => updateView(i));
      });

      document.getElementById('btnParentEscalate')?.addEventListener('click', () => {
        onAction('chat_prompt', `I would like to speak with ${child.name}'s class teacher regarding attendance.`);
      });
    };

    if (children.length > 0) {
      updateView(0);
    } else {
      container.innerHTML = `<p style="color:var(--text-muted); font-size:0.85rem;">No linked children registered.</p>`;
    }
  }

  static renderTeacher(data, container, onAction) {
    const classes = data.assigned_classes || [];

    const updateView = (idx) => {
      const cls = classes[idx] || {};
      const roster = cls.analytics?.class_roster_summary || [];
      const avg = cls.analytics?.average_attendance_percentage;

      container.innerHTML = `
        <div style="margin-bottom: 14px;">
          <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">Teacher Portal</h4>
          <p style="font-size: 0.8rem; color: var(--text-muted);">${data.teacher_name ?? 'Teacher'} • Subject: ${cls.subject ?? 'Core'}</p>
        </div>

        <div style="display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;">
          ${classes.map((c, i) => `
            <button class="btn ${i === idx ? 'btn-primary' : 'btn-secondary'}" style="padding: 4px 12px; font-size: 0.78rem;" id="clsTab_${i}">
              Class ${c.class_name}-${c.section}
            </button>
          `).join('')}
        </div>

        <div class="stat-summary-grid">
          <div class="stat-box">
            <div class="stat-number">${avg !== undefined ? avg + '%' : '—'}</div>
            <div class="stat-caption">Class Average</div>
          </div>
          <div class="stat-box">
            <div class="stat-number" style="color: var(--text-secondary);">${roster.length}</div>
            <div class="stat-caption">Students</div>
          </div>
        </div>

        <div style="margin-top: 14px;">
          <h5 style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Class Roster</h5>
          <div style="max-height: 200px; overflow-y: auto;">
            <table class="clean-table">
              <thead>
                <tr><th>Roll</th><th>Student</th><th>Rate</th><th>Action</th></tr>
              </thead>
              <tbody>
                ${roster.map(s => `
                  <tr>
                    <td>#${s.roll_no}</td>
                    <td><strong>${s.name}</strong></td>
                    <td>${s.attendance_percentage}%</td>
                    <td>
                      <button class="btn btn-outline btn-mark-att" style="padding: 2px 8px; font-size: 0.72rem;" data-id="${s.student_id}" data-name="${s.name}">
                        Mark
                      </button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;

      classes.forEach((_, i) => {
        document.getElementById(`clsTab_${i}`)?.addEventListener('click', () => updateView(i));
      });

      document.querySelectorAll('.btn-mark-att').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const sName = e.currentTarget.getAttribute('data-name');
          onAction('chat_prompt', `Please mark ${sName} present for today's class.`);
        });
      });
    };

    if (classes.length > 0) {
      updateView(0);
    } else {
      container.innerHTML = `<p style="color:var(--text-muted); font-size:0.85rem;">No assigned classes registered.</p>`;
    }
  }

  static renderPrincipal(data, container, onAction) {
    const school = data.school_analytics || {};
    const breakdowns = school.class_wise_breakdown || [];
    const escalations = data.recent_escalations || [];

    container.innerHTML = `
      <div style="margin-bottom: 14px;">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary);">Executive Overview</h4>
        <p style="font-size: 0.8rem; color: var(--text-muted);">${data.principal_name ?? 'Dr. Sunita Sharma'} (Principal)</p>
      </div>

      <div class="stat-summary-grid">
        <div class="stat-box">
          <div class="stat-number">${school.school_average_attendance !== undefined ? school.school_average_attendance + '%' : '—'}</div>
          <div class="stat-caption">School Avg</div>
        </div>
        <div class="stat-box">
          <div class="stat-number" style="color: var(--text-secondary);">${school.total_enrolled_students ?? '—'}</div>
          <div class="stat-caption">Enrolled</div>
        </div>
      </div>

      <div style="margin-top: 14px;">
        <h5 style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Class Breakdown</h5>
        <div style="max-height: 130px; overflow-y: auto;">
          <table class="clean-table">
            <thead>
              <tr><th>Class</th><th>Students</th><th>Avg</th></tr>
            </thead>
            <tbody>
              ${breakdowns.map(b => `
                <tr>
                  <td>Class ${b.class_name}-${b.section}</td>
                  <td>${b.student_count}</td>
                  <td><strong>${b.attendance_percentage}%</strong></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <div style="margin-top: 16px;">
        <h5 style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Recent Escalations</h5>
        <div style="max-height: 110px; overflow-y: auto;">
          <table class="clean-table">
            <thead>
              <tr><th>From</th><th>Target</th><th>Status</th></tr>
            </thead>
            <tbody>
              ${(escalations && escalations.length > 0) ? escalations.slice(0, 4).map(e => `
                <tr>
                  <td>${e.user_name}</td>
                  <td>${e.target}</td>
                  <td><span class="status-tag ${e.status}">${e.status}</span></td>
                </tr>
              `).join('') : '<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">No escalations logged</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }
}

// Role-based avatar persona color palettes
const AVATAR_PERSONAS = {
  student: {
    label: 'Student',
    background: '#dbeafe',  // light blue
    face: '#fef3c7',        // warm skin
    hair: '#2563eb',        // blue cap
    blush: 'rgba(251,113,133,0.40)',
    mouth: '#e11d48',
    statusIdleText: 'Ready to help you learn!'
  },
  parent: {
    label: 'Parent',
    background: '#fef3c7',  // warm amber
    face: '#fed7aa',        // slightly deeper skin
    hair: '#92400e',        // brown hair
    blush: 'rgba(251,146,60,0.35)',
    mouth: '#b45309',
    statusIdleText: 'Here for your family\'s needs'
  },
  teacher: {
    label: 'Teacher',
    background: '#d1fae5',  // soft green
    face: '#fef3c7',
    hair: '#1e293b',        // formal dark
    blush: 'rgba(52,211,153,0.30)',
    mouth: '#065f46',
    statusIdleText: 'Ready to assist your class'
  },
  principal: {
    label: 'Principal',
    background: '#ede9fe',  // soft indigo
    face: '#fef3c7',
    hair: '#3b0764',        // authoritative dark purple
    blush: 'rgba(139,92,246,0.25)',
    mouth: '#4c1d95',
    statusIdleText: 'School analytics at your command'
  }
};

export class AvatarRenderer {
  constructor(canvasId, role = 'student') {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.state = 'idle'; // idle, listening, thinking, speaking
    this.currentViseme = 'rest';
    this.blinkProgress = 0;
    this.isBlinking = false;
    this.animationFrameId = null;
    this.persona = AVATAR_PERSONAS[role] || AVATAR_PERSONAS.student;

    if (this.canvas) {
      this.initBlinkTimer();
      this.startLoop();
    }
  }

  /** Call this whenever the user role changes after login */
  setPersona(role) {
    this.persona = AVATAR_PERSONAS[role] || AVATAR_PERSONAS.student;
    const indicator = document.getElementById('assistantStatusIndicator');
    if (indicator && this.state === 'idle') {
      indicator.innerHTML = `<span class="pulse-dot"></span> ${this.persona.statusIdleText}`;
    }
  }

  initBlinkTimer() {
    const scheduleBlink = () => {
      const delay = 3000 + Math.random() * 3000;
      setTimeout(() => {
        this.triggerBlink();
        scheduleBlink();
      }, delay);
    };
    scheduleBlink();
  }

  triggerBlink() {
    this.isBlinking = true;
    let progress = 0;
    const interval = setInterval(() => {
      progress += 0.2;
      this.blinkProgress = Math.sin(progress * Math.PI);
      if (progress >= 1) {
        clearInterval(interval);
        this.isBlinking = false;
        this.blinkProgress = 0;
      }
    }, 25);
  }

  setState(newState) {
    this.state = newState;
    const indicator = document.getElementById('assistantStatusIndicator');
    if (indicator) {
      if (newState === 'listening') {
        indicator.innerHTML = '<span class="pulse-dot" style="background:#ef4444"></span> Listening...';
      } else if (newState === 'thinking') {
        indicator.innerHTML = '<span class="pulse-dot" style="background:#f59e0b"></span> Thinking...';
      } else if (newState === 'speaking') {
        indicator.innerHTML = '<span class="pulse-dot" style="background:#2563eb"></span> Speaking...';
      } else {
        const idleText = this.persona ? this.persona.statusIdleText : 'Ready to assist';
        indicator.innerHTML = `<span class="pulse-dot"></span> ${idleText}`;
      }
    }
  }

  playVisemes(visemeList, durationSeconds = 2.5, onComplete = null) {
    this.setState('speaking');
    const startTime = performance.now();

    const checkViseme = () => {
      const elapsedMs = performance.now() - startTime;
      if (elapsedMs >= durationSeconds * 1000) {
        this.currentViseme = 'rest';
        this.setState('idle');
        if (onComplete) onComplete();
        return;
      }

      let active = 'rest';
      if (visemeList && visemeList.length > 0) {
        for (let i = 0; i < visemeList.length; i++) {
          if (elapsedMs >= visemeList[i].time_ms) {
            active = visemeList[i].viseme;
          } else {
            break;
          }
        }
      } else {
        const shapes = ['aa', 'ee', 'oo', 'rest'];
        active = shapes[Math.floor((elapsedMs / 180) % shapes.length)];
      }

      this.currentViseme = active;
      requestAnimationFrame(checkViseme);
    };

    requestAnimationFrame(checkViseme);
  }

  startLoop() {
    const render = () => {
      this.draw();
      this.animationFrameId = requestAnimationFrame(render);
    };
    render();
  }

  draw() {
    if (!this.ctx || !this.canvas) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const cx = w / 2;
    const cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    const p = this.persona || AVATAR_PERSONAS.student;

    // Role-specific circular background
    ctx.fillStyle = p.background;
    ctx.beginPath();
    ctx.arc(cx, cy, 30, 0, Math.PI * 2);
    ctx.fill();

    // Friendly Face Base
    ctx.fillStyle = p.face;
    ctx.beginPath();
    ctx.arc(cx, cy, 20, 0, Math.PI * 2);
    ctx.fill();

    // Role-specific Hair / Cap
    ctx.fillStyle = p.hair;
    ctx.beginPath();
    ctx.arc(cx, cy - 10, 16, Math.PI * 0.9, Math.PI * 2.1);
    ctx.fill();

    // Eyes
    const eyeSpacing = 7;
    const eyeY = cy - 2;
    const eyeH = Math.max(0.5, 3.5 * (1 - this.blinkProgress));

    ctx.fillStyle = '#1e293b';
    ctx.beginPath();
    ctx.ellipse(cx - eyeSpacing, eyeY, 2.5, eyeH, 0, 0, Math.PI * 2);
    ctx.ellipse(cx + eyeSpacing, eyeY, 2.5, eyeH, 0, 0, Math.PI * 2);
    ctx.fill();

    // Soft Blush (role-tinted)
    ctx.fillStyle = p.blush;
    ctx.beginPath();
    ctx.arc(cx - 10, cy + 5, 3, 0, Math.PI * 2);
    ctx.arc(cx + 10, cy + 5, 3, 0, Math.PI * 2);
    ctx.fill();

    // Mouth Viseme
    const mouthY = cy + 9;
    ctx.strokeStyle = p.mouth;
    ctx.fillStyle = p.mouth;
    ctx.lineWidth = 1.5;

    ctx.beginPath();
    if (this.currentViseme === 'rest') {
      ctx.arc(cx, mouthY - 2, 4, 0.2 * Math.PI, 0.8 * Math.PI, false);
      ctx.stroke();
    } else if (this.currentViseme === 'aa') {
      ctx.ellipse(cx, mouthY, 4, 5, 0, 0, Math.PI * 2);
      ctx.fill();
    } else if (this.currentViseme === 'ee') {
      ctx.ellipse(cx, mouthY - 1, 6, 2.5, 0, 0, Math.PI * 2);
      ctx.fill();
    } else if (this.currentViseme === 'oo') {
      ctx.ellipse(cx, mouthY, 3, 3.5, 0, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.ellipse(cx, mouthY - 1, 5, 2, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

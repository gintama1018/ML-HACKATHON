// Role-based avatar persona color palettes (strictly matched to DESIGN.MD Warm Academic Humanism)
const AVATAR_PERSONAS = {
  student: {
    label: 'Student',
    accent: '#FF9F43',
    background: '#fff3e0', // soft warm orange tint
    face: '#fef3c7',        // warm skin
    hair: '#e67e22',        // warm orange cap/hair
    blush: 'rgba(255,159,67,0.40)',
    mouth: '#d35400',
    statusIdleText: 'Ready to help you learn!'
  },
  parent: {
    label: 'Parent',
    accent: '#58B19F',
    background: '#e6f7f3', // soft green tint
    face: '#fed7aa',        // slightly deeper skin
    hair: '#2c7a6b',        // soft deep green/brown
    blush: 'rgba(88,177,159,0.35)',
    mouth: '#218272',
    statusIdleText: 'Here for your family\'s needs'
  },
  teacher: {
    label: 'Teacher',
    accent: '#54A0FF',
    background: '#edf5ff', // approachable soft blue tint
    face: '#fef3c7',
    hair: '#2e66b8',        // professional navy-blue
    blush: 'rgba(84,160,255,0.30)',
    mouth: '#1b4f9b',
    statusIdleText: 'Ready to assist your class'
  },
  principal: {
    label: 'Principal',
    accent: '#2C3E50',
    background: '#f1eee7', // formal warm neutral
    face: '#fef3c7',
    hair: '#2C3E50',        // formal dark navy
    blush: 'rgba(44,62,80,0.25)',
    mouth: '#1c2833',
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
      const delay = 3000 + Math.random() * 3500;
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

    // Outer subtle border ring
    ctx.strokeStyle = p.accent;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, cy, 25, 0, Math.PI * 2);
    ctx.stroke();

    // Role-specific circular background
    ctx.fillStyle = p.background;
    ctx.beginPath();
    ctx.arc(cx, cy, 24, 0, Math.PI * 2);
    ctx.fill();

    // Friendly Face Base
    ctx.fillStyle = p.face;
    ctx.beginPath();
    ctx.arc(cx, cy + 1, 16, 0, Math.PI * 2);
    ctx.fill();

    // Role-specific Hair / Cap
    ctx.fillStyle = p.hair;
    ctx.beginPath();
    ctx.arc(cx, cy - 7, 13, Math.PI * 0.9, Math.PI * 2.1);
    ctx.fill();

    // Eyes (with gentle blink curve)
    const eyeSpacing = 6;
    const eyeY = cy;
    const eyeH = Math.max(0.5, 3 * (1 - this.blinkProgress));

    ctx.fillStyle = '#2C3E50';
    ctx.beginPath();
    ctx.ellipse(cx - eyeSpacing, eyeY, 2, eyeH, 0, 0, Math.PI * 2);
    ctx.ellipse(cx + eyeSpacing, eyeY, 2, eyeH, 0, 0, Math.PI * 2);
    ctx.fill();

    // Soft Blush (warm and empathetic)
    ctx.fillStyle = p.blush;
    ctx.beginPath();
    ctx.arc(cx - 8, cy + 6, 2.5, 0, Math.PI * 2);
    ctx.arc(cx + 8, cy + 6, 2.5, 0, Math.PI * 2);
    ctx.fill();

    // Mouth Viseme / Friendly smile
    const mouthY = cy + 9;
    ctx.strokeStyle = p.mouth;
    ctx.fillStyle = p.mouth;
    ctx.lineWidth = 1.6;
    ctx.lineCap = 'round';

    ctx.beginPath();
    if (this.currentViseme === 'rest') {
      ctx.arc(cx, mouthY - 2, 3.5, 0.2 * Math.PI, 0.8 * Math.PI, false);
      ctx.stroke();
    } else if (this.currentViseme === 'aa') {
      ctx.ellipse(cx, mouthY, 3.5, 4.5, 0, 0, Math.PI * 2);
      ctx.fill();
    } else if (this.currentViseme === 'ee') {
      ctx.ellipse(cx, mouthY - 1, 5, 2, 0, 0, Math.PI * 2);
      ctx.fill();
    } else if (this.currentViseme === 'oo') {
      ctx.ellipse(cx, mouthY, 2.5, 3, 0, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.ellipse(cx, mouthY - 1, 4, 1.8, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

export class AvatarRenderer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.state = 'idle'; // idle, listening, thinking, speaking
    this.currentViseme = 'rest';
    this.blinkProgress = 0;
    this.isBlinking = false;
    this.animationFrameId = null;

    if (this.canvas) {
      this.initBlinkTimer();
      this.startLoop();
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
        indicator.innerHTML = '<span class="pulse-dot"></span> Ready to assist';
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

    // Warm soft circular background
    ctx.fillStyle = '#eff6ff';
    ctx.beginPath();
    ctx.arc(cx, cy, 30, 0, Math.PI * 2);
    ctx.fill();

    // Friendly Face Base
    ctx.fillStyle = '#fef3c7'; // soft warm tone
    ctx.beginPath();
    ctx.arc(cx, cy, 20, 0, Math.PI * 2);
    ctx.fill();

    // Friendly Hair / Cap
    ctx.fillStyle = '#334155';
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

    // Soft Blush
    ctx.fillStyle = 'rgba(251, 113, 133, 0.4)';
    ctx.beginPath();
    ctx.arc(cx - 10, cy + 5, 3, 0, Math.PI * 2);
    ctx.arc(cx + 10, cy + 5, 3, 0, Math.PI * 2);
    ctx.fill();

    // Mouth Viseme
    const mouthY = cy + 9;
    ctx.strokeStyle = '#e11d48';
    ctx.fillStyle = '#e11d48';
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

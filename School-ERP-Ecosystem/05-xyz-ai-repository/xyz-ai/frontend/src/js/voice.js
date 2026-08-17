export class VoiceController {
  constructor(avatarRenderer) {
    this.avatar = avatarRenderer;
    this.recognition = null;
    this.isRecording = false;
    this.initSpeechRecognition();
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
    }
  }

  startListening(onResult, onError, language = 'en-IN') {
    if (!this.recognition) {
      // Fallback for browsers without Web Speech API
      const simulatedText = prompt("Microphone simulation: Enter your spoken query:", "What is my attendance percentage?");
      if (simulatedText) {
        onResult(simulatedText, 0.95);
      } else {
        if (onError) onError("Voice recording cancelled");
      }
      return;
    }

    this.isRecording = true;
    this.avatar.setState('listening');
    this.recognition.lang = language;

    this.recognition.onresult = (event) => {
      this.isRecording = false;
      this.avatar.setState('idle');
      const transcript = event.results[0][0].transcript;
      const confidence = event.results[0][0].confidence || 0.95;
      onResult(transcript, confidence);
    };

    this.recognition.onerror = (event) => {
      this.isRecording = false;
      this.avatar.setState('idle');
      if (onError) onError(event.error);
    };

    this.recognition.onend = () => {
      this.isRecording = false;
      this.avatar.setState('idle');
    };

    try {
      this.recognition.start();
    } catch (e) {
      console.warn("Speech recognition already running or error:", e);
    }
  }

  stopListening() {
    if (this.recognition && this.isRecording) {
      this.recognition.stop();
      this.isRecording = false;
      this.avatar.setState('idle');
    }
  }

  speak(text, visemes = [], durationSeconds = 3.0, language = 'en', onComplete = null) {
    // 1. Trigger Avatar Viseme Mouth Shapes
    this.avatar.playVisemes(visemes, durationSeconds, onComplete);

    // 2. Play Web Speech Synthesis
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Stop any pending speech
      const cleanText = text.replace(/[*#•_]/g, ''); // Clean markdown formatting
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.0;
      utterance.pitch = 1.05;
      
      const langCodes = {
        'en': 'en-IN',
        'hi': 'hi-IN',
        'ta': 'ta-IN',
        'bn': 'bn-IN'
      };
      utterance.lang = langCodes[language] || 'en-IN';

      window.speechSynthesis.speak(utterance);
    }
  }
}

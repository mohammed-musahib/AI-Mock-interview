/**
 * Interview Execution - State, Voice Input/Output, Navigation & Submission
 */

document.addEventListener('DOMContentLoaded', async () => {
  let questions = [];
  let currentIndex = 0;
  let answers = {};
  let recognition = null;
  let isRecording = false;
  let isSpeaking = false;
  let currentDomain = '';

  // DOM Elements
  const domainText = document.getElementById('header-domain-text');
  const qIndexText = document.getElementById('current-q-index');
  const progressBar = document.getElementById('progress-bar-fill');
  const topicBadge = document.getElementById('question-topic-badge');
  const questionText = document.getElementById('question-text');
  const speakBtn = document.getElementById('speak-question-btn');
  const speakerIcon = document.getElementById('speaker-icon');
  const speakerLabel = document.getElementById('speaker-label');

  const mcqContainer = document.getElementById('mcq-container');
  const optionsList = document.getElementById('options-list');

  const theoryContainer = document.getElementById('theory-container');
  const theoryInput = document.getElementById('theory-answer-input');
  const micBtn = document.getElementById('mic-toggle-btn');
  const micIcon = document.getElementById('mic-icon');
  const micLabel = document.getElementById('mic-label');
  const voiceStatus = document.getElementById('voice-status');
  const voicePulseDot = document.getElementById('voice-pulse-dot');
  const voiceStatusText = document.getElementById('voice-status-text');

  const prevBtn = document.getElementById('prev-question-btn');
  const nextBtn = document.getElementById('next-question-btn');
  const submitBtn = document.getElementById('submit-interview-btn');

  const confirmModal = document.getElementById('confirm-modal');
  const cancelSubmitBtn = document.getElementById('cancel-submit-btn');
  const confirmSubmitBtn = document.getElementById('confirm-submit-btn');
  const submitSummaryMsg = document.getElementById('submit-summary-msg');

  // Load Session State
  try {
    const res = await fetch('/api/session-data');
    if (!res.ok) {
      window.location.href = '/setup';
      return;
    }
    const data = await res.json();
    if (!data.has_interview || !data.questions || data.questions.length !== 10) {
      window.location.href = '/setup';
      return;
    }

    questions = data.questions;
    currentDomain = data.selected_domain || 'Technical Domain';
    domainText.textContent = `Domain: ${currentDomain}`;

    // Initialize Speech Recognition if supported
    initSpeechRecognition();

    // Render First Question
    renderCurrentQuestion();
  } catch (err) {
    console.error('Failed to load interview session:', err);
    window.location.href = '/setup';
  }

  // Render Question at currentIndex
  function renderCurrentQuestion() {
    stopSpeaking();
    stopRecording();

    const q = questions[currentIndex];
    qIndexText.textContent = currentIndex + 1;
    topicBadge.textContent = q.topic || currentDomain;
    questionText.textContent = q.question;

    // Progress bar update
    const progressPercent = ((currentIndex + 1) / questions.length) * 100;
    progressBar.style.width = `${progressPercent}%`;

    // Render Answer UI based on type
    if (q.type === 'mcq') {
      theoryContainer.style.display = 'none';
      mcqContainer.style.display = 'block';
      renderMcqOptions(q);
    } else {
      mcqContainer.style.display = 'none';
      theoryContainer.style.display = 'block';
      theoryInput.value = answers[q.id] || '';
    }

    // Navigation buttons state
    prevBtn.disabled = currentIndex === 0;

    if (currentIndex === questions.length - 1) {
      nextBtn.style.display = 'none';
      submitBtn.style.display = 'inline-flex';
    } else {
      nextBtn.style.display = 'inline-flex';
      submitBtn.style.display = 'none';
    }
  }

  // Render Options for MCQ
  function renderMcqOptions(q) {
    optionsList.innerHTML = '';
    const currentAnswer = answers[q.id] || '';

    q.options.forEach((optText) => {
      // Extract choice letter ('A', 'B', 'C', 'D')
      const match = optText.match(/^([A-Da-d])[\.\:\)]/);
      const choiceLetter = match ? match[1].toUpperCase() : optText.charAt(0).toUpperCase();

      const card = document.createElement('div');
      card.className = `option-card ${currentAnswer === choiceLetter ? 'selected' : ''}`;
      card.setAttribute('tabindex', '0');
      card.setAttribute('role', 'radio');
      card.setAttribute('aria-checked', currentAnswer === choiceLetter ? 'true' : 'false');

      card.innerHTML = `
        <div class="option-indicator">${choiceLetter}</div>
        <div class="option-text">${optText}</div>
      `;

      card.addEventListener('click', () => {
        answers[q.id] = choiceLetter;
        document.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
      });

      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          card.click();
        }
      });

      optionsList.appendChild(card);
    });
  }

  // Save Theory Input changes in real time
  theoryInput.addEventListener('input', () => {
    const q = questions[currentIndex];
    answers[q.id] = theoryInput.value;
  });

  // Navigation Click Handlers
  prevBtn.addEventListener('click', () => {
    if (currentIndex > 0) {
      currentIndex--;
      renderCurrentQuestion();
    }
  });

  nextBtn.addEventListener('click', () => {
    if (currentIndex < questions.length - 1) {
      currentIndex++;
      renderCurrentQuestion();
    }
  });

  // Speech Synthesis (Text to Speech - Voice Output)
  speakBtn.addEventListener('click', () => {
    if (!('speechSynthesis' in window)) {
      showToast('Voice output is not supported in this browser.', 'error');
      return;
    }

    if (isSpeaking) {
      stopSpeaking();
    } else {
      playSpeaking();
    }
  });

  function playSpeaking() {
    stopSpeaking();
    const q = questions[currentIndex];
    let textToSpeak = q.question;

    if (q.type === 'mcq' && q.options) {
      textToSpeak += '. Options are: ' + q.options.join(', ');
    }

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      isSpeaking = true;
      speakerIcon.textContent = '⏹️';
      speakerLabel.textContent = 'Stop Audio';
    };

    utterance.onend = () => {
      stopSpeaking();
    };

    utterance.onerror = () => {
      stopSpeaking();
    };

    window.speechSynthesis.speak(utterance);
  }

  function stopSpeaking() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    isSpeaking = false;
    if (speakerIcon) speakerIcon.textContent = '🔊';
    if (speakerLabel) speakerLabel.textContent = 'Read Question';
  }

  // Web Speech API (Voice Recognition - Voice Input)
  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      micBtn.addEventListener('click', () => {
        showToast('Voice input is not supported in this browser. You can continue using text input.', 'info');
      });
      voiceStatusText.textContent = 'Voice input unavailable in this browser';
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isRecording = true;
      micIcon.textContent = '⏹️';
      micLabel.textContent = 'Stop Voice Recording';
      voiceStatus.classList.add('listening');
      voicePulseDot.style.display = 'inline-block';
      voiceStatusText.textContent = 'Listening... Speak your technical answer.';
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + ' ';
        }
      }
      if (finalTranscript) {
        const q = questions[currentIndex];
        const existing = theoryInput.value.trim();
        theoryInput.value = existing ? `${existing} ${finalTranscript.trim()}` : finalTranscript.trim();
        answers[q.id] = theoryInput.value;
      }
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      stopRecording();
      if (event.error === 'not-allowed') {
        showToast('Microphone access was denied. Please allow microphone permissions.', 'error');
      }
    };

    recognition.onend = () => {
      stopRecording();
    };

    micBtn.addEventListener('click', () => {
      if (isRecording) {
        stopRecording();
      } else {
        startRecording();
      }
    });
  }

  function startRecording() {
    if (!recognition) return;
    try {
      recognition.start();
    } catch (e) {
      console.warn('Recognition start error:', e);
    }
  }

  function stopRecording() {
    if (recognition && isRecording) {
      try {
        recognition.stop();
      } catch (e) {}
    }
    isRecording = false;
    if (micIcon) micIcon.textContent = '🎤';
    if (micLabel) micLabel.textContent = 'Start Voice Recording';
    if (voiceStatus) voiceStatus.classList.remove('listening');
    if (voicePulseDot) voicePulseDot.style.display = 'none';
    if (voiceStatusText) voiceStatusText.textContent = 'Microphone ready';
  }

  // Submit Interview Flow
  submitBtn.addEventListener('click', () => {
    // Check answered count
    let answeredCount = 0;
    questions.forEach(q => {
      if (answers[q.id] && answers[q.id].trim().length > 0) {
        answeredCount++;
      }
    });

    submitSummaryMsg.textContent = `You have answered ${answeredCount} of 10 questions. Are you ready to submit your answers for evaluation?`;
    confirmModal.style.display = 'flex';
  });

  cancelSubmitBtn.addEventListener('click', () => {
    confirmModal.style.display = 'none';
  });

  confirmSubmitBtn.addEventListener('click', async () => {
    confirmModal.style.display = 'none';
    stopSpeaking();
    stopRecording();

    showLoading(
      'Evaluating Your Answers...',
      'Google Gemini is assessing technical depth, correctness, and generating your performance diagnostic.'
    );

    try {
      const response = await fetch('/api/evaluate-interview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers })
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        hideLoading();
        showToast(data.error || 'Evaluation failed. Please try again.', 'error');
        return;
      }

      // Redirect to results dashboard
      window.location.href = '/results';
    } catch (err) {
      hideLoading();
      showToast('Connection error during evaluation. Please try again.', 'error');
      console.error(err);
    }
  });
});

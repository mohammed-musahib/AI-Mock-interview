/**
 * Setup Screen Logic - Resume Processing & Domain Selection
 */

document.addEventListener('DOMContentLoaded', async () => {
  let isResumeUploaded = false;
  let selectedDomain = '';

  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('resume-file-input');
  const uploadedBanner = document.getElementById('uploaded-file-banner');
  const uploadedFilename = document.getElementById('uploaded-filename');
  const uploadedMeta = document.getElementById('uploaded-meta');
  const removeFileBtn = document.getElementById('remove-file-btn');
  const skillsWrap = document.getElementById('skills-tags-wrap');
  const skillsList = document.getElementById('skills-tags-list');
  const domainCards = document.querySelectorAll('.domain-card');
  const startBtn = document.getElementById('start-interview-btn');
  const statusLabel = document.getElementById('setup-status-label');

  // Check if session already has state
  try {
    const res = await fetch('/api/session-data');
    if (res.ok) {
      const data = await res.json();
      if (data.has_resume) {
        isResumeUploaded = true;
        uploadedFilename.textContent = data.resume_filename || 'Uploaded Resume';
        uploadedMeta.textContent = 'Active in current session';
        uploadedBanner.style.display = 'flex';
        dropzone.style.display = 'none';

        if (data.detected_skills && data.detected_skills.length > 0) {
          renderSkills(data.detected_skills);
        }
      }
      if (data.selected_domain) {
        selectDomain(data.selected_domain);
      }
      updateStartButtonState();
    }
  } catch (err) {
    console.warn('Could not restore session state:', err);
  }

  // Dropzone Events
  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  // Remove / Replace Resume
  removeFileBtn.addEventListener('click', () => {
    isResumeUploaded = false;
    fileInput.value = '';
    uploadedBanner.style.display = 'none';
    skillsWrap.style.display = 'none';
    skillsList.innerHTML = '';
    dropzone.style.display = 'block';
    updateStartButtonState();
    showToast('Resume removed. Please upload another file.', 'info');
  });

  // Domain Selection Events
  domainCards.forEach(card => {
    card.addEventListener('click', () => {
      const domain = card.getAttribute('data-domain');
      selectDomain(domain);
    });

    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const domain = card.getAttribute('data-domain');
        selectDomain(domain);
      }
    });
  });

  function selectDomain(domain) {
    selectedDomain = domain;
    domainCards.forEach(c => {
      if (c.getAttribute('data-domain') === domain) {
        c.classList.add('selected');
        c.querySelector('.domain-select-btn').textContent = 'Selected ✓';
      } else {
        c.classList.remove('selected');
        c.querySelector('.domain-select-btn').textContent = 'Select Domain';
      }
    });
    updateStartButtonState();
  }

  // Upload Handler
  async function handleFileUpload(file) {
    const validExtensions = ['pdf', 'docx', 'txt'];
    const ext = file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
      showToast('Unsupported file type. Please upload a PDF, DOCX, or TXT file.', 'error');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      showToast('File size exceeds the 10 MB limit.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('resume', file);

    showLoading('Analyzing Resume...', 'Extracting technical background, skills, and projects.');

    try {
      const response = await fetch('/api/upload-resume', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      hideLoading();

      if (!response.ok || !data.success) {
        showToast(data.error || 'Failed to process resume.', 'error');
        return;
      }

      isResumeUploaded = true;
      uploadedFilename.textContent = data.filename;
      uploadedMeta.textContent = `${data.word_count} words analyzed`;
      uploadedBanner.style.display = 'flex';
      dropzone.style.display = 'none';

      if (data.skills && data.skills.length > 0) {
        renderSkills(data.skills);
      }

      showToast('Resume parsed successfully!', 'success');
      updateStartButtonState();
    } catch (err) {
      hideLoading();
      showToast('Connection error while uploading resume. Please try again.', 'error');
      console.error(err);
    }
  }

  function renderSkills(skills) {
    skillsList.innerHTML = '';
    skills.forEach(skill => {
      const tag = document.createElement('span');
      tag.className = 'skill-tag';
      tag.textContent = skill;
      skillsList.appendChild(tag);
    });
    skillsWrap.style.display = 'block';
  }

  function updateStartButtonState() {
    if (isResumeUploaded && selectedDomain) {
      startBtn.disabled = false;
      statusLabel.textContent = `Ready! Selected domain: ${selectedDomain}. Click below to begin.`;
      statusLabel.style.color = 'var(--accent-cyan)';
    } else if (!isResumeUploaded && selectedDomain) {
      startBtn.disabled = true;
      statusLabel.textContent = 'Please upload your resume to continue.';
      statusLabel.style.color = 'var(--text-muted)';
    } else if (isResumeUploaded && !selectedDomain) {
      startBtn.disabled = true;
      statusLabel.textContent = 'Please select an interview domain above.';
      statusLabel.style.color = 'var(--text-muted)';
    } else {
      startBtn.disabled = true;
      statusLabel.textContent = 'Please upload your resume and select a domain to proceed.';
      statusLabel.style.color = 'var(--text-muted)';
    }
  }

  // Start Interview Click Action
  startBtn.addEventListener('click', async () => {
    if (!isResumeUploaded || !selectedDomain) return;

    startBtn.disabled = true;
    showLoading(
      'Generating Interview Questions...',
      `AI is generating 10 tailored questions for ${selectedDomain} based on your resume.`
    );

    try {
      const response = await fetch('/api/generate-interview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: selectedDomain })
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        hideLoading();
        startBtn.disabled = false;
        showToast(data.error || 'Failed to generate interview. Please retry.', 'error');
        return;
      }

      // Smooth transition to interview
      window.location.href = '/interview';
    } catch (err) {
      hideLoading();
      startBtn.disabled = false;
      showToast('Network error while preparing interview. Please try again.', 'error');
      console.error(err);
    }
  });
});

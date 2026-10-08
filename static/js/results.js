/**
 * Results & Diagnostic Dashboard - Score Animation, Report & Transcript Breakdown
 */

document.addEventListener('DOMContentLoaded', async () => {
  const domainSubtitle = document.getElementById('results-domain-subtitle');
  const tierBadge = document.getElementById('tier-badge');
  const finalScoreVal = document.getElementById('final-score-val');
  const circleProgressBar = document.getElementById('circle-progress-bar');
  const mcqScoreVal = document.getElementById('mcq-score-val');
  const theoryScoreVal = document.getElementById('theory-score-val');
  const readinessVal = document.getElementById('readiness-level-val');

  const strengthsList = document.getElementById('strengths-list');
  const weaknessesList = document.getElementById('weaknesses-list');
  const improvementsList = document.getElementById('improvements-list');
  const topicsList = document.getElementById('topics-list');
  const reviewsContainer = document.getElementById('reviews-container');

  const retakeBtn = document.getElementById('retake-interview-btn');
  const printBtn = document.getElementById('print-report-btn');

  try {
    const res = await fetch('/api/session-data');
    if (!res.ok) {
      window.location.href = '/setup';
      return;
    }

    const data = await res.json();
    if (!data.has_results || !data.evaluation_results) {
      window.location.href = '/setup';
      return;
    }

    const results = data.evaluation_results;
    const domain = data.selected_domain || 'Technical Domain';

    domainSubtitle.textContent = `Comprehensive evaluation for ${domain} (${data.resume_filename || 'Candidate Resume'}).`;

    // 1. Final Score & Circular Progress
    const finalScore = parseFloat(results.final_score).toFixed(1);
    const percentage = results.overall_percentage || (finalScore * 10);
    animateScore(finalScore, percentage);

    // 2. Performance Tier Badge
    const tier = results.performance_tier || 'Good';
    tierBadge.textContent = tier;
    setTierBadgeClass(tier);

    // 3. Sub-scores
    mcqScoreVal.textContent = `${results.mcq_score.correct} / ${results.mcq_score.total}`;
    theoryScoreVal.textContent = `${parseFloat(results.theory_score.points).toFixed(1)} / 5.0`;

    // 4. Performance Diagnostic
    const report = results.report || {};
    readinessVal.textContent = report.interview_readiness || 'Competent';

    renderList(strengthsList, report.strengths, 'No specific strengths flagged.');
    renderList(weaknessesList, report.weaknesses, 'No critical weaknesses observed.');
    renderList(improvementsList, report.areas_to_improve, 'Continue refining domain breadth.');
    renderList(topicsList, report.recommended_topics, 'Review foundational core documentation.');

    // 5. Question Reviews
    renderReviews(results.reviews);
  } catch (err) {
    console.error('Failed to load results:', err);
    window.location.href = '/setup';
  }

  function animateScore(targetScore, percentage) {
    let current = 0.0;
    const increment = targetScore / 30;
    const timer = setInterval(() => {
      current += increment;
      if (current >= targetScore) {
        current = targetScore;
        clearInterval(timer);
      }
      finalScoreVal.textContent = parseFloat(current).toFixed(1);
    }, 30);

    setTimeout(() => {
      circleProgressBar.setAttribute('stroke-dasharray', `${percentage}, 100`);
    }, 100);
  }

  function setTierBadgeClass(tier) {
    tierBadge.className = 'tier-badge';
    const norm = tier.toLowerCase();
    if (norm.includes('excellent')) tierBadge.classList.add('tier-excellent');
    else if (norm.includes('very good')) tierBadge.classList.add('tier-very-good');
    else if (norm.includes('good')) tierBadge.classList.add('tier-good');
    else if (norm.includes('needs improvement')) tierBadge.classList.add('tier-needs-improvement');
    else tierBadge.classList.add('tier-beginner');
  }

  function renderList(container, items, defaultText) {
    container.innerHTML = '';
    if (!items || items.length === 0) {
      container.innerHTML = `<li class="report-item">${defaultText}</li>`;
      return;
    }
    items.forEach(item => {
      const li = document.createElement('li');
      li.className = 'report-item';
      li.textContent = item;
      container.appendChild(li);
    });
  }

  function renderReviews(reviews) {
    reviewsContainer.innerHTML = '';
    if (!reviews) return;

    reviews.forEach(r => {
      const card = document.createElement('div');
      card.className = 'review-item';

      if (r.type === 'mcq') {
        const isCorrect = r.is_correct;
        const statusClass = isCorrect ? 'review-badge-correct' : 'review-badge-incorrect';
        const statusText = isCorrect ? '✓ Correct (+1 pt)' : '✗ Incorrect (0 pt)';

        card.innerHTML = `
          <div class="review-item-header">
            <div>
              <span class="topic-badge" style="margin-right: 0.5rem;">Q${r.id}</span>
              <span style="font-size: 0.85rem; color: var(--text-dim);">${r.topic}</span>
            </div>
            <span class="${statusClass}">${statusText}</span>
          </div>
          <div class="review-question">${r.question}</div>
          <div class="review-answer-box">
            <div style="margin-bottom: 0.25rem;">
              <strong>Your Selected Choice:</strong> 
              <span style="color: ${isCorrect ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">${r.user_answer || 'No answer selected'}</span>
            </div>
            <div>
              <strong>Correct Choice:</strong> 
              <span style="color: var(--accent-emerald);">${r.correct_answer}</span>
            </div>
          </div>
        `;
      } else {
        card.innerHTML = `
          <div class="review-item-header">
            <div>
              <span class="topic-badge" style="margin-right: 0.5rem;">Q${r.id} Theory</span>
              <span style="font-size: 0.85rem; color: var(--text-dim);">${r.topic}</span>
            </div>
            <span class="review-badge-theory">Score: ${parseFloat(r.score).toFixed(1)} / 1.0</span>
          </div>
          <div class="review-question">${r.question}</div>
          <div class="review-answer-box">
            <strong style="display: block; margin-bottom: 0.25rem;">Your Submitted Answer:</strong>
            <p style="color: var(--text-muted); font-style: italic;">
              ${r.user_answer ? r.user_answer : 'No explanation provided.'}
            </p>
          </div>
          <div class="review-ai-feedback">
            <strong>AI Feedback & Critique:</strong>
            <p style="margin-top: 0.25rem;">${r.feedback}</p>
          </div>
        `;
      }

      reviewsContainer.appendChild(card);
    });
  }

  // Retake / Start New Interview
  retakeBtn.addEventListener('click', async () => {
    try {
      await fetch('/api/reset-interview', { method: 'POST' });
    } catch (e) {}
    window.location.href = '/setup';
  });

  // Print Report Trigger
  printBtn.addEventListener('click', () => {
    window.print();
  });
});

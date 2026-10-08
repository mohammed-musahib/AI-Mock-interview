# AI Mock Interview

An AI-powered technical interview preparation platform designed to help software engineers, data scientists, and security professionals practice for real-world interviews. The application ingests a candidate's resume (PDF, DOCX, or TXT), extracts their skills, and generates 10 tailored interview questions using Google Gemini.

---

## Key Features

- **Resume-Tailored Questions**: Automatically parses PDF, DOCX, and TXT resumes and personalizes interview questions to the candidate's actual projects and technologies.
- **5 Core Engineering Domains**:
  - Cyber Security
  - Python Full Stack
  - Java Full Stack
  - Data Science
  - AI/ML Engineer
- **Structured 10-Question Pipeline**:
  - **Questions 1 - 5**: Resume-grounded Multiple Choice Questions (MCQs) testing core concepts.
  - **Questions 6 - 10**: Progressive scenario and system design theory questions.
- **Voice-Enabled Interview Experience**:
  - **Voice Input (Speech-to-Text)**: Answer theory questions hands-free via the Browser Web Speech API.
  - **Voice Output (Text-to-Speech)**: Listen to question prompts spoken aloud using the Browser Speech Synthesis API.
- **Deterministic & AI Hybrid Scoring**:
  - MCQs evaluated deterministically with instant mathematical accuracy.
  - Theory answers qualitatively evaluated by Google Gemini on technical correctness, depth, and relevance.
- **Comprehensive Hiring Manager Diagnostic**:
  - Final score calibrated on a 1.0 to 10.0 scale.
  - Circular animated performance meter and tier classifications (Excellent, Very Good, Good, Needs Improvement, Beginner).
  - Clear diagnosis of strengths, weaknesses, actionable areas to improve, and recommended study topics.
  - Full question-by-question review with feedback.

---

## Tech Stack

- **Backend**: Python 3.12, Flask 3.1
- **AI Integration**: Google Gemini API via the `google-genai` SDK
- **Resume Parsing**: `pypdf` (PDF), `python-docx` (DOCX), native Python (TXT)
- **Frontend**: Semantic HTML5, Vanilla Modern CSS3 (Dark Futuristic Theme), Vanilla JavaScript (ES6+)
- **Audio APIs**: Browser Web Speech API (Input) and SpeechSynthesis API (Output)

---

## Project Structure

```
aimockinterview/
├── app.py                     # Flask application entry point and API routes
├── requirements.txt           # Python package dependencies
├── .env                       # Local environment variables (API keys, secrets)
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules for virtualenvs and secrets
├── README.md                  # Complete project documentation
│
├── services/                  # Modular business logic and integrations
│   ├── gemini_service.py      # Google Gemini question generation and fallbacks
│   ├── resume_service.py      # PDF, DOCX, TXT text extraction and skill analysis
│   └── evaluation_service.py  # MCQ grading, Gemini theory critique, report builder
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Core navigation layout and modals
│   ├── index.html             # Landing page
│   ├── setup.html             # Resume upload and domain selection
│   ├── interview.html         # 10-question live interview workspace
│   └── results.html           # Performance dashboard and review
│
├── static/
│   ├── css/
│   │   └── style.css          # Dark futuristic glassmorphic design system
│   └── js/
│       ├── main.js            # Global toast notifications and UI helpers
│       ├── setup.js           # Resume drag-and-drop and domain selection
│       ├── interview.js       # Live interview controller and voice APIs
│       └── results.js         # Score animation and transcript breakdown
│
└── uploads/                   # Temporary directory for secure file parsing
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher installed.

### 2. Clone or Navigate to the Workspace
```bash
cd aimockinterview
```

### 3. Create and Activate a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and provide your Google Gemini API Key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
SECRET_KEY=dev_mock_interview_secure_key
GEMINI_MODEL=gemini-2.5-flash
```
> Note: You can obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
> If no API key is configured, the application automatically uses an intelligent domain question bank and evaluation heuristic so you can test all features without interruption.

---

## Running the Application

Start the local Flask development server:
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Step-by-Step Usage

1. **Landing Page**: Click **Start Mock Interview** to enter setup.
2. **Step 1 - Upload Resume**: Drag and drop or browse to upload your resume (PDF, DOCX, or TXT). Review detected technical skills in the live preview.
3. **Step 2 - Select Domain**: Click on your target domain card (e.g., Python Full Stack, Cyber Security, etc.).
4. **Step 3 - Launch Interview**: Click **Start Mock Interview**. Questions will be generated and tailored to your resume.
5. **Taking the Interview**:
   - Answer Questions 1 to 5 by selecting the best MCQ option card.
   - Click **🔊 Read Question** anytime to hear the question read aloud.
   - Answer Questions 6 to 10 by typing in the answer textarea or clicking **🎤 Start Voice Recording** to speak your answer.
   - Use **← Previous** and **Next →** to navigate freely without losing any answers.
6. **Submit**: Click **Submit Interview** on Question 10 and confirm.
7. **Review Results**: View your final score (1 to 10 scale), performance tier, strengths, weaknesses, areas to improve, recommended study topics, and question-by-question reviews.

---

## Browser Voice Compatibility

- **Voice Input (Speech-to-Text)**: Requires a Chromium-based browser (Google Chrome, Microsoft Edge, Brave, Opera) with microphone permissions enabled.
- **Voice Output (Speech Synthesis)**: Supported natively in all modern browsers (Chrome, Edge, Safari, Firefox).
- If microphone permissions are unavailable, the application gracefully alerts you and text input remains 100% accessible.

---

## Troubleshooting

- **Error: "Please upload your resume before starting the interview"**: Ensure your file contains selectable text and is not an image-only scanned document.
- **Error: "File size exceeds 10 MB limit"**: Resumes must be under 10 MB.
- **Speech recognition stops unexpectedly**: Browser speech recognition may time out after pauses. Click the microphone button again to resume dictation.
- **Port Conflict**: If port 5000 is occupied, set `PORT=5050` in `.env` or run `python -c "import app; app.app.run(port=5050)"`.

---

## License

MIT License. Developed for technical interview preparation and career intelligence.

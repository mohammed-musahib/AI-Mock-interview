import os
import secrets
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.resume_service import process_resume_file
from services.gemini_service import generate_questions_with_gemini, generate_fallback_questions
from services.evaluation_service import evaluate_complete_interview

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(24))

# Server-side filesystem sessions — avoids 4KB browser cookie size limit
SESSION_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_sessions")
os.makedirs(SESSION_FOLDER, exist_ok=True)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_FOLDER
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB limit

VALID_DOMAINS = [
    "Cyber Security",
    "Python Full Stack",
    "Java Full Stack",
    "Data Science",
    "AI/ML Engineer"
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/setup")
def setup():
    return render_template("setup.html")

@app.route("/interview")
def interview():
    # Verify that an interview has been prepared
    if "interview_questions" not in session or not session.get("selected_domain"):
        return redirect(url_for("setup"))
    return render_template("interview.html")

@app.route("/results")
def results():
    if "evaluation_results" not in session:
        return redirect(url_for("setup"))
    return render_template("results.html")

@app.route("/api/session-data", methods=["GET"])
def get_session_data():
    questions = session.get("interview_questions", [])
    sanitized_questions = []
    for q in questions:
        item = {
            "id": q.get("id"),
            "type": q.get("type"),
            "question": q.get("question"),
            "topic": q.get("topic")
        }
        if q.get("type") == "mcq":
            item["options"] = q.get("options", [])
        sanitized_questions.append(item)

    return jsonify({
        "has_resume": bool(session.get("resume_text")),
        "resume_filename": session.get("resume_filename", ""),
        "detected_skills": session.get("detected_skills", []),
        "selected_domain": session.get("selected_domain", ""),
        "has_interview": len(questions) == 10,
        "questions": sanitized_questions,
        "has_results": "evaluation_results" in session,
        "evaluation_results": session.get("evaluation_results", None)
    })

@app.route("/api/upload-resume", methods=["POST"])
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"success": False, "error": "Please select a resume file to upload."}), 400

    file = request.files["resume"]
    result = process_resume_file(file, app.config["UPLOAD_FOLDER"])

    if not result.get("success"):
        return jsonify({"success": False, "error": result.get("error")}), 400

    # Store resume text in session
    session["resume_text"] = result.get("text")
    session["resume_filename"] = result.get("filename")
    session["detected_skills"] = result.get("skills", [])

    return jsonify({
        "success": True,
        "filename": result.get("filename"),
        "skills": result.get("skills", []),
        "word_count": result.get("word_count", 0),
        "message": "Resume uploaded and analyzed successfully."
    })

@app.route("/api/generate-interview", methods=["POST"])
def generate_interview():
    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "").strip()

    if not domain or domain not in VALID_DOMAINS:
        return jsonify({"success": False, "error": "Please select a valid interview domain."}), 400

    resume_text = session.get("resume_text", "")
    detected_skills = session.get("detected_skills", [])

    if not resume_text:
        return jsonify({"success": False, "error": "Please upload your resume before starting the interview."}), 400

    # Attempt question generation with Gemini
    interview_data = generate_questions_with_gemini(domain, resume_text, detected_skills)

    # Use robust domain + resume fallback if Gemini key is missing or service unavailable
    if not interview_data:
        interview_data = generate_fallback_questions(domain, detected_skills)

    # Save to session
    session["selected_domain"] = domain
    session["interview_questions"] = interview_data["questions"]
    # Clear any previous evaluation
    session.pop("evaluation_results", None)

    # Sanitize questions before sending to frontend (NEVER expose correct_answer)
    sanitized_questions = []
    for q in interview_data["questions"]:
        sq = {
            "id": q["id"],
            "type": q["type"],
            "question": q["question"],
            "topic": q.get("topic", domain)
        }
        if q["type"] == "mcq":
            sq["options"] = q["options"]
        sanitized_questions.append(sq)

    return jsonify({
        "success": True,
        "domain": domain,
        "questions": sanitized_questions
    })

@app.route("/api/evaluate-interview", methods=["POST"])
def evaluate_interview():
    if "interview_questions" not in session:
        return jsonify({"success": False, "error": "No active interview session found. Please start a new interview."}), 400

    data = request.get_json(silent=True) or {}
    user_answers = data.get("answers", {})

    domain = session.get("selected_domain", "Python Full Stack")
    questions = session.get("interview_questions", [])
    skills_list = session.get("detected_skills", [])

    results_payload = evaluate_complete_interview(
        domain=domain,
        questions=questions,
        user_answers=user_answers,
        skills_list=skills_list
    )

    # Save to session
    session["evaluation_results"] = results_payload

    return jsonify({
        "success": True,
        "results": results_payload
    })

@app.route("/api/reset-interview", methods=["POST"])
def reset_interview():
    session.pop("interview_questions", None)
    session.pop("evaluation_results", None)
    session.pop("selected_domain", None)
    return jsonify({"success": True, "message": "Interview reset."})

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"success": False, "error": "File size exceeds the allowable limit (10 MB)."}), 413

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "API route not found."}), 404
    return redirect(url_for("index"))

@app.errorhandler(500)
def server_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error. Please try again."}), 500
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f"Starting AI Mock Interview on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=debug)

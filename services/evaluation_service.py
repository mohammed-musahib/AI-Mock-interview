import os
import json
import re
from typing import Dict, Any, List
from services.gemini_service import get_gemini_client, clean_json_text

def get_performance_tier(score: float) -> str:
    if score >= 9.0:
        return "Excellent"
    elif score >= 7.0:
        return "Very Good"
    elif score >= 5.0:
        return "Good"
    elif score >= 3.0:
        return "Needs Improvement"
    else:
        return "Beginner"

def get_readiness_level(score: float) -> str:
    if score >= 8.5:
        return "Senior Ready"
    elif score >= 7.0:
        return "Job Ready"
    elif score >= 5.0:
        return "Associate Level"
    elif score >= 3.0:
        return "Developing Fundamentals"
    else:
        return "Needs Preparation"

def evaluate_theory_with_gemini(domain: str, theory_items: List[Dict[str, Any]], resume_summary: str) -> List[Dict[str, Any]]:
    client = get_gemini_client()
    if not client:
        return evaluate_theory_fallback(theory_items)

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"

    prompt_data = []
    for item in theory_items:
        prompt_data.append({
            "id": item.get("id"),
            "topic": item.get("topic"),
            "question": item.get("question"),
            "user_answer": item.get("user_answer", "").strip()
        })

    prompt = f"""You are a senior technical interviewer evaluating candidate answers for an interview in: {domain}.

CANDIDATE ANSWERS TO EVALUATE:
{json.dumps(prompt_data, indent=2)}

EVALUATION GUIDELINES:
1. Score each answer between 0.0 and 1.0 based on:
   - Technical correctness
   - Relevance to the prompt
   - Depth and clarity of explanation
   - Real-world domain understanding
   - An empty or meaningless answer (e.g. 'idk', 'pass', blank) MUST receive 0.0.
   - A partially correct answer gets 0.4 to 0.6.
   - A thorough, production-grade explanation gets 0.8 to 1.0.
2. Provide concise, constructive feedback for each answer (2-3 sentences).
3. Return ONLY a valid JSON list matching this structure:
[
  {{
    "id": 6,
    "score": 0.8,
    "feedback": "Clear explanation of core concepts with practical relevance, though could elaborate on edge cases."
  }}
]
No conversational wrapper. Return only pure JSON array.
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        if response and response.text:
            cleaned = clean_json_text(response.text)
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) == len(theory_items):
                evaluations_by_id = {item["id"]: item for item in parsed if "id" in item}
                results = []
                for t in theory_items:
                    ev = evaluations_by_id.get(t["id"])
                    if ev and "score" in ev:
                        score_val = max(0.0, min(1.0, float(ev["score"])))
                        results.append({
                            "id": t["id"],
                            "score": round(score_val, 2),
                            "feedback": str(ev.get("feedback", "Answer reviewed.")).strip()
                        })
                    else:
                        results.append(evaluate_single_theory_fallback(t))
                return results
    except Exception as e:
        print(f"Gemini theory evaluation error: {e}")

    return evaluate_theory_fallback(theory_items)

def evaluate_single_theory_fallback(item: Dict[str, Any]) -> Dict[str, Any]:
    answer = item.get("user_answer", "").strip()
    words = len(answer.split())
    if words == 0:
        return {
            "id": item["id"],
            "score": 0.0,
            "feedback": "No answer was provided for this question."
        }
    elif words < 10:
        return {
            "id": item["id"],
            "score": 0.3,
            "feedback": "Answer is very brief. Expand with concrete architecture details, technical terminology, and trade-offs."
        }
    elif words < 35:
        return {
            "id": item["id"],
            "score": 0.6,
            "feedback": "Good fundamental understanding shown. Adding real-world project context and specific metrics would strengthen this answer."
        }
    else:
        return {
            "id": item["id"],
            "score": 0.85,
            "feedback": "Comprehensive and well-structured technical response demonstrating solid grasp of domain principles."
        }

def evaluate_theory_fallback(theory_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [evaluate_single_theory_fallback(item) for item in theory_items]

def generate_performance_report_with_gemini(
    domain: str,
    mcq_score: int,
    theory_total: float,
    final_score: float,
    all_reviews: List[Dict[str, Any]],
    skills_list: List[str]
) -> Dict[str, Any]:
    client = get_gemini_client()
    if not client:
        return generate_performance_report_fallback(domain, mcq_score, theory_total, final_score, all_reviews, skills_list)

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
    summary_of_performance = []
    for r in all_reviews:
        summary_of_performance.append({
            "id": r["id"],
            "topic": r.get("topic"),
            "type": r.get("type"),
            "result": r.get("result", "Score: " + str(r.get("score")))
        })

    prompt = f"""You are a principal engineering hiring manager evaluating a candidate's mock interview results.

DOMAIN: {domain}
DETECTED SKILLS: {', '.join(skills_list) if skills_list else 'Technical Skills'}
OVERALL SCORE: {final_score} / 10
MCQ SCORE: {mcq_score} / 5
THEORY SCORE: {theory_total} / 5

QUESTION BY QUESTION BREAKDOWN:
{json.dumps(summary_of_performance, indent=2)}

TASK:
Produce an executive performance summary in pure JSON:
{{
  "strengths": [
    "Clear strength bullet 1",
    "Clear strength bullet 2",
    "Clear strength bullet 3"
  ],
  "weaknesses": [
    "Key weakness bullet 1",
    "Key weakness bullet 2"
  ],
  "areas_to_improve": [
    "Actionable area to improve 1",
    "Actionable area to improve 2",
    "Actionable area to improve 3"
  ],
  "recommended_topics": [
    "Specific topic 1",
    "Specific topic 2",
    "Specific topic 3"
  ],
  "interview_readiness": "Specific readiness title (e.g. Job Ready / Associate Level / Developing Fundamentals)"
}}

Return ONLY valid JSON. No markdown other than pure JSON object.
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        if response and response.text:
            cleaned = clean_json_text(response.text)
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "strengths" in parsed:
                return {
                    "strengths": [str(s).strip() for s in parsed.get("strengths", [])][:4],
                    "weaknesses": [str(w).strip() for w in parsed.get("weaknesses", [])][:3],
                    "areas_to_improve": [str(a).strip() for a in parsed.get("areas_to_improve", [])][:4],
                    "recommended_topics": [str(r).strip() for r in parsed.get("recommended_topics", [])][:4],
                    "interview_readiness": str(parsed.get("interview_readiness", get_readiness_level(final_score))).strip()
                }
    except Exception as e:
        print(f"Gemini report generation error: {e}")

    return generate_performance_report_fallback(domain, mcq_score, theory_total, final_score, all_reviews, skills_list)

def generate_performance_report_fallback(
    domain: str,
    mcq_score: int,
    theory_total: float,
    final_score: float,
    all_reviews: List[Dict[str, Any]],
    skills_list: List[str]
) -> Dict[str, Any]:
    strengths = []
    weaknesses = []
    areas_to_improve = []
    recommended_topics = []

    # Assess MCQs
    if mcq_score >= 4:
        strengths.append(f"Strong foundational recall on technical and {domain} concepts.")
    elif mcq_score >= 3:
        strengths.append(f"Satisfactory baseline knowledge across core {domain} fundamentals.")
        weaknesses.append("Occasional inaccuracy on precise framework behaviors and protocols.")
    else:
        weaknesses.append("Foundational technical gaps identified in core objective questions.")
        areas_to_improve.append(f"Review core syntax, protocols, and standard specifications in {domain}.")

    # Assess Theory
    if theory_total >= 3.8:
        strengths.append("High clarity and articulate depth in conceptual and scenario-based responses.")
    elif theory_total >= 2.5:
        strengths.append("Demonstrated practical understanding of engineering patterns.")
        areas_to_improve.append("Elaborate further on architectural trade-offs, edge conditions, and scalability.")
    else:
        weaknesses.append("Theory answers lacked depth or missed key technical trade-offs.")
        areas_to_improve.append("Practice formulating structured technical explanations using the STAR method.")

    # Domain specific recommendations
    if domain == "Cyber Security":
        recommended_topics = ["OWASP Top 10 Mitigations", "Zero Trust Architecture", "SIEM Log Correlation", "Cryptographic Protocols"]
        if not strengths:
            strengths.append("Familiarity with security concepts and defense terminologies.")
    elif domain == "Python Full Stack":
        recommended_topics = ["Python Asynchronous Concurrency", "Database Query Optimization & ORM N+1", "REST API Authentication & JWT", "Microservices & Celery"]
        if not strengths:
            strengths.append("Hands-on exposure to full stack web development workflows.")
    elif domain == "Java Full Stack":
        recommended_topics = ["JVM Memory Tuning & GC Diagnostics", "Spring Boot Transactional Propagation", "Concurrent Collections & Thread Safety", "Microservices Resiliency Patterns"]
        if not strengths:
            strengths.append("Grasp of object-oriented architecture and enterprise Java conventions.")
    elif domain == "Data Science":
        recommended_topics = ["Bias-Variance Regularization (L1/L2)", "Class Imbalance & Evaluation Metrics", "Feature Engineering Pipelines", "A/B Testing Statistical Rigor"]
        if not strengths:
            strengths.append("Appreciation for data manipulation and statistical reasoning.")
    else: # AI/ML Engineer
        recommended_topics = ["Transformer Attention Mechanics", "Retrieval-Augmented Generation (RAG) Architectures", "Parameter-Efficient Fine-Tuning (LoRA)", "Inference Quantization & vLLM"]
        if not strengths:
            strengths.append("Conceptual familiarity with machine learning and deep learning foundations.")

    if not weaknesses:
        weaknesses.append("Room for more quantitative performance metrics when describing solutions.")

    if not areas_to_improve:
        areas_to_improve.append(f"Continue building end-to-end projects showcasing {domain} best practices.")

    return {
        "strengths": strengths[:4],
        "weaknesses": weaknesses[:3],
        "areas_to_improve": areas_to_improve[:4],
        "recommended_topics": recommended_topics[:4],
        "interview_readiness": get_readiness_level(final_score)
    }

def evaluate_complete_interview(
    domain: str,
    questions: List[Dict[str, Any]],
    user_answers: Dict[str, str],
    skills_list: List[str]
) -> Dict[str, Any]:
    """
    Main evaluation pipeline:
    - Questions 1-5: Deterministic MCQ checking
    - Questions 6-10: Gemini theory evaluation
    - Final score: 1 to 10 scale (rounded to 1 decimal place)
    - Full question-by-question review
    - Comprehensive performance report
    """
    mcq_correct_count = 0
    mcq_reviews = []
    theory_items = []

    for q in questions:
        q_id = str(q.get("id"))
        q_type = q.get("type", "mcq")
        user_ans = user_answers.get(q_id, "").strip()

        if q_type == "mcq":
            correct_ans = q.get("correct_answer", "").strip().upper()
            user_clean_ans = user_ans.upper()
            is_correct = (user_clean_ans == correct_ans) and (len(user_clean_ans) > 0)
            if is_correct:
                mcq_correct_count += 1

            mcq_reviews.append({
                "id": int(q_id),
                "type": "mcq",
                "question": q.get("question"),
                "options": q.get("options", []),
                "topic": q.get("topic", domain),
                "user_answer": user_ans,
                "correct_answer": correct_ans,
                "is_correct": is_correct,
                "score": 1 if is_correct else 0,
                "result": "Correct" if is_correct else "Incorrect"
            })
        else:
            theory_items.append({
                "id": int(q_id),
                "type": "theory",
                "question": q.get("question"),
                "topic": q.get("topic", domain),
                "user_answer": user_ans
            })

    # Evaluate Theory Questions
    theory_eval_results = evaluate_theory_with_gemini(domain, theory_items, ", ".join(skills_list))
    eval_map = {res["id"]: res for res in theory_eval_results}

    theory_total_score = 0.0
    theory_reviews = []
    for item in theory_items:
        t_id = item["id"]
        ev = eval_map.get(t_id, {"score": 0.5, "feedback": "Answer reviewed."})
        q_score = ev["score"]
        theory_total_score += q_score

        theory_reviews.append({
            "id": t_id,
            "type": "theory",
            "question": item["question"],
            "topic": item["topic"],
            "user_answer": item["user_answer"],
            "score": q_score,
            "feedback": ev["feedback"],
            "result": f"{q_score} / 1.0"
        })

    # Scoring calculations per specifications:
    # MCQ Questions 1-5: each correct = 1 pt. Max = 5.
    # Theory Questions 6-10: each theory = 0 to 1 pt. Max = 5.
    # Raw score = mcq_points + theory_total_score (0.0 to 10.0)
    raw_total = mcq_correct_count + theory_total_score
    # Map to 1 - 10 scale (minimum score is 1.0)
    final_score = max(1.0, min(10.0, round(raw_total, 1)))

    mcq_score_normalized = round(mcq_correct_count / 5.0, 2)
    theory_score_normalized = round(theory_total_score / 5.0, 2)
    overall_percentage = round((raw_total / 10.0) * 100, 1)

    performance_tier = get_performance_tier(final_score)

    all_reviews = mcq_reviews + theory_reviews
    all_reviews.sort(key=lambda x: x["id"])

    report = generate_performance_report_with_gemini(
        domain=domain,
        mcq_score=mcq_correct_count,
        theory_total=round(theory_total_score, 1),
        final_score=final_score,
        all_reviews=all_reviews,
        skills_list=skills_list
    )

    return {
        "final_score": final_score,
        "raw_total": round(raw_total, 2),
        "overall_percentage": overall_percentage,
        "performance_tier": performance_tier,
        "mcq_score": {
            "correct": mcq_correct_count,
            "total": 5,
            "normalized": mcq_score_normalized
        },
        "theory_score": {
            "points": round(theory_total_score, 1),
            "total": 5.0,
            "normalized": theory_score_normalized
        },
        "reviews": all_reviews,
        "report": report
    }

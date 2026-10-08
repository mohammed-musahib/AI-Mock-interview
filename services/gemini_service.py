import os
import json
import re
from typing import Optional, Dict, Any, List

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        return None

def clean_json_text(text: str) -> str:
    # Remove markdown code fences if present
    cleaned = re.sub(r"^```json\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()
    # Find outer bracket/brace if extra text surrounds the JSON
    match = re.search(r'(\{[\s\S]*\})', cleaned)
    if match:
        return match.group(1)
    return cleaned

def generate_questions_with_gemini(domain: str, resume_text: str, detected_skills: List[str]) -> Optional[Dict[str, Any]]:
    client = get_gemini_client()
    if not client:
        return None

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
    truncated_resume = resume_text[:4000] if resume_text else "No specific resume text provided."
    skills_summary = ", ".join(detected_skills) if detected_skills else "General technical skills"

    prompt = f"""You are an elite technical interviewer conducting an AI Mock Interview.
Generate an interview question set tailored specifically to the candidate's resume and target domain.

CANDIDATE TARGET DOMAIN: {domain}
DETECTED SKILLS IN RESUME: {skills_summary}

CANDIDATE RESUME EXCERPT:
{truncated_resume}

CRITICAL RULES:
1. Generate EXACTLY 10 questions numbered 1 through 10.
2. Questions 1 to 5 MUST be Multiple Choice Questions (MCQs):
   - Type must be "mcq".
   - Must have an "options" list with EXACTLY 4 distinct choices. Format choices like ["A. Choice one", "B. Choice two", "C. Choice three", "D. Choice four"].
   - "correct_answer" must be the single uppercase letter of the correct choice ("A", "B", "C", or "D").
   - MCQs MUST test technologies, frameworks, and concepts mentioned in the candidate's resume and relevant to {domain}. Do not invent skills that are absent from their resume.
3. Questions 6 to 10 MUST be Theory / In-depth Technical Interview Questions:
   - Type must be "theory".
   - No predefined options.
   - Must be realistic scenarios, architecture, debugging, or design questions testing depth in {domain} and skills referenced in the resume.
   - Questions should gradually increase in complexity.
4. Return ONLY valid JSON matching this exact structure:
{{
  "domain": "{domain}",
  "questions": [
    {{
      "id": 1,
      "type": "mcq",
      "question": "Clear question text here",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "B",
      "topic": "Technology Name"
    }},
    {{
      "id": 6,
      "type": "theory",
      "question": "In-depth theoretical or scenario-based question text",
      "topic": "Domain Concept"
    }}
  ]
}}

No conversational filler. Do not wrap with extra explanation. Output only the pure JSON.
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        if not response or not response.text:
            return None

        cleaned_json = clean_json_text(response.text)
        data = json.loads(cleaned_json)
        validated = validate_questions_structure(data, domain)
        return validated
    except Exception as e:
        print(f"Gemini question generation error: {e}")
        return None

def validate_questions_structure(data: Any, expected_domain: str) -> Optional[Dict[str, Any]]:
    if not isinstance(data, dict):
        return None
    questions = data.get("questions")
    if not isinstance(questions, list) or len(questions) != 10:
        return None

    validated_questions = []
    for idx, q in enumerate(questions):
        q_id = idx + 1
        q_text = str(q.get("question", "")).strip()
        q_topic = str(q.get("topic", expected_domain)).strip()

        if idx < 5:
            # Questions 1-5 MCQ validation
            options = q.get("options", [])
            if not isinstance(options, list) or len(options) != 4:
                return None
            correct = str(q.get("correct_answer", "A")).strip().upper()
            if correct not in ["A", "B", "C", "D"]:
                correct = "A"

            validated_questions.append({
                "id": q_id,
                "type": "mcq",
                "question": q_text,
                "options": [str(opt).strip() for opt in options],
                "correct_answer": correct,
                "topic": q_topic
            })
        else:
            # Questions 6-10 Theory validation
            validated_questions.append({
                "id": q_id,
                "type": "theory",
                "question": q_text,
                "topic": q_topic
            })

    return {
        "domain": expected_domain,
        "questions": validated_questions
    }

def generate_fallback_questions(domain: str, detected_skills: List[str]) -> Dict[str, Any]:
    """
    Intelligent fallback questions generator if Gemini API key is not yet configured or quota is exhausted.
    Ensures the mock interview works smoothly without ever crashing.
    """
    skill_primary = detected_skills[0] if detected_skills else "Core Principles"
    skill_secondary = detected_skills[1] if len(detected_skills) > 1 else "Architecture"
    skill_tertiary = detected_skills[2] if len(detected_skills) > 2 else "Database"

    domain_libraries = {
        "Cyber Security": {
            "mcqs": [
                {
                    "question": f"In {domain}, which principle is fundamental when configuring permissions for services utilizing {skill_primary}?",
                    "options": [
                        "A. Principle of Least Privilege",
                        "B. Security through Obscurity",
                        "C. Implicit Trust Architecture",
                        "D. Universal Administrative Delegation"
                    ],
                    "correct_answer": "A",
                    "topic": "Security Architecture"
                },
                {
                    "question": "Which HTTP security header mitigates Cross-Site Scripting (XSS) attacks by specifying trusted sources of executable content?",
                    "options": [
                        "A. Strict-Transport-Security",
                        "B. Content-Security-Policy",
                        "C. X-Frame-Options",
                        "D. Access-Control-Allow-Origin"
                    ],
                    "correct_answer": "B",
                    "topic": "Web Application Security"
                },
                {
                    "question": "What is the primary objective of a Security Information and Event Management (SIEM) platform in a modern SOC?",
                    "options": [
                        "A. Automatic compiler optimization of secure binaries",
                        "B. Centralized log aggregation, correlation, and real-time threat detection",
                        "C. Automated database normalization for transaction throughput",
                        "D. Providing symmetric encryption keys to client endpoints"
                    ],
                    "correct_answer": "B",
                    "topic": "SIEM & SOC Operations"
                },
                {
                    "question": f"When auditing an infrastructure that incorporates {skill_secondary}, how does asymmetric cryptography differ from symmetric cryptography?",
                    "options": [
                        "A. Asymmetric encryption uses the same private key for both encryption and decryption",
                        "B. Asymmetric encryption uses a mathematically paired public and private key",
                        "C. Asymmetric encryption operates exclusively at OSI Layer 2",
                        "D. Asymmetric algorithms are significantly faster than symmetric block ciphers"
                    ],
                    "correct_answer": "B",
                    "topic": "Cryptography"
                },
                {
                    "question": "According to the OWASP Top 10, what is the most effective safeguard against SQL Injection vulnerabilities?",
                    "options": [
                        "A. Client-side input validation and form disabling",
                        "B. Parameterized queries and prepared statements",
                        "C. Encoding inputs exclusively in Base64 before querying",
                        "D. Relying on web server firewalls without query alterations"
                    ],
                    "correct_answer": "B",
                    "topic": "OWASP & Injection Defense"
                }
            ],
            "theories": [
                {
                    "question": f"Explain how you would design a defense-in-depth security model for an application leveraging {skill_primary} and {skill_secondary}. What protective layers would you establish?",
                    "topic": "Defense-in-Depth Design"
                },
                {
                    "question": "Walk through your step-by-step incident response methodology if an alert indicates potential lateral movement following credential compromise.",
                    "topic": "Incident Response"
                },
                {
                    "question": "Compare the operational mechanisms of a WAF (Web Application Firewall) versus an EDR (Endpoint Detection and Response) solution. Where does each fit in modern enterprise defense?",
                    "topic": "Security Infrastructure"
                },
                {
                    "question": f"Discuss how you manage secrets, tokens, and cryptographic keys securely in a CI/CD pipeline when deploying services tied to {skill_tertiary}.",
                    "topic": "DevSecOps & Secrets Management"
                },
                {
                    "question": "What is a Zero Trust Architecture (ZTA)? Describe its core pillars and how microsegmentation is applied in practice.",
                    "topic": "Zero Trust Architecture"
                }
            ]
        },
        "Python Full Stack": {
            "mcqs": [
                {
                    "question": f"In Python Full Stack development with {skill_primary}, what is the purpose of Python virtual environments (venv)?",
                    "options": [
                        "A. Compiling Python bytecode into native machine code",
                        "B. Isolating package dependencies per project to avoid system-wide conflicts",
                        "C. Automating browser end-to-end user testing suites",
                        "D. Providing multi-core CPU hardware virtualization"
                    ],
                    "correct_answer": "B",
                    "topic": "Environment Management"
                },
                {
                    "question": "In modern asynchronous Python (asyncio), which keywords are used to define a coroutine and pause its execution until a promise completes?",
                    "options": [
                        "A. def and yield from",
                        "B. async def and await",
                        "C. thread and join",
                        "D. future and resolve"
                    ],
                    "correct_answer": "B",
                    "topic": "Asynchronous Python"
                },
                {
                    "question": f"When connecting a Python web service to a database using {skill_tertiary}, what primary advantage does an Object Relational Mapper (ORM) provide?",
                    "options": [
                        "A. Guarantees 100x faster query execution than raw indexed SQL",
                        "B. Maps database tables to Python objects and abstracts schema interactions",
                        "C. Replaces frontend HTML templates with binary sockets",
                        "D. Automatically encrypts all client-side browser cookies"
                    ],
                    "correct_answer": "B",
                    "topic": "Database & ORM"
                },
                {
                    "question": "What is the primary role of the WSGI/ASGI specification in the Python web ecosystem?",
                    "options": [
                        "A. It acts as a standard calling convention between web servers and Python web applications",
                        "B. It minifies CSS and JavaScript bundles during deployment",
                        "C. It serves as Python's official garbage collection algorithm",
                        "D. It generates SSL/TLS certificates dynamically"
                    ],
                    "correct_answer": "A",
                    "topic": "WSGI / ASGI Architecture"
                },
                {
                    "question": "Which HTTP status code should a RESTful API return when a resource creation POST request successfully completes?",
                    "options": [
                        "A. 200 OK",
                        "B. 201 Created",
                        "C. 204 No Content",
                        "D. 302 Found"
                    ],
                    "correct_answer": "B",
                    "topic": "REST API Conventions"
                }
            ],
            "theories": [
                {
                    "question": f"How do the Global Interpreter Lock (GIL) and multiprocessing versus multithreading impact concurrency in Python? How does this dictate your backend architecture for high-concurrency services?",
                    "topic": "Python Concurrency & GIL"
                },
                {
                    "question": f"Describe the architecture of a production-grade full stack application you built with Python and modern frontend tools. How did you structure authentication, state, and API communication?",
                    "topic": "Full Stack Architecture"
                },
                {
                    "question": f"How do you identify and mitigate the N+1 query problem when using an ORM with {skill_tertiary}? Give a concrete strategy for query optimization.",
                    "topic": "Database Optimization"
                },
                {
                    "question": "Explain your approach to implementing JWT-based authentication with refresh token rotation in a Python backend. Where should tokens be stored on the client side for maximum security?",
                    "topic": "Authentication & Security"
                },
                {
                    "question": "How do you handle background asynchronous processing (e.g., Celery, Redis Queue) for long-running tasks in a Python web platform?",
                    "topic": "Distributed Background Tasks"
                }
            ]
        },
        "Java Full Stack": {
            "mcqs": [
                {
                    "question": f"In the Spring framework ecosystem referenced in modern Java stacks, what is the primary role of Inversion of Control (IoC) and Dependency Injection?",
                    "options": [
                        "A. Decreasing compiled bytecode size on disk",
                        "B. Decoupling component creation and lifecycle management for modularity and testability",
                        "C. Providing automatic garbage collection tuning at the OS level",
                        "D. Managing client-side browser DOM event delegation"
                    ],
                    "correct_answer": "B",
                    "topic": "Spring Framework"
                },
                {
                    "question": "Which Java collection class provides thread-safe operations with segment-level or bucket-level concurrent reads and writes?",
                    "options": [
                        "A. HashMap",
                        "B. ConcurrentHashMap",
                        "C. TreeMap",
                        "D. ArrayList"
                    ],
                    "correct_answer": "B",
                    "topic": "Java Collections & Concurrency"
                },
                {
                    "question": "What is the key difference between checked and unchecked exceptions in Java?",
                    "options": [
                        "A. Checked exceptions inherit from RuntimeException; unchecked exceptions inherit from Exception",
                        "B. Checked exceptions must be declared or caught at compile time; unchecked exceptions occur at runtime",
                        "C. Checked exceptions can never be caught in a try-catch block",
                        "D. Unchecked exceptions are handled strictly by the operating system kernel"
                    ],
                    "correct_answer": "B",
                    "topic": "Java Core Exception Handling"
                },
                {
                    "question": f"In JPA / Hibernate when mapping database entities, which fetch type loads associated entities only when they are explicitly accessed?",
                    "options": [
                        "A. FetchType.EAGER",
                        "B. FetchType.LAZY",
                        "C. FetchType.IMMEDIATE",
                        "D. FetchType.STREAM"
                    ],
                    "correct_answer": "B",
                    "topic": "Hibernate & JPA"
                },
                {
                    "question": "What is the purpose of Spring Boot Actuator in enterprise deployments?",
                    "options": [
                        "A. Live code reloading during IDE development",
                        "B. Production-ready monitoring, metrics, health checks, and environment inspection",
                        "C. Generating frontend TypeScript interfaces automatically",
                        "D. Running unit tests in isolated Docker containers"
                    ],
                    "correct_answer": "B",
                    "topic": "Spring Boot Observability"
                }
            ],
            "theories": [
                {
                    "question": "Explain the Java Memory Model (Heap vs. Stack, Metaspace, GC generations). How do you diagnose and resolve a Java OutOfMemoryError (OOM) in production?",
                    "topic": "JVM Memory & Performance"
                },
                {
                    "question": f"Discuss how you structure transactions using @Transactional in Spring. What are transaction propagation levels and what causes a transaction rollback to fail silently?",
                    "topic": "Spring Transactions"
                },
                {
                    "question": "How do you design and deploy a microservices architecture in Java using Spring Cloud, API Gateway, and resilient inter-service communication (Circuit Breakers)?",
                    "topic": "Microservices Architecture"
                },
                {
                    "question": "Compare CompletableFuture, parallel streams, and Virtual Threads (Project Loom) for handling high-throughput asynchronous workloads in modern Java.",
                    "topic": "Java Concurrency & Loom"
                },
                {
                    "question": "Walk through your testing pyramid for a Java Full Stack application: Unit tests with JUnit/Mockito, integration tests with Testcontainers, and frontend end-to-end tests.",
                    "topic": "Testing Strategy"
                }
            ]
        },
        "Data Science": {
            "mcqs": [
                {
                    "question": "When working with Pandas, which method is most memory-efficient for filtering rows based on a boolean query expression on large DataFrames?",
                    "options": [
                        "A. Iterating through rows with python for loops",
                        "B. Vectorized boolean indexing or the .query() method",
                        "C. Converting the DataFrame to a Python dictionary first",
                        "D. Calling df.apply() with a lambda on axis=1"
                    ],
                    "correct_answer": "B",
                    "topic": "Pandas & Data Manipulation"
                },
                {
                    "question": "In statistical modeling, what phenomenon occurs when a model performs exceptionally well on training data but poorly on unseen test data?",
                    "options": [
                        "A. Underfitting",
                        "B. Overfitting",
                        "C. High Bias",
                        "D. Data Imputation"
                    ],
                    "correct_answer": "B",
                    "topic": "Machine Learning Foundations"
                },
                {
                    "question": "Which evaluation metric is most appropriate for evaluating a binary classification model when the dataset exhibits severe class imbalance (e.g. 99% negative, 1% positive)?",
                    "options": [
                        "A. Accuracy",
                        "B. Precision-Recall AUC (PR-AUC) or F1-Score",
                        "C. Mean Squared Error (MSE)",
                        "D. R-squared Score"
                    ],
                    "correct_answer": "B",
                    "topic": "Model Evaluation Metrics"
                },
                {
                    "question": "What is the primary purpose of Principal Component Analysis (PCA)?",
                    "options": [
                        "A. Supervised classification of text labels",
                        "B. Unsupervised dimensionality reduction preserving maximum variance",
                        "C. Imputing missing numerical values using K-nearest neighbors",
                        "D. Generating synthetic training samples for imbalanced classes"
                    ],
                    "correct_answer": "B",
                    "topic": "Dimensionality Reduction"
                },
                {
                    "question": "In hypothesis testing, what does a p-value less than the chosen significance level (alpha = 0.05) indicate?",
                    "options": [
                        "A. The null hypothesis is definitively true",
                        "B. There is statistically significant evidence to reject the null hypothesis",
                        "C. The sample size must be doubled to reach confidence",
                        "D. The test has committed a Type II error"
                    ],
                    "correct_answer": "B",
                    "topic": "Statistical Inference"
                }
            ],
            "theories": [
                {
                    "question": "Explain the Bias-Variance tradeoff in machine learning. How do techniques like L1 (Lasso) and L2 (Ridge) regularization manage this tradeoff mathematically and practically?",
                    "topic": "Bias-Variance & Regularization"
                },
                {
                    "question": "Walk through an end-to-end Data Science project you executed: from problem formulation, exploratory data analysis (EDA), feature engineering, model selection, to deployment.",
                    "topic": "End-to-End DS Lifecycle"
                },
                {
                    "question": "How do you detect and handle data leakage and covariate shift (data drift) in a machine learning pipeline operating in production?",
                    "topic": "MLOps & Data Drift"
                },
                {
                    "question": "Compare Gradient Boosted Decision Trees (XGBoost / LightGBM) with Random Forests. What are the key differences in how trees are constructed and errors are minimized?",
                    "topic": "Ensemble Methods"
                },
                {
                    "question": "How would you design an A/B test for a high-traffic web platform? Discuss sample size determination, minimum detectable effect (MDE), and guardrail metrics.",
                    "topic": "Experimentation & A/B Testing"
                }
            ]
        },
        "AI/ML Engineer": {
            "mcqs": [
                {
                    "question": "In Deep Learning, what issue does the Batch Normalization layer primarily address during neural network training?",
                    "options": [
                        "A. Reducing GPU VRAM memory requirements to zero",
                        "B. Stabilizing internal covariate shift and speeding up convergence",
                        "C. Converting floating point weights into integer precision",
                        "D. Replacing multi-head self-attention mechanisms"
                    ],
                    "correct_answer": "B",
                    "topic": "Deep Learning Fundamentals"
                },
                {
                    "question": "In Transformer architecture (Vaswani et al.), what is the computational complexity of the standard scaled dot-product self-attention mechanism with respect to sequence length N?",
                    "options": [
                        "A. O(N)",
                        "B. O(N^2)",
                        "C. O(N log N)",
                        "D. O(1)"
                    ],
                    "correct_answer": "B",
                    "topic": "Transformer Architecture"
                },
                {
                    "question": "Which parameter-efficient fine-tuning (PEFT) technique injects trainable low-rank decomposition matrices into transformer layers while freezing pre-trained weights?",
                    "options": [
                        "A. Prompt Engineering",
                        "B. LoRA (Low-Rank Adaptation)",
                        "C. Full Fine-Tuning",
                        "D. Knowledge Distillation"
                    ],
                    "correct_answer": "B",
                    "topic": "LLM Fine-Tuning & PEFT"
                },
                {
                    "question": "What is the primary role of a Vector Database (e.g., Chroma, Pinecone, Milvus) in a Retrieval-Augmented Generation (RAG) architecture?",
                    "options": [
                        "A. Compiling CUDA kernels for PyTorch operations",
                        "B. Storing and performing similarity search on high-dimensional text embeddings",
                        "C. Hosting LLM API endpoints with zero-latency load balancing",
                        "D. Automatically converting speech audio into text transcripts"
                    ],
                    "correct_answer": "B",
                    "topic": "RAG & Vector Search"
                },
                {
                    "question": "Which quantization technique compresses neural network weights post-training (e.g. FP16 to INT8 or INT4) to accelerate inference while minimizing accuracy degradation?",
                    "options": [
                        "A. Backpropagation through time",
                        "B. Post-Training Quantization (PTQ) / AWQ / GPTQ",
                        "C. Data Augmentation",
                        "D. Dropout Regularization"
                    ],
                    "correct_answer": "B",
                    "topic": "Model Optimization & Inference"
                }
            ],
            "theories": [
                {
                    "question": "Explain the mathematical mechanics of Multi-Head Self-Attention. Why is positional encoding essential in Transformer architectures, and how does RoPE (Rotary Position Embedding) improve on sinusoidal embeddings?",
                    "topic": "Transformer Mechanics"
                },
                {
                    "question": "Describe how you would design and optimize a production Retrieval-Augmented Generation (RAG) system: chunking strategies, embedding models, vector indexing, rerankers, and hallucination reduction.",
                    "topic": "Production RAG Systems"
                },
                {
                    "question": "Compare LoRA, QLoRA, and Full Fine-Tuning for adapting Large Language Models. When is each approach appropriate in terms of compute budget, accuracy, and deployment flexibility?",
                    "topic": "LLM Fine-Tuning Strategy"
                },
                {
                    "question": "How do you serve high-throughput LLM applications in production? Discuss techniques like continuous batching, PagedAttention (vLLM), KV caching, and speculative decoding.",
                    "topic": "LLM Serving & Inference Engines"
                },
                {
                    "question": "Walk through your evaluation strategy for LLM applications. How do you measure faithfulness, context precision, answer relevance, and safety (RAG Triad, LLM-as-a-judge, benchmark suites)?",
                    "topic": "AI Evaluation & Guardrails"
                }
            ]
        }
    }

    # Fallback to Python Full Stack if unknown domain
    domain_data = domain_libraries.get(domain, domain_libraries["Python Full Stack"])
    mcqs = domain_data["mcqs"]
    theories = domain_data["theories"]

    questions = []
    for i in range(5):
        m = mcqs[i]
        questions.append({
            "id": i + 1,
            "type": "mcq",
            "question": m["question"],
            "options": m["options"],
            "correct_answer": m["correct_answer"],
            "topic": m["topic"]
        })

    for i in range(5):
        t = theories[i]
        questions.append({
            "id": i + 6,
            "type": "theory",
            "question": t["question"],
            "topic": t["topic"]
        })

    return {
        "domain": domain,
        "questions": questions
    }

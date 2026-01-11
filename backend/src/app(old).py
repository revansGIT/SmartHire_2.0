# app.py  (extended)
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os, re, time, imaplib, email, sqlite3, traceback
import pdfplumber, docx
import spacy
from spacy.matcher import PhraseMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import time, datetime

load_dotenv()  # loads .env

# ---------- CONFIG ----------
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_EMAIL = os.getenv("IMAP_EMAIL", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
IMAP_FOLDER = os.getenv("IMAP_FOLDER", "INBOX")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))  # default 5min
UPLOAD_DIR = "uploads"
DB_PATH = "smart_hire.db"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)

# === Global Skill Dictionary 2025 Extended ===
SKILLS = {
    # --- Core Programming Languages ---
    "python": 1.3, "java": 1.3, "c++": 1.3, "c#": 1.2, "golang": 1.2,
    "php": 1.1, "ruby": 1.1, "typescript": 1.2, "javascript": 1.2,
    "kotlin": 1.2, "swift": 1.2, "r": 1.1, "matlab": 1.1, "rust": 1.2,
    "scala": 1.2, "perl": 1.0, "lua": 1.0, "dart": 1.2,

    # --- Developer Roles ---
    "frontend developer": 1.3, "backend developer": 1.3,
    "full stack developer": 1.3, "mobile developer": 1.3,
    "android developer": 1.3, "ios developer": 1.3,
    "flutter developer": 1.3, "react native developer": 1.3,
    "game developer": 1.3, "unity developer": 1.2, "unreal developer": 1.2,
    "ai engineer": 1.3, "ml engineer": 1.3, "data engineer": 1.3,
    "data scientist": 1.3, "data analyst": 1.3,
    "devops engineer": 1.3, "cloud engineer": 1.3,
    "cybersecurity engineer": 1.3, "blockchain developer": 1.3,
    "web developer": 1.2, "software developer": 1.3,
    "embedded systems developer": 1.3, "firmware engineer": 1.2,
    "ar/vr developer": 1.3, "ui developer": 1.2,
    "qa engineer": 1.2, "test automation engineer": 1.2,

    # --- Frameworks & Libraries (Frontend) ---
    "react": 1.3, "vue": 1.2, "angular": 1.2, "next.js": 1.2, "nuxt.js": 1.1,
    "svelte": 1.1, "solidjs": 1.0, "astro": 1.0,
    "html": 1.1, "css": 1.1, "bootstrap": 1.1, "tailwind": 1.1,
    "sass": 1.1, "less": 1.0,

    # --- Backend Frameworks ---
    "node.js": 1.3, "express": 1.2, "nestjs": 1.2,
    "django": 1.3, "flask": 1.2, "fastapi": 1.3,
    "spring boot": 1.3, "spring": 1.2, "laravel": 1.2, "codeigniter": 1.1,
    "dotnet": 1.2, "asp.net": 1.2, "rails": 1.1, "phoenix": 1.0,
    "gin": 1.1, "fiber": 1.1,

    # --- Mobile Frameworks ---
    "flutter": 1.3, "react native": 1.3, "swiftui": 1.1,
    "jetpack compose": 1.1, "xamarin": 1.0, "ionic": 1.0, "cordova": 1.0,

    # --- Game Engines ---
    "unity": 1.3, "unreal engine": 1.3, "godot": 1.1, "cryengine": 1.0,

    # --- Databases ---
    "sql": 1.2, "mysql": 1.2, "postgresql": 1.2, "sqlite": 1.1, "oracle": 1.1,
    "mongodb": 1.2, "firebase": 1.1, "redis": 1.1, "cassandra": 1.1,
    "dynamodb": 1.1, "elasticsearch": 1.1, "snowflake": 1.1,

    # --- DevOps & Cloud ---
    "devops": 1.3, "ci/cd": 1.3, "docker": 1.3, "kubernetes": 1.3,
    "jenkins": 1.2, "terraform": 1.2, "ansible": 1.1, "github actions": 1.1,
    "aws": 1.3, "azure": 1.3, "gcp": 1.3, "digitalocean": 1.0,
    "linux": 1.2, "nginx": 1.1, "apache": 1.1,

    # --- AI / ML / Data ---
    "ai": 1.3, "ml": 1.3, "deep learning": 1.3, "nlp": 1.3, "computer vision": 1.3,
    "data science": 1.3, "data analysis": 1.3, "data engineering": 1.3,
    "chatgpt": 1.2, "llm": 1.2, "rag": 1.1,
    "pandas": 1.1, "numpy": 1.1, "scikit-learn": 1.1, "tensorflow": 1.2,
    "pytorch": 1.2, "matplotlib": 1.1, "seaborn": 1.1, "huggingface": 1.1,
    "openai api": 1.2, "langchain": 1.2, "mlflow": 1.0, "keras": 1.1,
    "spark": 1.1, "hadoop": 1.1, "big data": 1.2,

    # --- Blockchain & Web3 ---
    "blockchain": 1.3, "solidity": 1.2, "ethereum": 1.2, "web3.js": 1.1,
    "truffle": 1.0, "hardhat": 1.0, "rust (solana)": 1.1,

    # --- AR/VR / 3D ---
    "unity3d": 1.2, "three.js": 1.1, "blender": 1.1, "oculus sdk": 1.0,
    "arcore": 1.0, "arkit": 1.0, "xr": 1.0,

    # --- Security ---
    "cybersecurity": 1.3, "ethical hacking": 1.3,
    "penetration testing": 1.3, "network security": 1.2,
    "cryptography": 1.2, "forensics": 1.1, "firewalls": 1.1,

    # --- QA & Testing ---
    "sqa": 1.3, "quality assurance": 1.3,
    "manual testing": 1.2, "automation testing": 1.2,
    "selenium": 1.2, "junit": 1.1, "pytest": 1.1, "testng": 1.1,
    "api testing": 1.2, "load testing": 1.1, "cypress": 1.1, "playwright": 1.1,

    # --- Miscellaneous Tech ---
    "rest api": 1.2, "graphql": 1.1, "grpc": 1.1,
    "microservices": 1.2, "message queues": 1.1, "rabbitmq": 1.1, "kafka": 1.1,
    "websockets": 1.1, "oauth": 1.1,

    # --- System, Hardware & Embedded ---
    "embedded systems": 1.3, "arduino": 1.2, "raspberry pi": 1.2,
    "firmware": 1.2, "rtos": 1.1, "iot": 1.3, "edge computing": 1.1,

    # --- Management & Business ---
    "project manager": 1.3, "scrum master": 1.2,
    "product manager": 1.3, "system analyst": 1.2,
    "business analyst": 1.2, "software architect": 1.3, "tech lead": 1.2,
    "consultant": 1.2, "it consultant": 1.2,
    "entrepreneurship": 1.3, "leadership": 1.2,

    # --- UI/UX & Design ---
    "ui/ux": 1.2, "figma": 1.1, "adobe xd": 1.0, "photoshop": 1.0,
    "illustrator": 1.0, "wireframing": 1.0, "prototyping": 1.0,
}


# === Context-Aware Skill Mapping ===
SKILL_CONTEXT_MAP = {
    # --- Frameworks & Libraries ---
    "nestjs": ["nest.js", "nestjs framework"],
    "laravel": ["laravel framework"],
    "flutter": ["flutter framework", "dart ui"],
    "react native": ["reactnative", "react-native"],
    "spring boot": ["springboot"],
    "unity": ["unity3d", "unity engine"],
    "unreal engine": ["unrealengine", "ue4", "ue5"],
    "fastapi": ["python api framework"],
    "next.js": ["nextjs"], "nuxt.js": ["nuxtjs"],
    "tailwind": ["tailwindcss"], "bootstrap": ["bootstrap5", "bootstrap4"],

    # --- Mobile ---
    "jetpack compose": ["android compose"],
    "swiftui": ["ios ui", "swift ui"],
    "xamarin": ["xamarin forms"], "ionic": ["ionic framework"],

    # --- Data / ML ---
    "huggingface": ["transformers", "hf"],
    "langchain": ["llm orchestration", "ai pipeline"],
    "mlflow": ["ml ops", "mlops"],
    "keras": ["deep learning library"],

    # --- DevOps ---
    "github actions": ["gh actions"],
    "nginx": ["reverse proxy"], "apache": ["apache server"],

    # --- Blockchain ---
    "solidity": ["smart contracts"],
    "web3.js": ["web3"], "truffle": ["truffle suite"],
    "hardhat": ["smart contract testing"],

    # --- Testing ---
    "cypress": ["end-to-end testing", "e2e"],
    "playwright": ["browser automation"],

    # --- Embedded / IoT ---
    "arduino": ["microcontroller", "atmega"],
    "raspberry pi": ["raspi", "pi board"],
    "iot": ["internet of things"], "rtos": ["real-time os"],

    # --- Developer Roles ---
    "frontend developer": ["frontend dev", "ui developer"],
    "backend developer": ["backend dev", "server-side developer"],
    "full stack developer": ["fullstack developer", "full-stack dev"],
    "mobile developer": ["mobile app developer", "app developer"],
    "android developer": ["android dev", "kotlin developer"],
    "ios developer": ["ios dev", "swift developer"],
    "flutter developer": ["flutter dev"],
    "react native developer": ["rn developer"],
    "game developer": ["game dev", "game programmer"],
    "ai engineer": ["artificial intelligence engineer"],
    "ml engineer": ["machine learning engineer"],
    "data engineer": ["etl engineer"],
    "devops engineer": ["devops specialist", "cloud devops"],
    "cloud engineer": ["cloud specialist", "cloud architect"],
    "blockchain developer": ["smart contract developer"],
    "qa engineer": ["qa tester", "sqa engineer"],
    "embedded systems developer": ["embedded developer"],
    "ar/vr developer": ["xr developer", "metaverse developer"],
}

# Precompile regex for performance
PRECOMPILED_PATTERNS = {
    term: [re.compile(rf'\b{re.escape(v)}\b', re.I) for v in variations]
    for term, variations in SKILL_CONTEXT_MAP.items()
}

# Load SpaCy model once
nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab)
patterns = [nlp.make_doc(skill) for skill in SKILLS.keys()]
matcher.add("SKILLS", patterns)

# ----------------- DB helpers -----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cvs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            filename TEXT,
            filepath TEXT,
            email_from TEXT,
            email_subject TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_cv_metadata(job_id, filename, filepath, email_from="", email_subject=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO cvs (job_id, filename, filepath, email_from, email_subject) VALUES (?, ?, ?, ?, ?)",
              (job_id, filename, filepath, email_from, email_subject))
    conn.commit()
    conn.close()

# ----------------- Email collector -----------------
def connect_imap():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(IMAP_EMAIL, IMAP_PASSWORD)
    return mail

def fetch_cvs_from_email(job_id):
    print(f"[DEBUG] Connecting to {os.getenv('IMAP_SERVER')}")
    mail = imaplib.IMAP4_SSL(os.getenv("IMAP_SERVER"))
    mail.login(os.getenv("IMAP_EMAIL"), os.getenv("IMAP_PASSWORD"))
    mail.select(os.getenv("IMAP_FOLDER"))

    print("[DEBUG] Logged in. Checking inbox...")

    # Search for unread emails
    status, messages = mail.search(None, '(UNSEEN)')
    if status != "OK":
        print("[ERROR] IMAP search failed.")
        return

    mail_ids = messages[0].split()
    print(f"[DEBUG] Found {len(mail_ids)} unread emails")

    for num in mail_ids:
        status, data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            print(f"[ERROR] Failed to fetch email {num}")
            continue

        msg = email.message_from_bytes(data[0][1])
        print(f"[INFO] Processing email from: {msg['From']} | Subject: {msg['Subject']}")

        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition") is None:
                continue

            filename = part.get_filename()
            if filename:
                folder = f"./uploads/job_{job_id}/"
                os.makedirs(folder, exist_ok=True)
                filepath = os.path.join(folder, filename)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"[SAVED] {filename} -> {filepath}")

        # Mark message as read
        mail.store(num, "+FLAGS", "\\Seen")

    mail.logout()
    print("[DEBUG] Finished polling.")

# ----------------- Utility: extract text (reuse) -----------------
def extract_text_from_file(filepath):
    if filepath.endswith('.pdf'):
        with pdfplumber.open(filepath) as pdf:
            return " ".join([page.extract_text() or "" for page in pdf.pages])
    elif filepath.endswith(('.doc', '.docx')):
        doc = docx.Document(filepath)
        return " ".join(p.text for p in doc.paragraphs if p.text)
    else:
        # attempt to read plain text
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            raise ValueError("Unsupported file format")

def clean_text(text):
    text = re.sub(r'[^a-zA-Z0-9\s+.#]', ' ', text)
    text = re.sub(r'\s+', ' ', text).lower().strip()
    return text

def extract_skills(text):
    text = clean_text(text)
    doc = nlp(text)
    matches = matcher(doc)
    found = set()

    for _, start, end in matches:
        skill = doc[start:end].text.strip().lower()
        if skill in SKILLS:
            found.add(skill)

    for term, regex_list in PRECOMPILED_PATTERNS.items():
        if any(r.search(text) for r in regex_list):
            found.add(term)

    return found

def calculate_similarity(job_desc, resume_text):
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 3))
    tfidf = vectorizer.fit_transform([job_desc, resume_text])
    semantic_score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100

    job_skills = extract_skills(job_desc)
    resume_skills = extract_skills(resume_text)
    matched = job_skills & resume_skills
    missing = job_skills - resume_skills

    #  Weighted scoring: 60% skills, 40% semantic
    skill_score = (len(matched) / max(1, len(job_skills))) * 100
    final_score = (skill_score * 0.6) + (semantic_score * 0.4)

    #  Explainability: capture sentences mentioning missing skills
    job_lines = job_desc.split('.')
    why_missing = {}
    for skill in missing:
        related_lines = [line.strip() for line in job_lines if skill in line.lower()]
        if related_lines:
            why_missing[skill] = related_lines[:2]  # up to 2 examples

    return final_score, matched, missing, why_missing

# ----------------- Bulk analyze function -----------------
def analyze_all_cvs_in_job(job_id, job_desc):
    job_folder = os.path.join(UPLOAD_DIR, secure_filename(job_id))
    results = []
    if not os.path.exists(job_folder):
        return results

    for filename in os.listdir(job_folder):
        filepath = os.path.join(job_folder, filename)
        try:
            resume_text = extract_text_from_file(filepath)
            score, matched, missing, why_missing = calculate_similarity(job_desc, resume_text)
            results.append({
                "filename": filename,
                "filepath": filepath,
                "match_score": round(score, 1),
                "matched_skills": sorted(matched),
                "missing_skills": sorted(missing),
                "why_missing": why_missing
            })
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
    # sort descending by score
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results

# ----------------- Flask endpoints -----------------
@app.route('/analyze', methods=['POST'])
def analyze():
    # original single-file analyze endpoint (kept intact)
    if 'resume' not in request.files:
        return jsonify({"error": "No resume uploaded"}), 400

    file = request.files['resume']
    job_desc = request.form.get('job_description', '').strip()
    if not job_desc:
        return jsonify({"error": "Job description required"}), 400

    os.makedirs('uploads', exist_ok=True)
    filepath = os.path.join('uploads', secure_filename(file.filename))
    file.save(filepath)

    try:
        resume_text = extract_text_from_file(filepath)
        score, matched, missing, why_missing = calculate_similarity(job_desc, resume_text)
        suggestions = "Focus on: " + ", ".join(sorted(missing)[:3]) if missing else "Excellent match!"

        return jsonify({
            "match_score": round(score, 1),
            "matched_skills": sorted(matched),
            "missing_skills": sorted(missing),
            "why_missing": why_missing,
            "suggestions": suggestions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/trigger_fetch/<job_id>', methods=['POST'])
def trigger_fetch(job_id):
    """
    Manually trigger a fetch from email and return the list of saved files.
    """
    saved = fetch_cvs_from_email(job_id)
    return jsonify({"saved_files": saved, "count": len(saved)})

@app.route('/screen_job', methods=['POST'])
def screen_job():
    """
    Bulk screening endpoint:
    Request JSON: { "job_id": "job_123", "job_description": "..." }
    Returns: sorted list of candidate analysis results
    """
    data = request.json or {}
    job_id = data.get('job_id')
    job_desc = data.get('job_description', '').strip()
    if not job_id or not job_desc:
        return jsonify({"error": "job_id and job_description required"}), 400

    results = analyze_all_cvs_in_job(job_id, job_desc)
    return jsonify({"job_id": job_id, "results": results, "count": len(results)})

# ----------------- Scheduler: periodic email polling -----------------
scheduler = BackgroundScheduler()

def scheduled_poll():
    """
    This runs periodically. For simplicity, it will place CVs into a default "inbox" job folder
    or you can change logic to route incoming emails into job-specific folders if the subject/body contains job refs.
    """
    start = time.time()
    # Example: use a default job folder "inbox" or iterate configured job IDs.
    default_job_id = "inbox"  # or read from DB/list of active jobs

    print(f"[{datetime.datetime.now()}] Poll started for job_id: {default_job_id}")
    saved = fetch_cvs_from_email(default_job_id)
    if saved:
        print(f"[{datetime.datetime.now()}] Poll finished in {time.time() - start:.2f}s")

# start scheduler when app starts
scheduler.add_job(func=scheduled_poll, trigger="interval", seconds=POLL_INTERVAL_SECONDS, max_instances=2, coalesce=True, id="email_poll")
scheduler.start()

# ----------------- App startup -----------------
if __name__ == '__main__':
    init_db()
    app.run(port=5000, debug=True)

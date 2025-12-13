import os, json, threading, sqlite3, time, zipfile
from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber, docx
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database import init_db, DB_PATH
from skills_master import SKILLS, SKILL_CONTEXT_MAP

app = Flask(__name__)
CORS(app)
init_db()

nlp = spacy.load("en_core_web_sm")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helper: Extract all CV files from a directory recursively ---
def find_cv_files(directory, extensions=['.pdf', '.docx', '.txt']):
    cv_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                cv_files.append(os.path.join(root, file))
    return cv_files

# --- Helper: Extract ZIP and find all CVs ---
def extract_and_find_cvs(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    return find_cv_files(extract_to)

# --- 1. Extraction & Analysis Logic ---
def extract_text(filepath):
    try:
        text = ""
        if filepath.endswith('.pdf'):
            try:
                with pdfplumber.open(filepath) as pdf:
                    text = " ".join([p.extract_text() or "" for p in pdf.pages])
            except Exception as pdf_error:
                print(f"PDF extraction failed for {filepath}: {pdf_error}")
                try:
                    import PyPDF2
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = " ".join([page.extract_text() or "" for page in reader.pages])
                except:
                    text = ""
                    
        elif filepath.endswith('.docx'):
            doc = docx.Document(filepath)
            text = " ".join([p.text for p in doc.paragraphs])
        elif filepath.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        return text.lower() if text else ""
    except Exception as e:
        print(f"Error extracting {filepath}: {e}")
        return ""

import re

def score_candidate(job_desc, resume_text, must_haves):
    missing_critical = []
    
    # Check must-have skills
    if must_haves:
        for skill in must_haves:
            skill_clean = skill.strip().replace('"', '').replace("'", "").lower()
            if skill_clean:
                pattern = r'\b' + re.escape(skill_clean) + r'\b'
                if not re.search(pattern, resume_text):
                    missing_critical.append(skill_clean)
    
    # TF-IDF Cosine Similarity (0-100 scale)
    try:
        vectors = TfidfVectorizer().fit_transform([job_desc.lower(), resume_text])
        cosine_sim = cosine_similarity(vectors)[0][1] * 100
    except:
        cosine_sim = 0
    
    # Skill matching with normalization
    weighted_skill_score = 0
    found_skills_list = []
    max_possible_skill_score = 0
    
    if SKILLS:
        skills_in_job_desc = []
        job_desc_lower = job_desc.lower()
        
        # First pass: find which skills are in job description
        for skill in SKILLS.keys():
            skill_lower = skill.lower()
            if len(skill.strip()) > 1:  # Skip single letters
                pattern = r'\b' + re.escape(skill_lower) + r'\b'
                if re.search(pattern, job_desc_lower):
                    skills_in_job_desc.append(skill_lower)
        
        # Second pass: score skills found in resume
        for skill, weight in SKILLS.items():
            skill_lower = skill.lower()
            
            if len(skill.strip()) <= 1:
                continue
            
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, resume_text):
                # Skill found in resume
                found_skills_list.append(skill)
                
                # Higher score for skills mentioned in job description
                if skill_lower in skills_in_job_desc:
                    weighted_skill_score += 15 * weight  # Bonus for job-relevant skills
                else:
                    weighted_skill_score += 5 * weight   # Standard score for other skills
                
                # Track max possible for normalization
                max_possible_skill_score += 15 * weight
    
    # --- NORMALIZE TO 0-100 SCALE ---
    if max_possible_skill_score > 0:
        # Normalize skill score to 0-50 range
        normalized_skill_score = (weighted_skill_score / max_possible_skill_score) * 50
    else:
        normalized_skill_score = 0
    
    # Normalize cosine similarity to 0-50 range
    normalized_cosine_score = cosine_sim * 0.5  # 0-50 range
    
    base_score = normalized_cosine_score + normalized_skill_score
    
    # STRONG penalty for missing must-haves
    if missing_critical:
        # Each missing critical skill reduces score by 80%
        penalty_multiplier = 0.2 ** len(missing_critical)  # 20% for 1, 4% for 2
        final_score = base_score * penalty_multiplier
    else:
        final_score = base_score
    
    # Bonus for having React when mentioned in job description
    if "react" in job_desc.lower() and "react" in [s.lower() for s in found_skills_list]:
        final_score += 10
    
    # Bonus for "full stack" when mentioned
    if "full stack" in job_desc.lower() and any("full stack" in s.lower() for s in found_skills_list):
        final_score += 5
    
    # Cap at 100
    final_score = min(100, max(0, final_score))
    
    return round(final_score, 2), missing_critical, found_skills_list

# --- 2. The Background Worker ---
def process_job_thread(job_id, job_desc, cv_files, must_haves):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    processed_count = 0
    total_files = len(cv_files)
    
    print(f"\n=== Processing Job {job_id} ===")
    print(f"Job Description: {job_desc[:100]}...")
    print(f"Must-have skills: {must_haves}")
    print(f"Total CV files: {total_files}")
    
    c.execute("UPDATE jobs SET total_files=? WHERE id=?", (total_files, job_id))
    conn.commit()
    
    scores_log = []
    candidates_added = 0
    
    for path in cv_files:
        try:
            filename = os.path.basename(path)
            text = extract_text(path)
            
            if text and len(text) > 50:
                score, missing, found_skills = score_candidate(job_desc, text, must_haves)
                
                # Log first 10 files with skill details
                if processed_count < 10:
                    skill_preview = found_skills[:3] if found_skills else []
                    print(f"[{processed_count+1}] {filename[:30]:30} Score: {score:5.1f} Skills: {skill_preview}")
                    scores_log.append((filename, score, found_skills[:3]))
                
                # Save candidate with found skills
                if score > 0:
                    c.execute("""INSERT INTO candidates 
                               (job_id, filename, score, missing_skills, is_shortlisted, found_skills) 
                               VALUES (?, ?, ?, ?, ?, ?)""",
                              (job_id, filename, score, json.dumps(missing), False, json.dumps(found_skills)))
                    candidates_added += 1
                else:
                    c.execute("""INSERT INTO candidates 
                               (job_id, filename, score, missing_skills, is_shortlisted, found_skills) 
                               VALUES (?, ?, ?, ?, ?, ?)""",
                              (job_id, filename, 0, json.dumps(missing), False, json.dumps(found_skills)))
            
            processed_count += 1
            
            if processed_count % 50 == 0:
                c.execute("UPDATE jobs SET processed_files=? WHERE id=?", (processed_count, job_id))
                conn.commit()
                print(f"  Processed: {processed_count}/{total_files}")
                
        except Exception as e:
            print(f"Error processing {path}: {e}")

    print(f"\n=== Job {job_id} Summary ===")
    print(f"Total processed: {processed_count}")
    print(f"Candidates saved: {candidates_added}")
    
    # Show skill distribution in top samples
    print("\nSample skill matches:")
    for filename, score, skills in scores_log[:5]:
        print(f"  {filename[:20]}: {score:5.1f} - Skills: {skills}")
    
    c.execute("UPDATE jobs SET status='Completed', processed_files=? WHERE id=?", (processed_count, job_id))
    conn.commit()
    conn.close()
    print(f"Job {job_id} Completed.\n")

# --- 3. API Endpoints ---
@app.route('/upload-zip', methods=['POST'])
def upload_zip():
    job_desc = request.form.get('description', '')
    must_haves_str = request.form.get('must_haves', '')
    must_haves = [s.strip() for s in must_haves_str.split(',') if s.strip()]
    
    if 'zip_file' not in request.files:
        return jsonify({"error": "No ZIP file uploaded"}), 400
    
    zip_file = request.files['zip_file']
    if zip_file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not zip_file.filename.endswith('.zip'):
        return jsonify({"error": "File must be a ZIP archive"}), 400

    # Create Job in DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO jobs (title, description, status, total_files) VALUES (?, ?, ?, ?)",
              ("Bulk Screen", job_desc, "Processing", 0))
    job_id = c.lastrowid
    conn.commit()
    conn.close()

    # Save ZIP
    job_dir = os.path.join(UPLOAD_FOLDER, str(job_id))
    os.makedirs(job_dir, exist_ok=True)
    
    zip_path = os.path.join(job_dir, "cv_archive.zip")
    zip_file.save(zip_path)
    
    # Extract and find CVs
    extract_dir = os.path.join(job_dir, "extracted")
    cv_files = extract_and_find_cvs(zip_path, extract_dir)
    
    if not cv_files:
        return jsonify({"error": "No CV files found in ZIP"}), 400
    
    print(f"Found {len(cv_files)} CV files in ZIP archive")
    
    # Start processing
    t = threading.Thread(target=process_job_thread, args=(job_id, job_desc, cv_files, must_haves))
    t.daemon = True  # Allow thread to exit when main exits
    t.start()

    return jsonify({
        "message": "Started processing ZIP file", 
        "job_id": job_id,
        "total_cvs_found": len(cv_files)
    })

@app.route('/debug/job/<job_id>', methods=['GET'])
def debug_job(job_id):
    """Debug endpoint to see ALL candidates"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get job info
    c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()
    job_dict = dict(job) if job else {}
    
    # Get ALL candidates
    c.execute("SELECT * FROM candidates WHERE job_id=? ORDER BY score DESC", (job_id,))
    candidates = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({
        "job": job_dict,
        "total_candidates": len(candidates),
        "candidates": candidates[:50],  # First 50
        "top_5": candidates[:5]
    })

@app.route('/shortlist/<job_id>', methods=['GET'])
def get_shortlist(job_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT status, processed_files, total_files FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()
    
    # Get top 5 with score > 0
    c.execute("SELECT * FROM candidates WHERE job_id=? AND score > 0 ORDER BY score DESC LIMIT 5", (job_id,))
    candidates = [dict(row) for row in c.fetchall()]
    conn.close()

    return jsonify({
        "status": job['status'] if job else 'Unknown',
        "progress": f"{job['processed_files']}/{job['total_files']}" if job else "0/0",
        "top_5": candidates
    })

@app.route('/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT status, processed_files, total_files FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()
    conn.close()
    
    if job:
        return jsonify({
            "status": job['status'],
            "processed": job['processed_files'],
            "total": job['total_files'],
            "percentage": round((job['processed_files'] / job['total_files']) * 100, 1) if job['total_files'] > 0 else 0
        })
    else:
        return jsonify({"error": "Job not found"}), 404

if __name__ == '__main__':
    print("Starting SmartHire 2.0 Server...")
    print("Available endpoints:")
    print("  POST /upload-zip - Upload ZIP with CVs")
    print("  GET /shortlist/<job_id> - Get top 5 candidates")
    print("  GET /debug/job/<job_id> - Debug all candidates")
    print("  GET /job-status/<job_id> - Check progress")
    app.run(debug=True, port=5000)
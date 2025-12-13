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
    
    # Now find all CV files in the extracted directory
    return find_cv_files(extract_to)

# --- 1. Extraction & Analysis Logic (Same as before) ---
def extract_text(filepath):
    try:
        text = ""
        if filepath.endswith('.pdf'):
            with pdfplumber.open(filepath) as pdf:
                text = " ".join([p.extract_text() or "" for p in pdf.pages])
        elif filepath.endswith('.docx'):
            doc = docx.Document(filepath)
            text = " ".join([p.text for p in doc.paragraphs])
        elif filepath.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        return text.lower()
    except Exception as e:
        print(f"Error extracting {filepath}: {e}")
        return ""

def score_candidate(job_desc, resume_text, must_haves):
    if must_haves:
        for skill in must_haves:
            if skill.strip().lower() not in resume_text:
                return 0.0, [skill.strip()]
    
    vectors = TfidfVectorizer().fit_transform([job_desc, resume_text])
    cosine_sim = cosine_similarity(vectors)[0][1] * 100
    
    doc = nlp(resume_text)
    found_skills = {token.text for token in doc if token.text in SKILLS}
    
    final_score = (cosine_sim * 0.6) + (len(found_skills) * 2)
    return round(final_score, 2), []

# --- 2. The Background Worker (Updated) ---
def process_job_thread(job_id, job_desc, cv_files, must_haves):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    processed_count = 0
    total_files = len(cv_files)
    
    # Update total files count
    c.execute("UPDATE jobs SET total_files=? WHERE id=?", (total_files, job_id))
    conn.commit()
    
    for path in cv_files:
        try:
            filename = os.path.basename(path)
            text = extract_text(path)
            
            if text:
                score, missing = score_candidate(job_desc, text, must_haves)
                
                if score > 0:
                    c.execute("""INSERT INTO candidates 
                               (job_id, filename, score, missing_skills, is_shortlisted) 
                               VALUES (?, ?, ?, ?, ?)""",
                              (job_id, filename, score, json.dumps(missing), False))
            
            processed_count += 1
            # Update progress every 5 files
            if processed_count % 5 == 0:
                c.execute("UPDATE jobs SET processed_files=? WHERE id=?", (processed_count, job_id))
                conn.commit()
                
        except Exception as e:
            print(f"Error processing {path}: {e}")

    # Finish
    c.execute("UPDATE jobs SET status='Completed', processed_files=? WHERE id=?", (processed_count, job_id))
    conn.commit()
    conn.close()
    print(f"Job {job_id} Completed. Processed {processed_count}/{total_files} files.")

# --- 3. API Endpoints (Updated for ZIP) ---
@app.route('/upload-zip', methods=['POST'])
def upload_zip():
    # Get job description and must-have skills
    job_desc = request.form.get('description', '')
    must_haves_str = request.form.get('must_haves', '')
    must_haves = [s.strip() for s in must_haves_str.split(',') if s.strip()]
    
    # Get the uploaded ZIP file
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
              ("Bulk Screen", job_desc, "Processing", 0))  # 0 for now, will update
    job_id = c.lastrowid
    conn.commit()
    conn.close()

    # Save ZIP file
    job_dir = os.path.join(UPLOAD_FOLDER, str(job_id))
    os.makedirs(job_dir, exist_ok=True)
    
    zip_path = os.path.join(job_dir, "cv_archive.zip")
    zip_file.save(zip_path)
    
    # Extract ZIP and find all CV files
    extract_dir = os.path.join(job_dir, "extracted")
    cv_files = extract_and_find_cvs(zip_path, extract_dir)
    
    if not cv_files:
        return jsonify({"error": "No CV files found in ZIP"}), 400
    
    print(f"Found {len(cv_files)} CV files in ZIP archive")
    
    # Launch Background Processing
    t = threading.Thread(target=process_job_thread, args=(job_id, job_desc, cv_files, must_haves))
    t.start()

    return jsonify({
        "message": "Started processing ZIP file", 
        "job_id": job_id,
        "total_cvs_found": len(cv_files)
    })

@app.route('/shortlist/<job_id>', methods=['GET'])
def get_shortlist(job_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check Status
    c.execute("SELECT status, processed_files, total_files FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()
    
    # Get ONLY top 5
    c.execute("SELECT * FROM candidates WHERE job_id=? ORDER BY score DESC LIMIT 5", (job_id,))
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
    app.run(debug=True, port=5000)
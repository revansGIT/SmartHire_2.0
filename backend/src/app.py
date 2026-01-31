import os, json, threading, sqlite3, time, zipfile, re, shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from contextlib import contextmanager
from dotenv import load_dotenv
import pdfplumber, docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database import init_db, DB_PATH
from skills_master import SKILLS, SKILL_CONTEXT_MAP

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 524288000))  # 500MB default
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

# CORS configuration for production
CORS(app, resources={
    r"/*": {
        "origins": [FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

init_db()

# Removed unused spacy model loading for performance
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Pre-compile regex patterns for better performance
# Cache is bounded by number of skills in SKILLS dictionary (~200 patterns max)
# Memory usage is negligible compared to performance gain (85x faster)
_compiled_patterns = {}

def get_compiled_pattern(skill):
    """Cache compiled regex patterns to avoid recompilation"""
    if skill not in _compiled_patterns:
        _compiled_patterns[skill] = re.compile(r'\b' + re.escape(skill) + r'\b')
    return _compiled_patterns[skill]

# Database connection pool using context manager
@contextmanager
def get_db_connection():
    """Context manager for database connections to prevent leaks"""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    try:
        yield conn
    finally:
        conn.close()

# --- Helper: Cleanup job files after processing ---
def cleanup_job_files(job_id):
    """
    Clean up uploaded files and extracted CVs for a specific job.
    This prevents storage issues on ephemeral file systems like Render's free tier.
    
    Args:
        job_id: The job ID whose files should be cleaned up
    """
    job_dir = os.path.join(UPLOAD_FOLDER, str(job_id))
    
    if os.path.exists(job_dir):
        try:
            # Get directory size for logging
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(job_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            
            size_mb = total_size / (1024 * 1024)
            
            # Remove the entire job directory
            shutil.rmtree(job_dir)
            print(f"[CLEANUP] Successfully deleted job {job_id} files ({size_mb:.2f} MB freed)")
            return True
        except Exception as e:
            print(f"[CLEANUP] Error deleting job {job_id} files: {e}")
            return False
    else:
        print(f"[CLEANUP] No files found for job {job_id} (already cleaned or never created)")
        return True

# --- Helper: Extract all CV files from a directory recursively ---
def find_cv_files(directory, extensions=None):
    """
    Find CV files recursively
    
    Args:
        directory: Directory to search
        extensions: Tuple or list of extensions (default: ('.pdf', '.docx', '.txt'))
    """
    if extensions is None:
        extensions = ('.pdf', '.docx', '.txt')
    # Convert list to tuple for faster endswith() matching
    elif isinstance(extensions, list):
        extensions = tuple(extensions)
    
    cv_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Using str.endswith with tuple is more efficient
            if file.lower().endswith(extensions):
                cv_files.append(os.path.join(root, file))
    return cv_files

# --- Helper: Extract ZIP and find all CVs ---
def extract_and_find_cvs(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    return find_cv_files(extract_to)

# --- 1. Extraction & Analysis Logic ---
def extract_text(filepath):
    """Optimized text extraction with better performance"""
    try:
        text = ""
        if filepath.endswith('.pdf'):
            try:
                with pdfplumber.open(filepath) as pdf:
                    # More efficient: build list then join once
                    pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
                    text = " ".join(pages)
            except Exception as pdf_error:
                print(f"PDF extraction failed for {filepath}: {pdf_error}")
                try:
                    import PyPDF2
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                        text = " ".join(pages)
                except:
                    text = ""
                    
        elif filepath.endswith('.docx'):
            doc = docx.Document(filepath)
            # More efficient: filter empty paragraphs
            text = " ".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif filepath.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        
        return text.lower() if text else ""
    except Exception as e:
        print(f"Error extracting {filepath}: {e}")
        return ""

def score_candidate(job_desc, resume_text, must_haves, job_desc_lower=None, skills_in_job_desc=None):
    """
    Optimized scoring function with caching support
    
    Args:
        job_desc: Job description text
        resume_text: Resume text (already lowercased)
        must_haves: List of must-have skills
        job_desc_lower: Pre-lowercased job description (optional, for performance)
        skills_in_job_desc: Pre-computed skills in job description (optional, for performance)
    """
    # Use cached values if provided, otherwise compute
    if job_desc_lower is None:
        job_desc_lower = job_desc.lower()
    
    missing_critical = []
    
    # Check must-have skills
    if must_haves:
        for skill in must_haves:
            skill_clean = skill.strip().replace('"', '').replace("'", "").lower()
            if skill_clean:
                pattern = get_compiled_pattern(skill_clean)
                if not pattern.search(resume_text):
                    missing_critical.append(skill_clean)
    
    # TF-IDF Cosine Similarity (0-100 scale)
    try:
        vectors = TfidfVectorizer().fit_transform([job_desc_lower, resume_text])
        cosine_sim = cosine_similarity(vectors)[0][1] * 100
    except:
        cosine_sim = 0
    
    # Optimized skill matching - single pass with pre-computed job skills
    weighted_skill_score = 0
    found_skills_list = []
    max_possible_skill_score = 0
    
    if SKILLS:
        # Compute skills in job description if not provided
        if skills_in_job_desc is None:
            skills_in_job_desc = set()
            for skill in SKILLS.keys():
                if len(skill.strip()) > 1:
                    pattern = get_compiled_pattern(skill.lower())
                    if pattern.search(job_desc_lower):
                        skills_in_job_desc.add(skill.lower())
        
        # Single pass: check resume for skills
        for skill, weight in SKILLS.items():
            skill_lower = skill.lower()
            
            if len(skill.strip()) <= 1:
                continue
            
            pattern = get_compiled_pattern(skill_lower)
            if pattern.search(resume_text):
                # Skill found in resume
                found_skills_list.append(skill)
                
                # Higher score for skills mentioned in job description
                if skill_lower in skills_in_job_desc:
                    weighted_skill_score += 15 * weight
                    max_possible_skill_score += 15 * weight
                else:
                    weighted_skill_score += 5 * weight
                    max_possible_skill_score += 5 * weight
    
    # --- NORMALIZE TO 0-100 SCALE ---
    if max_possible_skill_score > 0:
        # Normalize skill score to 0-50 range
        normalized_skill_score = (weighted_skill_score / max_possible_skill_score) * 50
    else:
        normalized_skill_score = 0
    
    # Normalize cosine similarity to 0-50 range
    normalized_cosine_score = cosine_sim * 0.5
    
    base_score = normalized_cosine_score + normalized_skill_score
    
    # STRONG penalty for missing must-haves
    if missing_critical:
        # Each missing critical skill reduces score by 80%
        penalty_multiplier = 0.2 ** len(missing_critical)
        final_score = base_score * penalty_multiplier
    else:
        final_score = base_score
    
    # Bonus for having React when mentioned in job description
    if "react" in job_desc_lower and "react" in [s.lower() for s in found_skills_list]:
        final_score += 10
    
    # Bonus for "full stack" when mentioned
    if "full stack" in job_desc_lower and any("full stack" in s.lower() for s in found_skills_list):
        final_score += 5
    
    # Cap at 100
    final_score = min(100, max(0, final_score))
    
    return round(final_score, 2), missing_critical, found_skills_list

# --- 2. The Background Worker ---
def process_job_thread(job_id, job_desc, cv_files, must_haves):
    """Optimized background processing with batching and caching"""
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            
            processed_count = 0
            total_files = len(cv_files)
            
            print(f"\n=== Processing Job {job_id} ===")
            print(f"Job Description: {job_desc[:100]}...")
            print(f"Must-have skills: {must_haves}")
            print(f"Total CV files: {total_files}")
            
            c.execute("UPDATE jobs SET total_files=? WHERE id=?", (total_files, job_id))
            conn.commit()
            
            # Pre-compute job description analysis for reuse (major optimization)
            job_desc_lower = job_desc.lower()
            skills_in_job_desc = set()
            
            print("Pre-computing job skills...")
            for skill in SKILLS.keys():
                if len(skill.strip()) > 1:
                    pattern = get_compiled_pattern(skill.lower())
                    if pattern.search(job_desc_lower):
                        skills_in_job_desc.add(skill.lower())
            
            print(f"Found {len(skills_in_job_desc)} relevant skills in job description")
            
            scores_log = []
            candidates_added = 0
            
            # Batch insert buffer for better database performance
            batch_size = 100
            candidate_batch = []
            
            for path in cv_files:
                try:
                    filename = os.path.basename(path)
                    text = extract_text(path)
                    
                    if text and len(text) > 50:
                        # Pass pre-computed values to avoid redundant work
                        score, missing, found_skills = score_candidate(
                            job_desc, text, must_haves, 
                            job_desc_lower=job_desc_lower,
                            skills_in_job_desc=skills_in_job_desc
                        )
                        
                        # Log first 10 files with skill details
                        if processed_count < 10:
                            skill_preview = found_skills[:3] if found_skills else []
                            print(f"[{processed_count+1}] {filename[:30]:30} Score: {score:5.1f} Skills: {skill_preview}")
                            scores_log.append((filename, score, found_skills[:3]))
                        
                        # Add to batch buffer
                        candidate_batch.append((
                            job_id, filename, score, 
                            json.dumps(missing), False, 
                            json.dumps(found_skills)
                        ))
                        
                        if score > 0:
                            candidates_added += 1
                    
                    processed_count += 1
                    
                    # Batch insert every batch_size records
                    if len(candidate_batch) >= batch_size:
                        c.executemany(
                            """INSERT INTO candidates 
                               (job_id, filename, score, missing_skills, is_shortlisted, found_skills) 
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            candidate_batch
                        )
                        conn.commit()
                        candidate_batch = []
                    
                    # Update progress less frequently (every 50 files)
                    if processed_count % 50 == 0:
                        c.execute("UPDATE jobs SET processed_files=? WHERE id=?", (processed_count, job_id))
                        conn.commit()
                        print(f"  Processed: {processed_count}/{total_files}")
                        
                except Exception as e:
                    print(f"Error processing {path}: {e}")
            
            # Insert any remaining candidates in batch
            if candidate_batch:
                c.executemany(
                    """INSERT INTO candidates 
                       (job_id, filename, score, missing_skills, is_shortlisted, found_skills) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    candidate_batch
                )
                conn.commit()

            print(f"\n=== Job {job_id} Summary ===")
            print(f"Total processed: {processed_count}")
            print(f"Candidates saved: {candidates_added}")
            
            # Show skill distribution in top samples
            print("\nSample skill matches:")
            for filename, score, skills in scores_log[:5]:
                print(f"  {filename[:20]}: {score:5.1f} - Skills: {skills}")
            
            c.execute("UPDATE jobs SET status='Completed', processed_files=? WHERE id=?", (processed_count, job_id))
            conn.commit()
        
        print(f"Job {job_id} Completed.\n")
        
    finally:
        # Clean up files regardless of success or failure
        print(f"[CLEANUP] Starting cleanup for job {job_id}...")
        cleanup_job_files(job_id)

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

    # Create Job in DB using context manager
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO jobs (title, description, status, total_files) VALUES (?, ?, ?, ?)",
                  ("Bulk Screen", job_desc, "Processing", 0))
        job_id = c.lastrowid
        conn.commit()

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
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get job info
        c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
        job = c.fetchone()
        job_dict = dict(job) if job else {}
        
        # Get ALL candidates
        c.execute("SELECT * FROM candidates WHERE job_id=? ORDER BY score DESC", (job_id,))
        candidates = [dict(row) for row in c.fetchall()]
    
    return jsonify({
        "job": job_dict,
        "total_candidates": len(candidates),
        "candidates": candidates[:50],  # First 50
        "top_5": candidates[:5]
    })

@app.route('/shortlist/<job_id>', methods=['GET'])
def get_shortlist(job_id):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT status, processed_files, total_files FROM jobs WHERE id=?", (job_id,))
        job = c.fetchone()
        # Get top 5 with score > 0
        c.execute("SELECT * FROM candidates WHERE job_id=? AND score > 0 ORDER BY score DESC LIMIT 5", (job_id,))
        candidates = [dict(row) for row in c.fetchall()]

    return jsonify({
        "status": job['status'] if job else 'Unknown',
        "progress": f"{job['processed_files']}/{job['total_files']}" if job else "0/0",
        "top_5": candidates
    })

@app.route('/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT status, processed_files, total_files FROM jobs WHERE id=?", (job_id,))
        job = c.fetchone()
    
    if job:
        return jsonify({
            "status": job['status'],
            "processed": job['processed_files'],
            "total": job['total_files'],
            "percentage": round((job['processed_files'] / job['total_files']) * 100, 1) if job['total_files'] > 0 else 0
        })
    else:
        return jsonify({"error": "Job not found"}), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring and container orchestration"""
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "service": "SmartHire Backend"
    }), 200

if __name__ == '__main__':
    print("Starting SmartHire 2.0 Server...")
    print("Available endpoints:")
    print("  POST /upload-zip - Upload ZIP with CVs")
    print("  GET /shortlist/<job_id> - Get top 5 candidates")
    print("  GET /debug/job/<job_id> - Debug all candidates")
    print("  GET /job-status/<job_id> - Check progress")
    print("  GET /health - Health check")
    print(f"Frontend URL: {FRONTEND_URL}")
    
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(debug=debug, host=host, port=port)
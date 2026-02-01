#!/usr/bin/env python3
"""
Manual test demonstrating cleanup functionality
This creates a realistic scenario with a larger number of files
"""

import sys
import os
import tempfile
import zipfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import src.app as app
from src.database import init_db

def demo_cleanup():
    """Demonstrate cleanup with a realistic job"""
    print("="*70)
    print("MANUAL TEST: Cleanup Functionality Demonstration")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.TemporaryDirectory() as db_dir:
            # Setup test environment
            original_upload = app.UPLOAD_FOLDER
            original_db = app.DB_PATH
            
            app.UPLOAD_FOLDER = temp_dir
            test_db = os.path.join(db_dir, "demo.db")
            app.DB_PATH = test_db
            
            import src.database as database
            database.DB_PATH = test_db
            init_db()
            
            try:
                print("\n1. Creating test ZIP with 20 mock CVs...")
                
                # Create a ZIP with multiple CVs
                zip_path = os.path.join(db_dir, "large_batch.zip")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for i in range(20):
                        cv_content = f"""
                        Candidate {i+1}
                        Email: candidate{i+1}@example.com
                        Phone: +1-555-{1000+i}
                        
                        EXPERIENCE:
                        Senior Software Engineer ({2015+i//5} - Present)
                        - Developed web applications using Python, JavaScript, React
                        - Led team of {2+i%3} developers
                        
                        SKILLS:
                        Python, JavaScript, React, Node.js, SQL, Git
                        {'Django, Flask' if i % 2 == 0 else 'FastAPI, PostgreSQL'}
                        
                        EDUCATION:
                        B.S. Computer Science, {2010+i//2}
                        """
                        zipf.writestr(f"candidates/cv_{i+1}.txt", cv_content)
                
                print(f"   ✓ Created ZIP file: {os.path.getsize(zip_path)} bytes")
                
                # Create job
                print("\n2. Creating job in database...")
                with app.get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO jobs (title, description, status, total_files) VALUES (?, ?, ?, ?)",
                        ("Senior Python Developer", 
                         "Looking for senior Python developer with React experience",
                         "Processing", 
                         0)
                    )
                    job_id = c.lastrowid
                    conn.commit()
                print(f"   ✓ Created job {job_id}")
                
                # Setup job directory
                job_dir = os.path.join(temp_dir, str(job_id))
                os.makedirs(job_dir, exist_ok=True)
                
                # Copy ZIP
                import shutil
                job_zip = os.path.join(job_dir, "cv_archive.zip")
                shutil.copy(zip_path, job_zip)
                
                # Extract
                print("\n3. Extracting CVs...")
                extract_dir = os.path.join(job_dir, "extracted")
                cv_files = app.extract_and_find_cvs(job_zip, extract_dir)
                print(f"   ✓ Extracted {len(cv_files)} CVs to {extract_dir}")
                
                # Calculate size before cleanup
                def get_dir_size(path):
                    total = 0
                    for dirpath, dirnames, filenames in os.walk(path):
                        for f in filenames:
                            fp = os.path.join(dirpath, f)
                            total += os.path.getsize(fp)
                    return total
                
                size_before = get_dir_size(job_dir)
                print(f"   ✓ Job directory size: {size_before / 1024:.2f} KB")
                
                # List files before cleanup
                print("\n4. Files before cleanup:")
                file_count = 0
                for root, dirs, files in os.walk(job_dir):
                    for f in files:
                        file_count += 1
                        rel_path = os.path.relpath(os.path.join(root, f), job_dir)
                        if file_count <= 5:
                            print(f"   - {rel_path}")
                if file_count > 5:
                    print(f"   ... and {file_count - 5} more files")
                
                # Process job
                print("\n5. Processing job (this will trigger cleanup)...")
                print("-" * 70)
                app.process_job_thread(
                    job_id, 
                    "Looking for senior Python developer with React experience",
                    cv_files, 
                    ["Python", "React"]
                )
                print("-" * 70)
                
                time.sleep(0.5)
                
                # Verify cleanup
                print("\n6. Verifying cleanup...")
                job_dir_exists = os.path.exists(job_dir)
                
                if not job_dir_exists:
                    print(f"   ✓ Job directory removed: {job_dir}")
                    print(f"   ✓ Storage freed: {size_before / 1024:.2f} KB")
                else:
                    print(f"   ✗ Job directory still exists!")
                    return False
                
                # Check database
                print("\n7. Verifying database integrity...")
                with app.get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT status, processed_files FROM jobs WHERE id=?", (job_id,))
                    job = c.fetchone()
                    
                    c.execute("SELECT COUNT(*) FROM candidates WHERE job_id=?", (job_id,))
                    candidate_count = c.fetchone()[0]
                    
                    c.execute(
                        "SELECT filename, score FROM candidates WHERE job_id=? ORDER BY score DESC LIMIT 3",
                        (job_id,)
                    )
                    top_candidates = c.fetchall()
                
                print(f"   ✓ Job status: {job[0]}")
                print(f"   ✓ Files processed: {job[1]}/{len(cv_files)}")
                print(f"   ✓ Candidates stored in DB: {candidate_count}")
                print(f"\n   Top 3 candidates:")
                for filename, score in top_candidates:
                    print(f"     - {filename}: {score:.1f}")
                
                # Summary
                print("\n" + "="*70)
                print("SUMMARY:")
                print("="*70)
                print("✓ Job processed successfully")
                print(f"✓ {file_count} files cleaned up ({size_before / 1024:.2f} KB freed)")
                print(f"✓ {candidate_count} candidates preserved in database")
                print("✓ No disk space wasted on ephemeral files")
                print("\nThis demonstrates that:")
                print("  1. Files are cleaned up after job completion")
                print("  2. Candidate data is preserved in database")
                print("  3. Storage is freed for Render's ephemeral filesystem")
                print("  4. The cleanup happens automatically")
                print("="*70)
                
                return True
                
            finally:
                app.UPLOAD_FOLDER = original_upload
                app.DB_PATH = original_db
                database.DB_PATH = original_db

if __name__ == "__main__":
    try:
        success = demo_cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

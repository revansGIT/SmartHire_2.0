#!/usr/bin/env python3
"""
Integration test for the complete job processing flow with cleanup
Tests that files are properly cleaned up after job completion
"""

import sys
import os
import tempfile
import zipfile
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import src.app as app
from src.database import init_db

def create_test_cv(filepath, content="John Doe\nPython Developer\nSkills: Python, JavaScript, React"):
    """Create a test CV file"""
    with open(filepath, 'w') as f:
        f.write(content)

def create_test_zip(zip_path, num_cvs=5):
    """Create a test ZIP file with mock CVs"""
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for i in range(num_cvs):
            cv_content = f"Candidate {i}\nExperience: {i+2} years\nSkills: Python, Java, React"
            cv_filename = f"cv_{i}.txt"
            zipf.writestr(cv_filename, cv_content)
    return num_cvs

def test_integration_cleanup():
    """Test that cleanup works in the actual job processing flow"""
    print("\n=== Integration Test: Full Job Processing with Cleanup ===")
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.TemporaryDirectory() as db_dir:
            # Configure test environment
            original_upload = app.UPLOAD_FOLDER
            original_db = app.DB_PATH
            
            app.UPLOAD_FOLDER = temp_dir
            test_db = os.path.join(db_dir, "test.db")
            app.DB_PATH = test_db
            
            # Initialize test database
            import src.database as database
            database.DB_PATH = test_db
            init_db()
            
            try:
                # Create a test ZIP with CVs
                zip_path = os.path.join(db_dir, "test_cvs.zip")
                num_cvs = create_test_zip(zip_path, num_cvs=3)
                print(f"Created test ZIP with {num_cvs} CVs")
                
                # Simulate job creation
                with app.get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO jobs (title, description, status, total_files) VALUES (?, ?, ?, ?)",
                             ("Test Job", "Python developer with React", "Processing", 0))
                    job_id = c.lastrowid
                    conn.commit()
                
                print(f"Created job {job_id}")
                
                # Extract and process
                job_dir = os.path.join(temp_dir, str(job_id))
                os.makedirs(job_dir, exist_ok=True)
                
                # Copy zip to job directory
                import shutil
                job_zip = os.path.join(job_dir, "cv_archive.zip")
                shutil.copy(zip_path, job_zip)
                
                # Extract CVs
                extract_dir = os.path.join(job_dir, "extracted")
                cv_files = app.extract_and_find_cvs(job_zip, extract_dir)
                
                print(f"Extracted {len(cv_files)} CV files")
                
                # Verify files exist before processing
                assert os.path.exists(job_dir), "Job directory should exist before processing"
                assert os.path.exists(extract_dir), "Extract directory should exist"
                assert len(cv_files) == num_cvs, f"Should have {num_cvs} CVs"
                
                # Process job (this should trigger cleanup in finally block)
                app.process_job_thread(job_id, "Python developer with React", cv_files, ["Python"])
                
                # Give cleanup a moment to complete
                time.sleep(0.5)
                
                # Verify cleanup happened
                job_dir_exists = os.path.exists(job_dir)
                
                print(f"Job directory exists after processing: {job_dir_exists}")
                
                # Verify database still has job data
                with app.get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("SELECT status, processed_files FROM jobs WHERE id=?", (job_id,))
                    job = c.fetchone()
                    
                    c.execute("SELECT COUNT(*) FROM candidates WHERE job_id=?", (job_id,))
                    candidate_count = c.fetchone()[0]
                
                print(f"Job status: {job[0]}, Processed: {job[1]}")
                print(f"Candidates in database: {candidate_count}")
                
                # Verify results
                success = (
                    not job_dir_exists and  # Files cleaned up
                    job[0] == 'Completed' and  # Job completed
                    job[1] == num_cvs and  # All files processed
                    candidate_count > 0  # Candidates saved to DB
                )
                
                if success:
                    print("✓ Integration test passed!")
                    print("  - Files properly cleaned up after processing")
                    print("  - Job marked as completed")
                    print("  - Candidate data preserved in database")
                else:
                    print("✗ Integration test failed")
                    print(f"  - Files cleaned: {not job_dir_exists}")
                    print(f"  - Job completed: {job[0] == 'Completed'}")
                    print(f"  - All processed: {job[1] == num_cvs}")
                    print(f"  - Candidates saved: {candidate_count > 0}")
                
                return success
                
            finally:
                # Restore original configuration
                app.UPLOAD_FOLDER = original_upload
                app.DB_PATH = original_db
                database.DB_PATH = original_db

def test_cleanup_on_error():
    """Test that cleanup happens even when job processing fails"""
    print("\n=== Test: Cleanup on Error ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with tempfile.TemporaryDirectory() as db_dir:
            original_upload = app.UPLOAD_FOLDER
            original_db = app.DB_PATH
            
            app.UPLOAD_FOLDER = temp_dir
            test_db = os.path.join(db_dir, "test_error.db")
            app.DB_PATH = test_db
            
            import src.database as database
            database.DB_PATH = test_db
            init_db()
            
            try:
                # Create job directory with files
                job_id = 999
                job_dir = os.path.join(temp_dir, str(job_id))
                os.makedirs(job_dir, exist_ok=True)
                
                # Create some test files
                test_file = os.path.join(job_dir, "test.txt")
                with open(test_file, 'w') as f:
                    f.write("Test content")
                
                # Verify files exist
                assert os.path.exists(job_dir), "Job directory should exist"
                
                # Create a job in database
                with app.get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO jobs (id, title, description, status, total_files) VALUES (?, ?, ?, ?, ?)",
                             (job_id, "Error Test", "Test", "Processing", 0))
                    conn.commit()
                
                # Try to process with invalid CV files (should cause errors but cleanup should still run)
                try:
                    app.process_job_thread(job_id, "Test description", [], ["Python"])
                except Exception as e:
                    print(f"Expected error during processing: {e}")
                
                # Give cleanup time to run
                time.sleep(0.5)
                
                # Verify cleanup happened even though processing had issues
                job_dir_exists = os.path.exists(job_dir)
                
                if not job_dir_exists:
                    print("✓ Cleanup occurred even with errors in processing")
                    return True
                else:
                    print("✗ Cleanup did not occur after error")
                    return False
                
            finally:
                app.UPLOAD_FOLDER = original_upload
                app.DB_PATH = original_db
                database.DB_PATH = original_db

if __name__ == "__main__":
    print("Running integration tests for cleanup functionality...")
    
    tests = [
        test_integration_cleanup,
        test_cleanup_on_error
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*60)
    print(f"Integration tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All integration tests passed!")
        sys.exit(0)
    else:
        print("✗ Some integration tests failed")
        sys.exit(1)

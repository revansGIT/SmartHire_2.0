#!/usr/bin/env python3
"""
Test script for cleanup functionality
Tests that cleanup_job_files correctly removes job directories and logs appropriately
"""

import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock the UPLOAD_FOLDER for testing
import src.app as app

def test_cleanup_nonexistent_job():
    """Test cleanup when job directory doesn't exist"""
    print("\n=== Test 1: Cleanup non-existent job ===")
    
    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload = app.UPLOAD_FOLDER
        app.UPLOAD_FOLDER = temp_dir
        
        # Try to cleanup a job that doesn't exist
        result = app.cleanup_job_files(99999)
        
        app.UPLOAD_FOLDER = original_upload
        
        if result:
            print("✓ Test 1 passed: Cleanup handles non-existent job gracefully")
        else:
            print("✗ Test 1 failed")
        return result

def test_cleanup_with_files():
    """Test cleanup when job directory exists with files"""
    print("\n=== Test 2: Cleanup existing job with files ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload = app.UPLOAD_FOLDER
        app.UPLOAD_FOLDER = temp_dir
        
        # Create a mock job directory with files
        job_id = 1
        job_dir = os.path.join(temp_dir, str(job_id))
        os.makedirs(job_dir, exist_ok=True)
        
        # Create some mock files
        with open(os.path.join(job_dir, "test.txt"), "w") as f:
            f.write("Test content" * 100)
        
        # Create subdirectory with files (like extracted/)
        extracted_dir = os.path.join(job_dir, "extracted")
        os.makedirs(extracted_dir, exist_ok=True)
        with open(os.path.join(extracted_dir, "cv1.pdf"), "w") as f:
            f.write("Mock CV content" * 100)
        with open(os.path.join(extracted_dir, "cv2.pdf"), "w") as f:
            f.write("Mock CV content" * 100)
        
        # Verify directory exists before cleanup
        assert os.path.exists(job_dir), "Job directory should exist before cleanup"
        
        # Perform cleanup
        result = app.cleanup_job_files(job_id)
        
        # Verify directory is removed
        dir_exists = os.path.exists(job_dir)
        
        app.UPLOAD_FOLDER = original_upload
        
        if result and not dir_exists:
            print("✓ Test 2 passed: Cleanup successfully removes job directory")
        else:
            print(f"✗ Test 2 failed: result={result}, dir_exists={dir_exists}")
        
        return result and not dir_exists

def test_cleanup_with_nested_structure():
    """Test cleanup with deeply nested directory structure"""
    print("\n=== Test 3: Cleanup with nested directory structure ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload = app.UPLOAD_FOLDER
        app.UPLOAD_FOLDER = temp_dir
        
        # Create a complex nested structure
        job_id = 2
        job_dir = os.path.join(temp_dir, str(job_id))
        os.makedirs(job_dir, exist_ok=True)
        
        # Create nested directories
        nested = os.path.join(job_dir, "extracted", "subfolder", "deep")
        os.makedirs(nested, exist_ok=True)
        
        # Add files at different levels
        with open(os.path.join(job_dir, "archive.zip"), "w") as f:
            f.write("Z" * 1000)
        with open(os.path.join(nested, "deep_cv.pdf"), "w") as f:
            f.write("Deep content")
        
        # Perform cleanup
        result = app.cleanup_job_files(job_id)
        
        # Verify complete removal
        dir_exists = os.path.exists(job_dir)
        
        app.UPLOAD_FOLDER = original_upload
        
        if result and not dir_exists:
            print("✓ Test 3 passed: Cleanup handles nested structures")
        else:
            print(f"✗ Test 3 failed: result={result}, dir_exists={dir_exists}")
        
        return result and not dir_exists

def test_cleanup_concurrent_jobs():
    """Test that cleanup only affects the specified job"""
    print("\n=== Test 4: Cleanup doesn't affect other jobs ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload = app.UPLOAD_FOLDER
        app.UPLOAD_FOLDER = temp_dir
        
        # Create multiple job directories
        job1_dir = os.path.join(temp_dir, "1")
        job2_dir = os.path.join(temp_dir, "2")
        job3_dir = os.path.join(temp_dir, "3")
        
        for job_dir in [job1_dir, job2_dir, job3_dir]:
            os.makedirs(job_dir, exist_ok=True)
            with open(os.path.join(job_dir, "data.txt"), "w") as f:
                f.write("Job data")
        
        # Cleanup only job 2
        result = app.cleanup_job_files(2)
        
        # Verify only job 2 is removed
        job1_exists = os.path.exists(job1_dir)
        job2_exists = os.path.exists(job2_dir)
        job3_exists = os.path.exists(job3_dir)
        
        app.UPLOAD_FOLDER = original_upload
        
        if result and job1_exists and not job2_exists and job3_exists:
            print("✓ Test 4 passed: Cleanup is job-specific, doesn't affect other jobs")
        else:
            print(f"✗ Test 4 failed: result={result}, job1={job1_exists}, job2={job2_exists}, job3={job3_exists}")
        
        return result and job1_exists and not job2_exists and job3_exists

if __name__ == "__main__":
    print("Running cleanup functionality tests...")
    
    tests = [
        test_cleanup_nonexistent_job,
        test_cleanup_with_files,
        test_cleanup_with_nested_structure,
        test_cleanup_concurrent_jobs
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All cleanup tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)

#!/usr/bin/env python3
"""
Performance test script for SmartHire 2.0 optimizations
Tests the key optimization improvements made
"""

import sys
import os
import time
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import (
    get_compiled_pattern, 
    score_candidate, 
    extract_text,
    get_db_connection
)
from skills_master import SKILLS

def test_regex_pattern_caching():
    """Test that regex patterns are properly cached"""
    print("\n=== Testing Regex Pattern Caching ===")
    
    # First call should create the pattern
    start = time.time()
    pattern1 = get_compiled_pattern("python")
    time1 = time.time() - start
    
    # Second call should retrieve from cache
    start = time.time()
    pattern2 = get_compiled_pattern("python")
    time2 = time.time() - start
    
    print(f"First call (create): {time1*1000:.4f}ms")
    print(f"Second call (cache): {time2*1000:.4f}ms")
    print(f"Speed improvement: {time1/time2:.2f}x faster")
    
    assert pattern1 is pattern2, "Patterns should be the same object (cached)"
    print("✓ Regex caching working correctly")
    
    return True

def test_job_desc_preprocessing():
    """Test that job description preprocessing optimization works"""
    print("\n=== Testing Job Description Preprocessing ===")
    
    job_desc = """
    We are looking for a Python developer with React experience.
    Must have: Django, PostgreSQL
    Nice to have: Docker, AWS
    """
    
    resume_text = """
    experienced python developer with 5 years of experience.
    worked with django, flask, postgresql, and docker.
    frontend: react, vue, javascript
    cloud: aws, azure
    """.lower()
    
    must_haves = ["python", "django"]
    
    # Test without preprocessing (old way)
    start = time.time()
    score1, missing1, skills1 = score_candidate(job_desc, resume_text, must_haves)
    time1 = time.time() - start
    
    # Test with preprocessing (new way)
    job_desc_lower = job_desc.lower()
    skills_in_job_desc = set()
    for skill in SKILLS.keys():
        if len(skill.strip()) > 1:
            pattern = get_compiled_pattern(skill.lower())
            if pattern.search(job_desc_lower):
                skills_in_job_desc.add(skill.lower())
    
    start = time.time()
    score2, missing2, skills2 = score_candidate(
        job_desc, resume_text, must_haves,
        job_desc_lower=job_desc_lower,
        skills_in_job_desc=skills_in_job_desc
    )
    time2 = time.time() - start
    
    print(f"Without preprocessing: {time1*1000:.2f}ms")
    print(f"With preprocessing: {time2*1000:.2f}ms")
    print(f"Score: {score2}, Missing: {missing2}")
    print(f"Found skills: {skills2[:5]}")
    
    assert score1 == score2, "Scores should be identical"
    assert missing1 == missing2, "Missing skills should be identical"
    
    print("✓ Job description preprocessing working correctly")
    
    return True

def test_text_extraction_optimization():
    """Test optimized text extraction"""
    print("\n=== Testing Text Extraction Optimization ===")
    
    # Create a test text file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Python developer\n\nReact expert\n\n\nDjango experience\n")
        temp_file = f.name
    
    try:
        start = time.time()
        text = extract_text(temp_file)
        elapsed = time.time() - start
        
        print(f"Extraction time: {elapsed*1000:.2f}ms")
        print(f"Extracted text: '{text[:50]}...'")
        
        assert "python" in text, "Should contain python"
        assert "react" in text, "Should contain react"
        assert "django" in text, "Should contain django"
        
        print("✓ Text extraction working correctly")
        
        return True
    finally:
        os.unlink(temp_file)

def test_db_connection_context_manager():
    """Test database connection context manager"""
    print("\n=== Testing Database Connection Context Manager ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1, "Should return 1"
        
        print("✓ Database context manager working correctly")
        return True
    except Exception as e:
        print(f"✗ Database context manager failed: {e}")
        return False

def benchmark_scoring_speed():
    """Benchmark the scoring function speed"""
    print("\n=== Benchmarking Scoring Speed ===")
    
    job_desc = """
    Senior Python Developer position
    Required: Python, Django, PostgreSQL, React, Docker
    Experience: 5+ years
    Cloud: AWS or Azure
    """
    
    resumes = [
        "python django developer 7 years postgresql react docker aws expert",
        "java spring boot developer kubernetes microservices",
        "react frontend developer javascript typescript node.js",
        "python data scientist pandas numpy sklearn tensorflow",
        "full stack developer python react postgresql docker"
    ]
    
    # Pre-process job description (optimization)
    job_desc_lower = job_desc.lower()
    skills_in_job_desc = set()
    for skill in SKILLS.keys():
        if len(skill.strip()) > 1:
            pattern = get_compiled_pattern(skill.lower())
            if pattern.search(job_desc_lower):
                skills_in_job_desc.add(skill.lower())
    
    print(f"Skills in job description: {len(skills_in_job_desc)}")
    
    # Benchmark
    start = time.time()
    results = []
    for resume in resumes:
        score, missing, found = score_candidate(
            job_desc, resume.lower(), ["python", "django"],
            job_desc_lower=job_desc_lower,
            skills_in_job_desc=skills_in_job_desc
        )
        results.append((score, len(found)))
    
    elapsed = time.time() - start
    avg_time = elapsed / len(resumes)
    
    print(f"\nProcessed {len(resumes)} resumes in {elapsed*1000:.2f}ms")
    print(f"Average time per resume: {avg_time*1000:.2f}ms")
    print(f"Estimated throughput: {1/avg_time:.1f} resumes/second")
    
    print("\nScores:")
    for i, (score, skill_count) in enumerate(results):
        print(f"  Resume {i+1}: Score={score:.1f}, Skills={skill_count}")
    
    print("✓ Benchmark completed")
    
    return True

def main():
    """Run all performance tests"""
    print("=" * 60)
    print("SmartHire 2.0 Performance Optimization Tests")
    print("=" * 60)
    
    tests = [
        ("Regex Pattern Caching", test_regex_pattern_caching),
        ("Job Description Preprocessing", test_job_desc_preprocessing),
        ("Text Extraction", test_text_extraction_optimization),
        ("DB Connection Manager", test_db_connection_context_manager),
        ("Scoring Speed Benchmark", benchmark_scoring_speed),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"✗ {name} ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

# Performance Best Practices for SmartHire 2.0

## Quick Reference for Developers

### When Adding New Features

#### ✓ DO:
1. **Use the pattern cache** when adding new regex searches:
   ```python
   pattern = get_compiled_pattern(skill.lower())
   if pattern.search(text):
       # Match found
   ```

2. **Use database context managers** for all DB operations:
   ```python
   with get_db_connection() as conn:
       cursor = conn.cursor()
       # Your operations
       conn.commit()
   ```

3. **Batch database operations** when inserting multiple records:
   ```python
   batch = []
   for item in items:
       batch.append((value1, value2))
       if len(batch) >= 100:
           cursor.executemany("INSERT INTO ...", batch)
           conn.commit()
           batch = []
   ```

4. **Pre-compute expensive operations** when processing multiple items:
   ```python
   # Compute once
   job_desc_lower = job_desc.lower()
   
   # Reuse many times
   for resume in resumes:
       score = score_candidate(..., job_desc_lower=job_desc_lower)
   ```

#### ✗ DON'T:
1. **Don't compile regex in loops**:
   ```python
   # BAD
   for text in texts:
       if re.search(r'\bpython\b', text):  # Compiles every time!
           
   # GOOD
   pattern = get_compiled_pattern("python")  # Compile once
   for text in texts:
       if pattern.search(text):
   ```

2. **Don't open/close DB connections repeatedly**:
   ```python
   # BAD
   for item in items:
       conn = sqlite3.connect(DB_PATH)
       # operation
       conn.close()
       
   # GOOD
   with get_db_connection() as conn:
       for item in items:
           # operations
   ```

3. **Don't call expensive operations in tight loops**:
   ```python
   # BAD
   for resume in resumes:
       job_lower = job_desc.lower()  # Repeats 1000 times!
       
   # GOOD
   job_lower = job_desc.lower()  # Once
   for resume in resumes:
       # use job_lower
   ```

### Performance Testing

Run performance tests before committing:
```bash
python test_performance.py
```

Expected results:
- Regex caching: >50x faster
- Job preprocessing: >3x faster
- Throughput: >500 resumes/second

### Common Pitfalls

1. **List Comprehensions with Or Operator**
   - BAD: `[p.text or "" for p in pages]`
   - GOOD: `[p.text for p in pages if p.text]`

2. **String Concatenation in Loops**
   - BAD: `text = ""; for p in pages: text += p.text`
   - GOOD: `text = " ".join([p.text for p in pages])`

3. **Multiple Database Commits**
   - BAD: `for item in items: insert(); conn.commit()`
   - GOOD: Batch inserts every 100 records

### Memory Management

Monitor these if you add new caches:
- Pattern cache: Bounded by SKILLS dict size (~200 max)
- Don't cache large objects (resume text, etc.)
- Use context managers for automatic cleanup

### Profiling

To profile new code:
```python
import time
start = time.time()
# Your code
elapsed = time.time() - start
print(f"Took {elapsed*1000:.2f}ms")
```

For detailed profiling:
```python
import cProfile
cProfile.run('your_function()')
```

### When in Doubt

- Use built-in Python optimizations (tuple.endswith vs any)
- Pre-compute outside loops
- Batch operations
- Use context managers
- Cache compiled patterns/expensive computations
- Profile before and after changes

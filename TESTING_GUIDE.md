# Testing Guide for Cleanup Functionality

## Quick Verification

### 1. Run All Tests (Recommended)
```bash
cd backend

# Run unit tests
python test_cleanup.py

# Run integration tests  
python test_integration_cleanup.py

# Run demonstration
python demo_cleanup.py
```

Expected: All tests pass ✓

### 2. Verify Server Starts
```bash
cd backend/src
python app.py
```

Expected: Server starts without errors, shows endpoints list

### 3. Manual Testing (Optional)

Create a test job and verify cleanup:

```bash
# Start the server
cd backend/src
python app.py

# In another terminal, upload a test ZIP
# (Use the frontend or curl to POST to /upload-zip)

# Check logs for cleanup message:
# [CLEANUP] Successfully deleted job X files (Y MB freed)
```

## Test Coverage

### Unit Tests (`test_cleanup.py`)
- ✓ Cleanup non-existent job
- ✓ Cleanup with files
- ✓ Nested directory structures  
- ✓ Job-specific cleanup (no interference)

### Integration Tests (`test_integration_cleanup.py`)
- ✓ Full job processing with cleanup
- ✓ Cleanup on processing errors

### Demonstration (`demo_cleanup.py`)
- ✓ Realistic scenario with 20 CVs
- ✓ Shows storage freed
- ✓ Verifies database integrity

## Expected Log Output

When a job completes, you should see:

```
=== Job 1 Summary ===
Total processed: 20
Candidates saved: 20

Sample skill matches:
  candidate_1.pdf: 85.3 - Skills: ['python', 'react', 'sql']
  ...
Job 1 Completed.

[CLEANUP] Starting cleanup for job 1...
[CLEANUP] Successfully deleted job 1 files (245.32 MB freed)
```

## Troubleshooting

### Tests Fail
- Ensure dependencies installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (3.8+ required)

### Cleanup Doesn't Run
- Check logs for errors
- Verify uploads/ directory has proper permissions
- Ensure job_id is valid

### Files Not Deleted
- Check error in logs: `[CLEANUP] Error deleting job X files: <error>`
- Verify no processes have files open
- Check file permissions

## Production Verification

After deploying to Render:

1. Upload a test job
2. Wait for completion
3. Check application logs for cleanup message
4. Verify uploads/ directory remains small
5. Confirm candidate data in database

## Success Criteria

- ✓ All tests pass locally
- ✓ Server starts without errors
- ✓ Cleanup logs appear after job completion
- ✓ Files removed from uploads/
- ✓ Candidate data in database
- ✓ No error messages in logs

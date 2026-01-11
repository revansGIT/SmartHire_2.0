import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function App() {
  const [jobDescription, setJobDescription] = useState('');
  const [mustHaves, setMustHaves] = useState('');
  const [zipFile, setZipFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Poll for job status
  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const statusRes = await axios.get(`${API_URL}/job-status/${jobId}`);
        setStatus(statusRes.data);

        if (statusRes.data.status === 'Completed') {
          const shortlistRes = await axios.get(`${API_URL}/shortlist/${jobId}`);
          setCandidates(shortlistRes.data.top_5 || []);
          clearInterval(interval);
          setLoading(false);
        }
      } catch (err) {
        console.error('Error fetching status:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.zip')) {
      setZipFile(file);
      setError(null);
    } else {
      setError('Please select a valid ZIP file');
      setZipFile(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!zipFile) {
      setError('Please select a ZIP file containing CVs');
      return;
    }

    if (!jobDescription.trim()) {
      setError('Please enter a job description');
      return;
    }

    setLoading(true);
    setError(null);
    setJobId(null);
    setStatus(null);
    setCandidates([]);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('zip_file', zipFile);
    formData.append('description', jobDescription);
    formData.append('must_haves', mustHaves);

    try {
      const response = await axios.post(`${API_URL}/upload-zip`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        },
      });

      setJobId(response.data.job_id);
      setUploadProgress(100);
    } catch (err) {
      setError(err.response?.data?.error || 'Error uploading file. Please try again.');
      setLoading(false);
    }
  };

  const handleReset = () => {
    setJobDescription('');
    setMustHaves('');
    setZipFile(null);
    setJobId(null);
    setStatus(null);
    setCandidates([]);
    setLoading(false);
    setError(null);
    setUploadProgress(0);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎯 SmartHire 2.0</h1>
        <p className="tagline">AI-Powered Resume Screening System</p>
      </header>

      <main className="main-content">
        {!jobId ? (
          <div className="upload-section">
            <h2>Create New Screening Job</h2>
            <form onSubmit={handleSubmit} className="job-form">
              <div className="form-group">
                <label htmlFor="jobDescription">
                  Job Description <span className="required">*</span>
                </label>
                <textarea
                  id="jobDescription"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Enter the complete job description, including required skills, responsibilities, and qualifications..."
                  rows="8"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="mustHaves">
                  Must-Have Skills (comma-separated)
                </label>
                <input
                  type="text"
                  id="mustHaves"
                  value={mustHaves}
                  onChange={(e) => setMustHaves(e.target.value)}
                  placeholder="e.g., Python, React, AWS, 5 years experience"
                />
                <small className="help-text">
                  Candidates without these skills will receive significantly lower scores
                </small>
              </div>

              <div className="form-group">
                <label htmlFor="zipFile">
                  Upload CVs (ZIP file) <span className="required">*</span>
                </label>
                <div className="file-upload-wrapper">
                  <input
                    type="file"
                    id="zipFile"
                    accept=".zip"
                    onChange={handleFileChange}
                    required
                  />
                  {zipFile && (
                    <div className="file-info">
                      <span className="file-name">📁 {zipFile.name}</span>
                      <span className="file-size">
                        ({(zipFile.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </div>
                  )}
                </div>
                <small className="help-text">
                  Supported formats: PDF, DOCX, TXT inside ZIP archive
                </small>
              </div>

              {error && <div className="error-message">{error}</div>}

              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? 'Processing...' : 'Start Screening'}
              </button>
            </form>
          </div>
        ) : (
          <div className="results-section">
            <div className="status-card">
              <h2>Processing Job #{jobId}</h2>
              
              {uploadProgress < 100 ? (
                <div className="progress-container">
                  <div className="progress-label">Uploading...</div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <div className="progress-percentage">{uploadProgress}%</div>
                </div>
              ) : status ? (
                <div className="status-info">
                  <div className="status-badge" data-status={status.status.toLowerCase()}>
                    {status.status}
                  </div>
                  
                  {status.status === 'Processing' && (
                    <div className="progress-container">
                      <div className="progress-label">
                        Analyzing Resumes: {status.processed} / {status.total}
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${status.percentage}%` }}
                        />
                      </div>
                      <div className="progress-percentage">{status.percentage}%</div>
                    </div>
                  )}

                  {status.status === 'Completed' && (
                    <div className="completion-message">
                      ✅ Analysis complete! Processed {status.total} resumes.
                    </div>
                  )}
                </div>
              ) : (
                <div className="loading-spinner">Loading...</div>
              )}
            </div>

            {candidates.length > 0 && (
              <div className="candidates-section">
                <h2>🏆 Top 5 Candidates</h2>
                <div className="candidates-list">
                  {candidates.map((candidate, index) => (
                    <div key={candidate.id} className="candidate-card">
                      <div className="candidate-rank">#{index + 1}</div>
                      <div className="candidate-info">
                        <h3 className="candidate-name">{candidate.filename}</h3>
                        <div className="candidate-score">
                          <div className="score-label">Match Score</div>
                          <div className="score-value">{candidate.score.toFixed(1)}%</div>
                        </div>
                        
                        {candidate.found_skills && JSON.parse(candidate.found_skills).length > 0 && (
                          <div className="skills-found">
                            <strong>Skills Found:</strong>
                            <div className="skills-tags">
                              {JSON.parse(candidate.found_skills).slice(0, 10).map((skill, i) => (
                                <span key={i} className="skill-tag">{skill}</span>
                              ))}
                              {JSON.parse(candidate.found_skills).length > 10 && (
                                <span className="skill-tag more">
                                  +{JSON.parse(candidate.found_skills).length - 10} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}

                        {candidate.missing_skills && JSON.parse(candidate.missing_skills).length > 0 && (
                          <div className="missing-skills">
                            <strong>Missing Must-Haves:</strong>
                            <div className="skills-tags">
                              {JSON.parse(candidate.missing_skills).map((skill, i) => (
                                <span key={i} className="skill-tag missing">{skill}</span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button onClick={handleReset} className="reset-btn">
              Start New Screening
            </button>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>
          SmartHire 2.0 - Powered by AI | Processing Speed: ~890 resumes/second
        </p>
      </footer>
    </div>
  );
}

export default App;

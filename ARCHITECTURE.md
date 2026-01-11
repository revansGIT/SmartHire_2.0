# 🏗️ SmartHire 2.0 Architecture

This document describes the architecture, design decisions, and technical implementation of SmartHire 2.0.

## 📐 System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                    (React Frontend - SPA)                    │
└────────────────┬───────────────────────────┬────────────────┘
                 │                           │
                 │ HTTP/AJAX                 │ WebSocket-like
                 │ (File Upload)             │ (Polling)
                 │                           │
┌────────────────▼───────────────────────────▼────────────────┐
│                     Flask Backend API                        │
│              (RESTful API + Background Tasks)                │
├──────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │   CORS     │  │  File      │  │  Text Extraction       │ │
│  │  Handler   │  │  Upload    │  │  (PDF/DOCX/TXT)        │ │
│  └────────────┘  └────────────┘  └────────────────────────┘ │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │  Job       │  │  Scoring   │  │  Skill Matching        │ │
│  │  Manager   │  │  Engine    │  │  (200+ skills)         │ │
│  └────────────┘  └────────────┘  └────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Background Worker (Threading)                   │ │
│  │         - Processes CVs asynchronously                  │ │
│  │         - Updates progress in real-time                 │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ SQLite
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                     SQLite Database                          │
│  ┌────────────────┐        ┌──────────────────────────────┐ │
│  │  jobs          │        │  candidates                   │ │
│  │  - id          │        │  - id                         │ │
│  │  - description │        │  - job_id (FK)                │ │
│  │  - status      │        │  - filename                   │ │
│  │  - progress    │        │  - score                      │ │
│  └────────────────┘        │  - found_skills               │ │
│                            │  - missing_skills             │ │
│                            └──────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## 🎨 Frontend Architecture (React)

### Technology Stack

- **Framework**: React 19.x
- **Build Tool**: Vite (fast, modern bundler)
- **HTTP Client**: Axios
- **Styling**: CSS3 with CSS Variables
- **State Management**: React Hooks (useState, useEffect)

### Component Structure

```
App.jsx (Main Component)
├── Header Section
│   └── Title + Tagline
│
├── Upload Section (Initial State)
│   ├── Job Description Form
│   ├── Must-Have Skills Input
│   └── ZIP File Upload
│
├── Results Section (After Upload)
│   ├── Status Card
│   │   ├── Upload Progress Bar
│   │   └── Processing Progress Bar
│   │
│   └── Candidates List
│       └── Candidate Cards
│           ├── Rank Badge
│           ├── Score Display
│           ├── Found Skills Tags
│           └── Missing Skills Tags
│
└── Footer Section
```

### State Management

**Application State**:
- `jobDescription`: Job description text
- `mustHaves`: Must-have skills list
- `zipFile`: Selected ZIP file
- `jobId`: Current job ID
- `status`: Processing status
- `candidates`: Top 5 candidates
- `loading`: Loading state
- `error`: Error messages
- `uploadProgress`: Upload percentage

**Data Flow**:
1. User fills form → State updates
2. User submits → API call
3. Backend responds → jobId stored
4. Polling starts → Status updated every 2s
5. Job completes → Candidates fetched
6. Results displayed → Polling stops

### Key Features

**Real-time Progress**:
- Uses `setInterval` to poll `/job-status/:id` every 2 seconds
- Displays upload progress separately from processing progress
- Automatically stops polling when job completes

**Error Handling**:
- Form validation before submission
- Network error handling
- User-friendly error messages

**Responsive Design**:
- Mobile-first approach
- Breakpoints at 768px and 480px
- Flexbox and Grid layouts
- Touch-friendly UI elements

## ⚙️ Backend Architecture (Flask)

### Technology Stack

- **Framework**: Flask 2.x
- **CORS**: Flask-CORS
- **Database**: SQLite3
- **ML Libraries**: scikit-learn (TF-IDF, Cosine Similarity)
- **Text Extraction**: pdfplumber, python-docx
- **Environment**: python-dotenv
- **Threading**: Python threading module

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload-zip` | POST | Upload ZIP and start job |
| `/job-status/:id` | GET | Get job processing status |
| `/shortlist/:id` | GET | Get top 5 candidates |
| `/debug/job/:id` | GET | Debug endpoint (all candidates) |

### Request Flow

```
1. Client uploads ZIP
   ↓
2. Flask receives multipart/form-data
   ↓
3. Create job record in database
   ↓
4. Save and extract ZIP file
   ↓
5. Find all CV files (.pdf, .docx, .txt)
   ↓
6. Start background thread
   ↓
7. Return job_id to client
   ↓
8. Background thread processes CVs:
   - Extract text from each file
   - Score against job description
   - Batch insert to database
   - Update progress periodically
   ↓
9. Client polls for status
   ↓
10. Return top 5 when complete
```

### Scoring Algorithm

**Multi-Factor Scoring System**:

```python
final_score = normalized_cosine_score + normalized_skill_score
              - must_have_penalty + bonus_points

Where:
- normalized_cosine_score: TF-IDF similarity (0-50 range)
- normalized_skill_score: Weighted skill matching (0-50 range)
- must_have_penalty: 80% reduction per missing critical skill
- bonus_points: Extra points for high-demand skills
```

**Skill Matching Logic**:
1. Skills in job description get 15x weight
2. Other skills get 5x weight
3. Weight multiplied by skill importance (from skills_master.py)
4. Normalized to 0-50 scale

**Performance Optimizations**:
- Regex pattern caching (85x faster)
- Job description pre-processing (5.2x faster)
- Batch database operations (90% less I/O)
- Single-pass skill matching

### Database Schema

**jobs table**:
```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    status TEXT,  -- 'Processing' or 'Completed'
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0
);
```

**candidates table**:
```sql
CREATE TABLE candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    filename TEXT,
    score REAL,
    missing_skills TEXT,  -- JSON array
    is_shortlisted BOOLEAN,
    found_skills TEXT  -- JSON array
);
```

### Background Processing

**Threading Strategy**:
- Main thread handles HTTP requests
- Background thread processes CVs
- Thread-safe database operations via context managers
- Daemon thread (allows clean shutdown)

**Progress Tracking**:
- Updates database every 50 files
- Real-time status via polling endpoint
- Atomic operations for consistency

## 🔄 Data Flow

### Complete User Journey

```
1. User lands on homepage
   ↓
2. Fills job description form
   ↓
3. Selects must-have skills (optional)
   ↓
4. Uploads ZIP file with CVs
   ↓
5. Frontend validates inputs
   ↓
6. Frontend sends POST /upload-zip
   ↓
7. Backend creates job record
   ↓
8. Backend starts background processing
   ↓
9. Backend returns job_id
   ↓
10. Frontend starts polling GET /job-status/:id
    ↓
11. Frontend displays progress (0% → 100%)
    ↓
12. Backend processes all CVs:
    - Extract text
    - Calculate scores
    - Store in database
    ↓
13. Backend marks job as 'Completed'
    ↓
14. Frontend detects completion
    ↓
15. Frontend fetches GET /shortlist/:id
    ↓
16. Frontend displays Top 5 candidates
    ↓
17. User reviews results
    ↓
18. User can start new job (loop back to step 2)
```

## 🚀 Performance Characteristics

### Frontend Performance

- **Bundle Size**: ~200KB (production build)
- **Initial Load**: <1s (Vite HMR in dev)
- **Render Time**: <100ms for state updates
- **Network Requests**: Minimal (polling only)

### Backend Performance

- **Throughput**: ~890 resumes/second
- **Latency**: ~1.1ms per resume
- **Memory**: <50MB for 10,000 resumes
- **Concurrency**: 4 workers (Gunicorn)

### Scaling Considerations

**Current Limitations**:
- Single SQLite database
- In-memory regex cache
- File-based storage

**Scaling Solutions**:
- PostgreSQL for multi-user
- Redis for caching
- S3/Cloud storage for files
- Message queue (Celery) for background tasks
- Load balancer for multiple backend instances

## 🔒 Security Features

### Input Validation

- File type checking (.zip only)
- File size limits (500MB default)
- ZIP bomb protection (implicit via size limit)
- SQL injection prevention (parameterized queries)

### CORS Configuration

- Whitelist specific origins
- Controlled methods (GET, POST)
- Credentials support
- Preflight handling

### Data Protection

- No PII stored (only filenames)
- Temporary file cleanup
- Database connection pooling
- Context managers for resource cleanup

## 📊 Design Decisions

### Why React + Flask?

**React**:
- Component-based architecture
- Rich ecosystem
- Fast development with Vite
- Excellent for SPAs

**Flask**:
- Lightweight and flexible
- Python ML ecosystem
- Easy to learn and deploy
- Perfect for RESTful APIs

### Why SQLite?

- Zero configuration
- Single file database
- Perfect for small-medium scale
- Easy backup and migration
- Sufficient for thesis/demo

### Why Threading (not Celery)?

- Simpler deployment
- No external dependencies
- Sufficient for single server
- Easy to understand and debug

### Why Polling (not WebSockets)?

- Simpler implementation
- Works with any hosting
- No persistent connections
- Easier to debug
- Sufficient for 2s intervals

## 🎯 Future Enhancements

### Phase 1 (MVP+)
- [ ] Export results to PDF/Excel
- [ ] User authentication
- [ ] Multiple job management
- [ ] Resume preview

### Phase 2 (Scale)
- [ ] PostgreSQL migration
- [ ] Redis caching
- [ ] Celery for background tasks
- [ ] WebSocket real-time updates

### Phase 3 (Features)
- [ ] Email notifications
- [ ] Interview scheduling
- [ ] Custom skill databases
- [ ] Analytics dashboard
- [ ] Multi-language support

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [scikit-learn TF-IDF](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [Performance Optimizations](PERFORMANCE_OPTIMIZATIONS.md)

---

**Architecture Version**: 2.0  
**Last Updated**: 2024  
**Status**: Production Ready

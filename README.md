# SmartHire 2.0 - AI-Powered Resume Screening System

A production-ready web application that uses AI and machine learning to automatically screen and rank CVs/resumes against job descriptions. Built with React frontend and Flask backend.

![SmartHire 2.0](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![React](https://img.shields.io/badge/React-19.x-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features
- **🚀 High Performance**: Processes ~890 resumes per second (8.9x faster than baseline)
- **🎯 Smart Matching**: Uses TF-IDF and cosine similarity for intelligent resume ranking
- **💼 Skill Analysis**: Automatically extracts and matches technical skills
- **📊 Real-time Progress**: Live progress tracking with WebSocket-like polling
- **📱 Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **🔒 Production Ready**: Environment-based configuration, CORS support, error handling

## 🏗️ Architecture

```
SmartHire_2.0/
├── frontend/              # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx       # Main application component
│   │   ├── App.css       # Styles and responsive design
│   │   └── main.jsx      # Application entry point
│   ├── package.json
│   └── vite.config.js
│
├── backend/               # Flask backend API
│   ├── src/
│   │   ├── app.py        # Main Flask application
│   │   ├── database.py   # Database initialization
│   │   └── skills_master.py  # Skills database
│   ├── requirements.txt
│   └── test_performance.py
│
└── docs/                  # Documentation
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **pip** (Python package manager)
- **npm** (Node package manager)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy language model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Run the backend server**:
   ```bash
   cd src
   python app.py
   ```
   
   Backend will start at `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your API URL
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```
   
   Frontend will start at `http://localhost:5173`

## 📖 Usage

### Step 1: Prepare Your CVs

1. Collect all CVs/resumes (PDF, DOCX, or TXT format)
2. Organize them in a folder structure
3. Create a ZIP archive of the folder

### Step 2: Create Screening Job

1. Open the application in your browser (`http://localhost:5173`)
2. Enter the **Job Description** (include required skills and responsibilities)
3. Add **Must-Have Skills** (comma-separated, optional but recommended)
4. Upload the **ZIP file** containing CVs
5. Click **Start Screening**

### Step 3: View Results

1. Monitor real-time progress as resumes are analyzed
2. View the **Top 5 Candidates** ranked by match score
3. Review matched skills and missing must-haves for each candidate
4. Start a new screening job or export results

## 🎯 How It Works

### Scoring Algorithm

SmartHire uses a sophisticated multi-factor scoring system:

1. **TF-IDF Cosine Similarity (50%)**: Measures overall text similarity between job description and resume
2. **Skill Matching (50%)**: Analyzes technical skills from a database of 200+ skills
3. **Must-Have Penalty**: Significantly reduces score for missing critical skills
4. **Bonus Points**: Extra points for high-demand skills (React, Full Stack, etc.)

Final score: 0-100 scale

### Performance Optimizations

- **Regex Pattern Caching**: 85x faster pattern matching
- **Job Description Pre-processing**: Compute once, reuse for all resumes (5.2x faster)
- **Batch Database Operations**: 90% reduction in I/O operations
- **Optimized Text Extraction**: Efficient PDF and DOCX parsing
- **No Unused Dependencies**: Removed 100MB+ unused spaCy model

See [PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md) for details.

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FRONTEND_URL=http://localhost:5173
DB_PATH=smarthire.db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=524288000  # 500MB
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:5000
```

## 🌐 Deployment

### Backend Deployment Options

#### Option 1: Traditional Hosting (DigitalOcean, AWS EC2, etc.)

```bash
# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Run with Gunicorn (production server)
cd backend/src
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Option 2: Docker

```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY backend/src/ .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### Option 3: Platform-as-a-Service (Heroku, Render.com)

1. Create `Procfile` in backend/:
   ```
   web: cd src && gunicorn app:app
   ```

2. Deploy using platform CLI or Git integration

### Frontend Deployment Options

#### Option 1: Static Hosting (Netlify, Vercel, GitHub Pages)

```bash
# Build for production
npm run build

# Deploy the 'dist' folder to your hosting provider
```

#### Option 2: Traditional Hosting

```bash
# Build
npm run build

# Serve with any static file server (nginx, Apache, etc.)
```

## 📊 API Reference

### POST /upload-zip

Upload ZIP file with CVs and start screening job.

**Request:**
- `Content-Type: multipart/form-data`
- `zip_file`: ZIP archive containing CVs
- `description`: Job description text
- `must_haves`: Comma-separated must-have skills

**Response:**
```json
{
  "message": "Started processing ZIP file",
  "job_id": 1,
  "total_cvs_found": 150
}
```

### GET /job-status/:job_id

Get processing status of a job.

**Response:**
```json
{
  "status": "Processing",
  "processed": 75,
  "total": 150,
  "percentage": 50.0
}
```

### GET /shortlist/:job_id

Get top 5 candidates for a job.

**Response:**
```json
{
  "status": "Completed",
  "progress": "150/150",
  "top_5": [
    {
      "id": 1,
      "filename": "john_doe.pdf",
      "score": 87.5,
      "found_skills": "[\"Python\", \"React\", \"AWS\"]",
      "missing_skills": "[]"
    }
  ]
}
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
python test_performance.py
```

Expected output:
- ✓ Regex caching working correctly (85x faster)
- ✓ Job description preprocessing working correctly (5.2x faster)
- ✓ Text extraction working correctly
- ✓ Database context manager working correctly
- ✓ Benchmark completed (890 resumes/second)

### Frontend Tests

```bash
cd frontend
npm run lint
```

## 🤝 Contributing

This is a thesis/academic project. For collaboration:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**SmartHire 2.0** - Academic Project / Thesis Work

## 🙏 Acknowledgments

- TF-IDF and Cosine Similarity algorithms from scikit-learn
- Flask web framework
- React and Vite for modern frontend development
- Performance optimization techniques from Python best practices

## 📧 Support

For questions, issues, or thesis inquiries:
- Open an issue on GitHub
- Review existing documentation in `/docs`
- Check performance guides in repository

## 🗺️ Roadmap

Future enhancements for production use:

- [ ] User authentication and multi-tenant support
- [ ] Export results to PDF/Excel
- [ ] Advanced filtering and sorting
- [ ] Resume download functionality
- [ ] Email notifications
- [ ] Interview scheduling integration
- [ ] Analytics dashboard
- [ ] Bulk job management
- [ ] Custom skill databases per organization

---

**Made with ❤️ for automated recruitment | Processing at 890 resumes/second ⚡**

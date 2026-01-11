# 🚀 Deployment Guide for SmartHire 2.0

This guide covers deploying SmartHire 2.0 for production use, including various hosting options suitable for a thesis/academic project demonstration.

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Production Testing](#local-production-testing)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Full-Stack Deployment](#full-stack-deployment)
6. [Recommended Setup for Thesis](#recommended-setup-for-thesis)

---

## ✅ Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] Tested the application locally
- [ ] Run performance tests (`python backend/test_performance.py`)
- [ ] Configured environment variables
- [ ] Prepared sample CV dataset for demonstration
- [ ] Created production `.env` files
- [ ] Tested with different browsers
- [ ] Documented any custom configurations

---

## 🏠 Local Production Testing

Test the production build locally before deploying:

### Backend Production Mode

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install production server
pip install gunicorn

# Set production environment
export FLASK_ENV=production
export FLASK_DEBUG=False

# Run with Gunicorn
cd src
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend Production Build

```bash
cd frontend

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🔧 Backend Deployment

### Option 1: Render.com (Recommended for Free Tier)

**Pros**: Free tier, easy setup, automatic HTTPS, good for demos
**Cons**: May sleep after inactivity (free tier)

**Steps**:

1. **Prepare your repository**:
   ```bash
   # Ensure requirements.txt is in backend/
   # Create backend/render.yaml
   ```

2. **Create `backend/render.yaml`**:
   ```yaml
   services:
     - type: web
       name: smarthire-backend
       runtime: python
       buildCommand: "pip install -r requirements.txt && python -m spacy download en_core_web_sm"
       startCommand: "cd src && gunicorn app:app"
       envVars:
         - key: FLASK_ENV
           value: production
         - key: FLASK_DEBUG
           value: False
         - key: PYTHON_VERSION
           value: 3.9.0
   ```

3. **Deploy**:
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository
   - Select the backend directory
   - Deploy!

4. **Note your backend URL**: `https://smarthire-backend.onrender.com`

### Option 2: Heroku

**Pros**: Simple deployment, free tier available
**Cons**: Requires credit card for verification

**Steps**:

1. **Create `backend/Procfile`**:
   ```
   web: cd src && gunicorn app:app
   ```

2. **Create `backend/runtime.txt`**:
   ```
   python-3.9.16
   ```

3. **Deploy**:
   ```bash
   cd backend
   heroku create smarthire-backend
   git subtree push --prefix backend heroku main
   ```

### Option 3: PythonAnywhere

**Pros**: Free tier, easy for Python apps, no credit card needed
**Cons**: Limited resources on free tier

**Steps**:

1. Create account at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload your backend code
3. Create a virtual environment
4. Configure WSGI file
5. Set up web app

Detailed guide: [PythonAnywhere Flask Tutorial](https://help.pythonanywhere.com/pages/Flask/)

### Option 4: DigitalOcean / AWS EC2 (For Production)

**Pros**: Full control, scalable
**Cons**: Costs money, requires more setup

**Steps**:

1. **Create a server** (Ubuntu 20.04 recommended)

2. **SSH into server**:
   ```bash
   ssh root@your-server-ip
   ```

3. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

4. **Clone and setup**:
   ```bash
   cd /var/www
   git clone <your-repo>
   cd SmartHire_2.0/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

5. **Create systemd service** (`/etc/systemd/system/smarthire.service`):
   ```ini
   [Unit]
   Description=SmartHire Backend
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/SmartHire_2.0/backend/src
   Environment="PATH=/var/www/SmartHire_2.0/backend/.venv/bin"
   ExecStart=/var/www/SmartHire_2.0/backend/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

6. **Configure Nginx** (`/etc/nginx/sites-available/smarthire`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **Start services**:
   ```bash
   sudo systemctl start smarthire
   sudo systemctl enable smarthire
   sudo systemctl restart nginx
   ```

---

## 🎨 Frontend Deployment

### Option 1: Netlify (Recommended)

**Pros**: Free, automatic HTTPS, easy deployment, excellent for React apps
**Cons**: None for static sites

**Steps**:

1. **Build your frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy**:
   - Go to [netlify.com](https://netlify.com)
   - Drag and drop the `dist` folder
   - Or connect GitHub for automatic deployments

3. **Configure environment variables**:
   - In Netlify dashboard: Site settings → Environment variables
   - Add: `VITE_API_URL=https://your-backend-url.com`

4. **Update build settings** (if using GitHub):
   ```
   Build command: npm run build
   Publish directory: dist
   ```

### Option 2: Vercel

**Pros**: Excellent performance, free tier, easy deployment
**Cons**: None for this use case

**Steps**:

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Deploy:
   ```bash
   cd frontend
   vercel --prod
   ```

3. Set environment variable:
   ```bash
   vercel env add VITE_API_URL
   ```

### Option 3: GitHub Pages

**Pros**: Free, integrated with GitHub
**Cons**: Requires some configuration for SPA routing

**Steps**:

1. **Install gh-pages**:
   ```bash
   npm install --save-dev gh-pages
   ```

2. **Update `package.json`**:
   ```json
   {
     "homepage": "https://yourusername.github.io/SmartHire_2.0",
     "scripts": {
       "predeploy": "npm run build",
       "deploy": "gh-pages -d dist"
     }
   }
   ```

3. **Deploy**:
   ```bash
   npm run deploy
   ```

---

## 🎯 Full-Stack Deployment

### Docker Compose (All-in-One)

**Best for**: Local demonstration, containerized deployment

**Create `docker-compose.yml`** in root:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
      - FRONTEND_URL=http://localhost:3000
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/smarthire.db:/app/smarthire.db

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://localhost:5000
    depends_on:
      - backend
```

**Create `backend/Dockerfile`**:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY src/ .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

**Create `frontend/Dockerfile`**:

```dockerfile
FROM node:18 as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Deploy**:

```bash
docker-compose up -d
```

---

## 🎓 Recommended Setup for Thesis

For a thesis/academic project demonstration, we recommend:

### **Frontend**: Netlify (Free Tier)
- Professional URL
- Automatic HTTPS
- Easy to share with reviewers
- Fast global CDN

### **Backend**: Render.com (Free Tier)
- Easy Python deployment
- Automatic HTTPS
- Free tier sufficient for demos
- Simple database persistence

### **Setup Steps**:

1. **Deploy Backend to Render.com**:
   ```bash
   # Push your code to GitHub
   git push origin main
   
   # On Render.com:
   # 1. Create new Web Service
   # 2. Connect GitHub repo
   # 3. Root directory: backend
   # 4. Build: pip install -r requirements.txt && python -m spacy download en_core_web_sm
   # 5. Start: cd src && gunicorn app:app
   ```

2. **Deploy Frontend to Netlify**:
   ```bash
   # Build locally
   cd frontend
   npm run build
   
   # Create .env.production
   echo "VITE_API_URL=https://your-backend.onrender.com" > .env.production
   
   # Rebuild with production env
   npm run build
   
   # Deploy to Netlify (drag and drop dist folder)
   ```

3. **Update Backend CORS**:
   - Add your Netlify URL to `FRONTEND_URL` in backend/.env

4. **Test the deployment**:
   - Upload a test ZIP with sample CVs
   - Verify real-time progress tracking
   - Check top candidates display correctly

### **For Thesis Defense**:

Prepare these materials:

1. **Live Demo URL**: Your Netlify frontend URL
2. **Sample Dataset**: 50-100 test CVs in a ZIP file
3. **Sample Job Description**: Ready to paste
4. **Screenshots**: Capture key features
5. **Performance Metrics**: From test_performance.py
6. **Architecture Diagram**: Show frontend-backend separation
7. **Backup Video**: Record a demo in case of connectivity issues

---

## 🔐 Security Considerations

For production deployment:

1. **Environment Variables**: Never commit `.env` files
2. **File Upload Limits**: Configure `MAX_CONTENT_LENGTH`
3. **CORS**: Restrict to your frontend domain
4. **Input Validation**: Validate ZIP files before processing
5. **Rate Limiting**: Consider adding rate limits for APIs
6. **HTTPS**: Always use HTTPS in production
7. **Database Backups**: Regular backups of `smarthire.db`

---

## 📊 Monitoring & Maintenance

### Health Checks

Add to `backend/src/app.py`:

```python
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "version": "2.0"}), 200
```

### Logging

Configure logging for production:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## 🆘 Troubleshooting

### Common Issues:

**Backend won't start**:
- Check Python version (3.8+)
- Verify all dependencies installed
- Check port 5000 is available

**Frontend can't connect to backend**:
- Verify `VITE_API_URL` is set correctly
- Check CORS configuration
- Verify backend is running

**File upload fails**:
- Check `MAX_CONTENT_LENGTH` setting
- Verify uploads folder exists and is writable
- Check network timeout settings

**Database errors**:
- Ensure `smarthire.db` has write permissions
- Check disk space
- Verify SQLite is available

---

## 📞 Support

For deployment issues:
- Check [backend logs](#logging)
- Review [troubleshooting](#troubleshooting)
- Test locally first
- Consult platform documentation

---

**Happy Deploying! 🚀**

Remember: For thesis purposes, stability and demonstration quality are more important than scale. The free tier options are perfect for academic presentations.

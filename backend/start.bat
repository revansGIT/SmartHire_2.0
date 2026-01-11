@echo off
REM SmartHire 2.0 Backend Startup Script for Windows

echo Starting SmartHire 2.0 Backend...

cd /d %~dp0

REM Check if virtual environment exists
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist ".venv\.dependencies_installed" (
    echo Installing dependencies...
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    echo. > .venv\.dependencies_installed
    echo Dependencies installed!
)

REM Create .env if it doesn't exist
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env file with your configuration
)

REM Start the backend server
echo Starting Flask server...
cd src
python app.py

pause

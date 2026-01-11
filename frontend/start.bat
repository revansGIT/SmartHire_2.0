@echo off
REM SmartHire 2.0 Frontend Startup Script for Windows

echo Starting SmartHire 2.0 Frontend...

cd /d %~dp0

REM Install dependencies if needed
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
    echo Dependencies installed!
)

REM Create .env if it doesn't exist
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo Please edit .env file with your API URL
)

REM Start the development server
echo Starting Vite development server...
call npm run dev

pause

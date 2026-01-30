@echo off
ECHO "Activating virtual environment..."
CALL "C:\Users\user\.claude-perplexity\venv\Scripts\activate.bat"

ECHO "Starting the Claude+Perplexity stack..."
python launch_claude_perplexity.py

pause

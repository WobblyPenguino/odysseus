@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo Installing recommended Nova v55.3.155 Ollama models for upgraded PCs...
set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Ollama"
ollama pull qwen3-coder:30b
ollama pull gemma2:2b
ollama pull llama3.2-vision:11b
ollama pull nomic-embed-text:latest
echo Done. Start Nova with START_NOVA_HERE.bat
pause

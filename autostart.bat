@echo off
chcp 65001 > nul
title ORION AUTONOMOUS SYSTEM — DDGK HyperLab
color 0B

echo.
echo  ========================================================
echo   ORION AUTONOMOUS SYSTEM — Auto-Start
echo   DDGK HyperLab v1.0 ^| Governance-gesteuert
echo  ========================================================
echo.

:: Wechsle ins ORION-Verzeichnis
cd /d "c:\Users\annah\Dropbox\Mein PC (LAPTOP-RQH448P4)\Downloads\ORION-ROS2-Consciousness-Node"

echo  [1/4] Pruefe Python...
python --version
if %errorlevel% neq 0 (
    echo  FEHLER: Python nicht gefunden!
    pause
    exit /b 1
)

echo  [2/4] Pruefe Ollama...
curl -s http://127.0.0.1:11434/api/tags > nul 2>&1
if %errorlevel% neq 0 (
    echo  Starte Ollama im Hintergrund...
    start /min "" ollama serve
    timeout /t 5 /nobreak > nul
)

echo  [3/4] Starte DDGK Dashboard (Port 7860)...
start /min "ORION-Dashboard" python -X utf8 ddgk_dashboard.py

timeout /t 2 /nobreak > nul

echo  [4/4] Starte ORION Autonomous Runner...
start "ORION-Autorun" python -X utf8 orion_autorun.py

echo.
echo  ✅ ORION SYSTEM GESTARTET
echo  Dashboard: http://localhost:7860
echo.
echo  Druecke eine Taste zum Schliessen dieses Fensters...
pause > nul

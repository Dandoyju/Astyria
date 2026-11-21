@echo off
echo.
echo  ╔═══════════════════════════════════╗
echo  ║          ASTYRIA — D^&D 5e         ║
echo  ║      Lancement du serveur MJ      ║
echo  ╚═══════════════════════════════════╝
echo.

:: Vérifie que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe.
    echo Telechargez Python 3 sur https://python.org
    pause
    exit /b 1
)

echo Demarrage du serveur sur http://localhost:8000
echo Appuyez sur Ctrl+C pour arreter.
echo.

:: Ouvre le navigateur après 1.5 secondes
start "" timeout /t 2 /nobreak >nul & start "" "http://localhost:8000/app/creer.html"

:: Lance le serveur
python server.py
pause

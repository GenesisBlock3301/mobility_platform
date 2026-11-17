@echo off
rem Stops the app. Profiles and shortlists are kept for next time.
rem To delete all data as well, run: docker compose down -v
cd /d "%~dp0"
docker compose down
echo.
echo The app is stopped. Start it again by double-clicking start.bat in the deployment folder
echo.
pause

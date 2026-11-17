@echo off
rem One-step start for Windows: double-click this file in the deployment folder.
rem Checks Docker, creates .env with random secrets on first run, starts every
rem service, waits until the site answers, then opens it.
setlocal EnableDelayedExpansion
cd /d "%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
  echo.
  echo [!] Docker is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop/ then run this again.
  goto :end
)
docker info >nul 2>&1
if errorlevel 1 (
  echo.
  echo [!] Docker is installed but not running. Open the Docker Desktop app, wait until it says "running", then run this again.
  goto :end
)

if not exist .env (
  echo.
  echo First run: creating settings ^(.env^) with random passwords...
  call :secret S1
  call :secret S2
  call :secret S3
  call :freeport 3000 WEBP
  set /a NEXT=!WEBP!+1
  call :freeport 8000 APIP
  if "!APIP!"=="!WEBP!" call :freeport !NEXT! APIP
  powershell -NoProfile -Command ^
    "(Get-Content .env.example) -replace '^POSTGRES_PASSWORD=.*','POSTGRES_PASSWORD=!S1!' -replace '^APP_DB_PASSWORD=.*','APP_DB_PASSWORD=!S2!' -replace '^INTERNAL_TOKEN=.*','INTERNAL_TOKEN=!S3!' -replace '^WEB_PORT=.*','WEB_PORT=!WEBP!' -replace '^API_PORT=.*','API_PORT=!APIP!' | Set-Content -Encoding ascii .env"
)

set WEB_PORT=3000
for /f "tokens=1,* delims==" %%a in ('findstr /b "WEB_PORT=" .env') do set WEB_PORT=%%b
set URL=http://localhost:%WEB_PORT%

echo.
echo Starting the app. The first time this downloads and builds everything, which can take 5-10 minutes...
docker compose up --build --detach
if errorlevel 1 (
  echo.
  echo [!] The app did not start. Run "docker compose logs" in the deployment folder and send the output to the developer.
  goto :end
)

echo.
echo Waiting for the website to be ready...
set /a TRIES=0
:wait
curl -fsS -o nul %URL% >nul 2>&1
if not errorlevel 1 goto :ready
set /a TRIES+=1
if %TRIES% gtr 150 (
  echo.
  echo [!] The website did not respond after 5 minutes. Run "docker compose logs" in the deployment folder and send the output to the developer.
  goto :end
)
timeout /t 2 /nobreak >nul
goto :wait

:ready
echo.
echo Ready: %URL%
echo To stop the app later, double-click stop.bat
start "" %URL%
goto :end

:secret
set "%1=%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%"
exit /b

:freeport
set /a P=%1
:freeport_loop
netstat -an | findstr /r /c:":%P% .*LISTENING" >nul
if not errorlevel 1 (
  set /a P+=1
  goto :freeport_loop
)
set "%2=%P%"
exit /b

:end
echo.
pause

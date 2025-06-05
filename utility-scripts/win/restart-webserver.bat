@echo off
REM Windows wrapper for restart-webserver.sh
set "SCRIPT_DIR=%~dp0"
bash "%SCRIPT_DIR%..\restart-webserver.sh" %*
pause


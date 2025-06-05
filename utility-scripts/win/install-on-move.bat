@echo off
REM Windows wrapper for install-on-move.sh
set "SCRIPT_DIR=%~dp0"
bash "%SCRIPT_DIR%..\install-on-move.sh" %*
pause



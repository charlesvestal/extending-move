@echo off
REM Windows wrapper for update-on-move.sh
set "SCRIPT_DIR=%~dp0"
bash "%SCRIPT_DIR%..\update-on-move.sh" %*
pause


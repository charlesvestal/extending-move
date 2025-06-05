@echo off
REM Windows wrapper for setup-ssh-and-install-on-move.sh
set "SCRIPT_DIR=%~dp0"
bash "%SCRIPT_DIR%..\setup-ssh-and-install-on-move.sh" %*
pause


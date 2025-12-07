@echo off
REM Start the first-flow mixer detection agent

echo Starting First-Flow Mixer Detection Agent...
echo This will run on port 5001
echo.

cd agent\first-flow
python mixer_mcp_tool.py

pause

@echo off
chcp 65001 >nul
REM 원고 검수 GUI 실행 스크립트

cd /d "%~dp0"

REM Python 가상환경 확인
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
)

REM GUI 실행
python manuscript_gui.py

REM 종료 대기
pause

#!/bin/bash
# 원고 검수 GUI 실행 스크립트

cd "$(dirname "$0")"

# Python 가상환경 확인
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# GUI 실행
python3 manuscript_gui.py

# 종료 대기
read -p "Press Enter to exit..."

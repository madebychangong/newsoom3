#!/bin/bash

echo "===================================="
echo "블로그 SEO 최적화 시스템 빌드"
echo "===================================="
echo

echo "[1/4] 필수 패키지 설치 확인..."
pip install pyinstaller pandas openpyxl anthropic
if [ $? -ne 0 ]; then
    echo "오류: 패키지 설치 실패"
    exit 1
fi

echo
echo "[2/4] 이전 빌드 정리..."
rm -rf dist build

echo
echo "[3/4] EXE 파일 빌드 중... (시간이 걸릴 수 있습니다)"
pyinstaller blog_optimizer.spec --clean
if [ $? -ne 0 ]; then
    echo "오류: 빌드 실패"
    exit 1
fi

echo
echo "[4/4] 필수 파일 복사..."
cp "금칙어 수정사항 모음.txt" dist/ 2>/dev/null || true

echo
echo "===================================="
echo "✅ 빌드 완료!"
echo "===================================="
echo
echo "📁 출력 위치: dist/블로그SEO최적화"
echo
echo "배포 시 함께 포함할 파일:"
echo "  - 블로그SEO최적화 (실행 파일)"
echo "  - 금칙어 수정사항 모음.txt"
echo

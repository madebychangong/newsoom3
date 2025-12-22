@echo off
chcp 65001 >nul
echo ====================================
echo 블로그 SEO 최적화 시스템 빌드
echo ====================================
echo.

echo [1/4] 필수 패키지 설치 확인...
pip install pyinstaller pandas openpyxl anthropic
if errorlevel 1 (
    echo 오류: 패키지 설치 실패
    pause
    exit /b 1
)

echo.
echo [2/4] 이전 빌드 정리...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo [3/4] EXE 파일 빌드 중... (시간이 걸릴 수 있습니다)
pyinstaller blog_optimizer.spec --clean
if errorlevel 1 (
    echo 오류: 빌드 실패
    pause
    exit /b 1
)

echo.
echo [4/4] 필수 파일 복사...
copy "금칙어 수정사항 모음.txt" "dist\" 2>nul

echo.
echo ====================================
echo ✅ 빌드 완료!
echo ====================================
echo.
echo 📁 출력 위치: dist\블로그SEO최적화.exe
echo.
echo 배포 시 함께 포함할 파일:
echo   - 블로그SEO최적화.exe
echo   - 금칙어 수정사항 모음.txt
echo.
pause

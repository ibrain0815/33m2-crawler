#!/bin/bash
echo "========================================"
echo "33m2 크롤러 빌드 스크립트 (Linux/Mac)"
echo "========================================"
echo

# 가상환경 활성화
source venv/bin/activate

# 빌드 전 정리
echo "이전 빌드 파일 정리 중..."
rm -rf dist build

# 아이콘 생성 (Pillow 설치 확인)
echo "아이콘 확인 중..."
if [ ! -f "assets/icon.png" ]; then
    echo "아이콘 생성 시도..."
    pip install pillow -q
    python create_icon.py
fi

# PyInstaller 실행
echo
echo "빌드 시작..."
echo

# spec 파일 사용
pyinstaller build.spec --noconfirm

echo
if [ -f "dist/33m2크롤러" ]; then
    echo "========================================"
    echo "빌드 성공!"
    echo "실행 파일: dist/33m2크롤러"
    echo "========================================"
else
    echo "========================================"
    echo "빌드 실패. 로그를 확인하세요."
    echo "========================================"
fi

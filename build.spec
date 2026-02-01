# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 빌드 설정 파일
33m2 크롤러를 EXE 파일로 빌드합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 경로
PROJECT_ROOT = Path(SPECPATH)

# 아이콘 경로
ICON_PATH = PROJECT_ROOT / 'assets' / 'icon.ico'
icon_file = str(ICON_PATH) if ICON_PATH.exists() else None

# 데이터 파일 설정
datas = [
    # assets 폴더 포함
    (str(PROJECT_ROOT / 'assets'), 'assets'),
]

# 숨겨진 import 설정
hiddenimports = [
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'webdriver_manager',
    'webdriver_manager.chrome',
    'beautifulsoup4',
    'bs4',
    'pandas',
    'openpyxl',
    'PyQt5',
    'PyQt5.QtWidgets',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.sip',
]

# 제외할 모듈
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'PIL.ImageTk',
]

a = Analysis(
    ['main.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='33m2크롤러',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

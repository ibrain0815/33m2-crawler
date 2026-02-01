"""
설정 파일
크롤링에 필요한 설정 값들을 관리합니다.
"""

import sys
from pathlib import Path

# ============================================================
# 기본 URL 설정
# ============================================================
BASE_URL = "https://web.33m2.co.kr"
MAIN_URL = f"{BASE_URL}/guest/main"
SEARCH_URL = f"{BASE_URL}/guest/search"

# ============================================================
# User-Agent 설정
# ============================================================
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ============================================================
# 딜레이 설정 (초) - 속도 개선을 위해 단축
# ============================================================
DELAY_MIN = 0.8  # 최소 딜레이 (목록 로드)
DELAY_MAX = 1.8  # 최대 딜레이
PAGE_LOAD_TIMEOUT = 12  # 페이지 로딩 타임아웃
SCROLL_DELAY_MIN = 0.6  # 스크롤 후 최소 대기
SCROLL_DELAY_MAX = 1.2  # 스크롤 후 최대 대기

# ============================================================
# 윈도우 설정
# ============================================================
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 650  # 로그 스크롤바가 가리지 않도록 여유 높이
WINDOW_X = 100
WINDOW_Y = 100

# 브라우저 창 크기
BROWSER_WIDTH = 1920
BROWSER_HEIGHT = 1080

# ============================================================
# 저장 경로 설정 (엑셀은 실행파일/스크립트와 동일한 위치에 저장)
# ============================================================
if getattr(sys, "frozen", False):
    # EXE 실행 시: 실행파일이 있는 폴더
    APP_DIR = Path(sys.executable).parent
    BASE_DIR = Path(sys._MEIPASS)  # 리소스(assets)는 번들 경로
else:
    # Python 스크립트 실행 시: main.py가 있는 폴더(프로젝트 루트)
    APP_DIR = Path(__file__).parent.parent
    BASE_DIR = APP_DIR

DATA_DIR = APP_DIR  # 엑셀 저장 위치 = 실행파일과 동일
LOGS_DIR = APP_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

# 폴더 생성 (LOGS_DIR만 생성, DATA_DIR는 이미 존재)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# CSS 선택자 설정 (33m2 검색 페이지 실제 HTML 구조 기준)
# 구조: ul.grid > li.h-fit > a[href="/guest/room/ID"] > h3(숙소명), p(위치), div(방구성), strong(가격), div(가격상세), div(할인)
# ============================================================
SELECTORS = {
    # 숙소 카드: ul 내 li.h-fit (각 카드)
    'room_card': 'ul[class*="grid"] li.h-fit, ul li.h-fit',
    # 숙소명: h3.typo-body1
    'room_title': 'h3.typo-body1, h3.font-semibold.text-gray-900',
    # 세부 위치/특징 (예: 공덕/광화문/여의도): p.typo-label1
    'room_location': 'div.mb-\\[6px\\] p.typo-label1, p.typo-label1.font-normal.text-gray-900, p.typo-label1',
    # 방 구성 (방1 화장실1 주방1): div.typo-label1.flex.gap-2 중 첫 번째
    'room_composition': 'div.typo-label1.flex.gap-2.font-normal.text-gray-500',
    # 주요 가격: strong.typo-headline3 + 부모 p에서 "원 / 1주" 등
    'room_price': 'strong.typo-headline3, p.flex.items-center.gap-0\\.5.font-bold',
    # 가격 기간 (1주 등): span.text-purple-500
    'room_price_period': 'span.typo-body1.font-bold.text-purple-500, span.text-purple-500',
    # 가격 상세 (임대료/관리비): div.typo-label1.mb-2
    'room_price_detail': 'div.typo-label1.mb-2.flex.gap-2, div.mb-2.typo-label1',
    # 할인 정보: div.bg-gray-50
    'room_discount': 'div.bg-gray-50.rounded-sm, div.rounded-sm.bg-gray-50',
    # 썸네일: 카드 내 첫 img
    'room_image': 'img',
    'room_rating': '[class*="rating"], [class*="score"]',
    'room_type': '[class*="type"], [class*="category"]',
    'next_page': '[class*="next"], [class*="pagination"] a:last-child',
    'load_more': '[class*="more"], [class*="load"]',
    # 스크롤 컨테이너 (목록 영역)
    'scroll_container': 'ul[class*="grid"][class*="overflow-y-auto"], ul.overflow-y-auto',
}

# 상세 페이지 선택자
DETAIL_SELECTORS = {
    'description': '[class*="description"], [class*="detail"], [class*="content"]',
    'images': '[class*="gallery"] img, [class*="slider"] img, [class*="carousel"] img',
    'amenities': '[class*="amenity"], [class*="facility"], [class*="feature"]',
    'address': '[class*="address"], [class*="location"]',
    'review_count': '[class*="review-count"], [class*="review"] [class*="count"]',
    'average_rating': '[class*="rating"], [class*="score"]',
}

# ============================================================
# 크롤링 설정
# ============================================================
DEFAULT_CRAWL_COUNT = 50  # 기본 크롤링 개수
MAX_CRAWL_COUNT = 500  # 최대 크롤링 개수
CRAWL_COUNT_OPTIONS = [10, 20, 50, 100, 200, 500]  # 선택 가능한 개수

# ============================================================
# 앱 정보
# ============================================================
APP_NAME = "삼삼엠투 숙박정보 크롤러"
APP_VERSION = "1.0.0"
APP_AUTHOR = "33m2 Crawler Team"

# ============================================================
# GUI 스타일 설정
# ============================================================
STYLE_SHEET = """
QMainWindow {
    background-color: #f5f5f5;
}

QPushButton {
    background-color: #4472C4;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #3461b3;
}

QPushButton:pressed {
    background-color: #2850a2;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QPushButton#stopButton {
    background-color: #dc3545;
}

QPushButton#stopButton:hover {
    background-color: #c82333;
}

QPushButton#saveButton {
    background-color: #28a745;
}

QPushButton#saveButton:hover {
    background-color: #218838;
}

QProgressBar {
    border: 1px solid #ccc;
    border-radius: 5px;
    text-align: center;
    height: 25px;
}

QProgressBar::chunk {
    background-color: #4472C4;
    border-radius: 4px;
}

QTextEdit {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 5px;
    font-family: "Consolas", "맑은 고딕", monospace;
    font-size: 12px;
    background-color: white;
}

QComboBox {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 5px 10px;
    min-width: 100px;
}

QLabel {
    font-size: 13px;
}

QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #333;
}

QLabel#statusLabel {
    color: #666;
    font-size: 12px;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #ccc;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
"""

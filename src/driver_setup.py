"""
Selenium WebDriver 설정 모듈
봇 감지 우회 및 브라우저 설정을 담당합니다.
"""

import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# User-Agent 목록 (실제 Chrome 브라우저)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]


def get_random_user_agent() -> str:
    """랜덤 User-Agent 반환"""
    return random.choice(USER_AGENTS)


def random_delay(min_sec: float = 2.0, max_sec: float = 5.0) -> None:
    """
    랜덤 딜레이 함수 (봇 감지 우회용)

    Args:
        min_sec: 최소 대기 시간 (초)
        max_sec: 최대 대기 시간 (초)
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def create_driver(headless: bool = False) -> webdriver.Chrome:
    """
    봇 감지 우회 설정이 적용된 Chrome 드라이버 생성

    Args:
        headless: 헤드리스 모드 사용 여부

    Returns:
        설정된 Chrome WebDriver 인스턴스
    """
    options = Options()

    # User-Agent 설정
    user_agent = get_random_user_agent()
    options.add_argument(f"user-agent={user_agent}")

    # 브라우저 창 크기 설정 (1920x1080)
    options.add_argument("--window-size=1920,1080")

    # 자동화 감지 비활성화
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # 추가 옵션
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ko-KR")

    # 헤드리스 모드
    if headless:
        options.add_argument("--headless=new")

    # 드라이버 생성
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # WebDriver 속성 숨기기
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            });
        """
    })

    # 암묵적 대기 설정 (요소 탐색 타임아웃, 짧을수록 응답 빠름)
    driver.implicitly_wait(5)

    return driver


def close_driver(driver: webdriver.Chrome) -> None:
    """
    드라이버 안전하게 종료

    Args:
        driver: 종료할 WebDriver 인스턴스
    """
    if driver:
        try:
            driver.quit()
        except Exception:
            pass

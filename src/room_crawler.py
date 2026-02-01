"""
숙소 목록 크롤러 모듈
삼삼엠투 검색 페이지에서 숙소 목록을 수집합니다.
"""

import logging
from typing import Callable, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .driver_setup import random_delay
from .config import SEARCH_URL, SELECTORS

logger = logging.getLogger(__name__)


def crawl_rooms(
    driver: webdriver.Chrome,
    max_count: int,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> list:
    """
    숙소 목록 크롤링

    Args:
        driver: Selenium WebDriver 인스턴스
        max_count: 수집할 숙소 개수
        progress_callback: 진행률 콜백 함수 (현재, 전체)

    Returns:
        list: 숙소 정보 리스트
    """
    rooms = []
    collected = 0

    try:
        # 검색 페이지 접속
        logger.info(f"검색 페이지 접속 중: {SEARCH_URL}")
        driver.get(SEARCH_URL)
        random_delay(2, 4)

        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 15)

        while collected < max_count:
            # 숙소 카드 요소 탐색
            try:
                room_cards = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, SELECTORS['room_card'])
                    )
                )
            except TimeoutException:
                logger.warning("숙소 카드를 찾을 수 없습니다. 다른 선택자 시도...")
                room_cards = _try_alternative_selectors(driver)

            if not room_cards:
                logger.error("숙소 목록을 찾을 수 없습니다.")
                break

            # 각 숙소 카드에서 정보 추출
            for card in room_cards:
                if collected >= max_count:
                    break

                room_info = _extract_room_info(card)
                if room_info:
                    rooms.append(room_info)
                    collected += 1
                    logger.info(f"[{collected}/{max_count}] {room_info.get('title', 'Unknown')}")

                    if progress_callback:
                        progress_callback(collected, max_count)

            # 다음 페이지 또는 스크롤
            if collected < max_count:
                if not _load_more_rooms(driver):
                    logger.info("더 이상 로드할 숙소가 없습니다.")
                    break
                random_delay(2, 4)

    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")

    logger.info(f"크롤링 완료: 총 {len(rooms)}개 숙소 수집")
    return rooms


def _extract_room_info(card) -> Optional[dict]:
    """
    숙소 카드에서 정보 추출

    Args:
        card: 숙소 카드 WebElement

    Returns:
        dict: 추출된 숙소 정보 또는 None
    """
    try:
        room_info = {}

        # 숙소 제목
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['room_title'])
            room_info['title'] = title_elem.text.strip()
        except NoSuchElementException:
            room_info['title'] = ""

        # 가격 정보
        try:
            price_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['room_price'])
            room_info['price'] = price_elem.text.strip()
        except NoSuchElementException:
            room_info['price'] = ""

        # 썸네일 이미지 URL
        try:
            img_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['room_image'])
            room_info['image_url'] = img_elem.get_attribute('src') or img_elem.get_attribute('data-src')
        except NoSuchElementException:
            room_info['image_url'] = ""

        # 평점
        try:
            rating_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['room_rating'])
            room_info['rating'] = rating_elem.text.strip()
        except NoSuchElementException:
            room_info['rating'] = ""

        # 숙소 타입
        try:
            type_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['room_type'])
            room_info['room_type'] = type_elem.text.strip()
        except NoSuchElementException:
            room_info['room_type'] = ""

        # 위치
        try:
            location_elem = card.find_element(By.CSS_SELECTOR, SELECTORS['room_location'])
            room_info['location'] = location_elem.text.strip()
        except NoSuchElementException:
            room_info['location'] = ""

        # 숙소 링크/ID
        try:
            link_elem = card.find_element(By.CSS_SELECTOR, "a")
            href = link_elem.get_attribute('href')
            room_info['url'] = href
            # URL에서 ID 추출 시도
            if href and '/room/' in href:
                room_info['room_id'] = href.split('/room/')[-1].split('?')[0]
            else:
                room_info['room_id'] = ""
        except NoSuchElementException:
            room_info['url'] = ""
            room_info['room_id'] = ""

        return room_info if room_info.get('title') else None

    except Exception as e:
        logger.warning(f"숙소 정보 추출 실패: {str(e)}")
        return None


def _try_alternative_selectors(driver: webdriver.Chrome) -> list:
    """
    대체 선택자로 숙소 카드 탐색

    Args:
        driver: WebDriver 인스턴스

    Returns:
        list: 찾은 숙소 카드 요소들
    """
    alternative_selectors = [
        "[class*='room']",
        "[class*='property']",
        "[class*='card']",
        "[class*='item']",
        "article",
        ".list-item",
        ".search-item",
    ]

    for selector in alternative_selectors:
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if cards and len(cards) > 1:
                logger.info(f"대체 선택자로 {len(cards)}개 요소 발견: {selector}")
                return cards
        except Exception:
            continue

    return []


def _load_more_rooms(driver: webdriver.Chrome) -> bool:
    """
    더 많은 숙소 로드 (페이지네이션 또는 무한 스크롤)

    Args:
        driver: WebDriver 인스턴스

    Returns:
        bool: 추가 로드 성공 여부
    """
    try:
        # 방법 1: "더보기" 버튼 클릭
        more_buttons = [
            "[class*='more']",
            "[class*='load']",
            "button:contains('더보기')",
            ".btn-more",
            ".load-more",
        ]

        for selector in more_buttons:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    random_delay(2, 3)
                    return True
            except NoSuchElementException:
                continue

        # 방법 2: 다음 페이지 버튼
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, SELECTORS.get('next_page', '.next'))
            if next_btn.is_displayed() and next_btn.is_enabled():
                next_btn.click()
                random_delay(2, 3)
                return True
        except NoSuchElementException:
            pass

        # 방법 3: 무한 스크롤
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        random_delay(2, 3)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height > last_height:
            return True

        return False

    except Exception as e:
        logger.warning(f"추가 로드 실패: {str(e)}")
        return False

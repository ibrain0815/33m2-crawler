"""
숙소 상세 정보 크롤러 모듈
개별 숙소 페이지에서 상세 정보를 수집합니다.
"""

import logging
from typing import Callable, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .driver_setup import random_delay
from .config import BASE_URL, DETAIL_SELECTORS

logger = logging.getLogger(__name__)


def get_room_details(
    driver: webdriver.Chrome,
    room_id: str,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Optional[dict]:
    """
    숙소 상세 정보 수집

    Args:
        driver: Selenium WebDriver 인스턴스
        room_id: 숙소 ID 또는 URL
        progress_callback: 진행 상태 콜백 함수

    Returns:
        dict: 상세 정보 또는 None
    """
    details = {}

    try:
        # 상세 페이지 URL 구성
        if room_id.startswith('http'):
            detail_url = room_id
        else:
            detail_url = f"{BASE_URL}/guest/room/{room_id}"

        if progress_callback:
            progress_callback(f"상세 페이지 접속 중: {room_id}")

        logger.info(f"상세 페이지 접속: {detail_url}")
        driver.get(detail_url)
        random_delay(2, 4)

        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 15)

        # 숙소 상세 설명
        details['description'] = _get_description(driver)

        # 모든 이미지 URL
        details['images'] = _get_all_images(driver)

        # 편의시설 목록
        details['amenities'] = _get_amenities(driver)

        # 상세 주소
        details['address'] = _get_address(driver)

        # 후기 정보
        review_info = _get_review_info(driver)
        details['review_count'] = review_info.get('count', 0)
        details['average_rating'] = review_info.get('average', "")

        # 호스트 정보
        details['host_info'] = _get_host_info(driver)

        # 가격 상세
        details['price_details'] = _get_price_details(driver)

        # 체크인/체크아웃 시간
        details['check_in_out'] = _get_check_in_out(driver)

        if progress_callback:
            progress_callback(f"상세 정보 수집 완료: {room_id}")

        return details

    except Exception as e:
        logger.error(f"상세 정보 수집 실패 ({room_id}): {str(e)}")
        return None


def _get_description(driver: webdriver.Chrome) -> str:
    """숙소 상세 설명 추출"""
    selectors = [
        DETAIL_SELECTORS.get('description', ''),
        "[class*='description']",
        "[class*='detail']",
        "[class*='content']",
        ".room-description",
        ".property-description",
    ]

    for selector in selectors:
        if not selector:
            continue
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            text = elem.text.strip()
            if text and len(text) > 20:
                return text
        except NoSuchElementException:
            continue

    return ""


def _get_all_images(driver: webdriver.Chrome) -> list:
    """모든 이미지 URL 추출"""
    images = []
    selectors = [
        DETAIL_SELECTORS.get('images', ''),
        "[class*='gallery'] img",
        "[class*='slider'] img",
        "[class*='carousel'] img",
        ".room-images img",
        ".property-images img",
        "img[class*='room']",
        "img[class*='photo']",
    ]

    for selector in selectors:
        if not selector:
            continue
        try:
            img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for img in img_elements:
                src = img.get_attribute('src') or img.get_attribute('data-src')
                if src and src not in images and not src.startswith('data:'):
                    images.append(src)
        except NoSuchElementException:
            continue

    return images[:20]  # 최대 20개


def _get_amenities(driver: webdriver.Chrome) -> list:
    """편의시설 목록 추출"""
    amenities = []
    selectors = [
        DETAIL_SELECTORS.get('amenities', ''),
        "[class*='amenity']",
        "[class*='facility']",
        "[class*='feature']",
        ".amenities li",
        ".facilities li",
    ]

    for selector in selectors:
        if not selector:
            continue
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip()
                if text and text not in amenities:
                    amenities.append(text)
        except NoSuchElementException:
            continue

    return amenities


def _get_address(driver: webdriver.Chrome) -> str:
    """상세 주소 추출"""
    selectors = [
        DETAIL_SELECTORS.get('address', ''),
        "[class*='address']",
        "[class*='location']",
        ".room-address",
        ".property-location",
    ]

    for selector in selectors:
        if not selector:
            continue
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            text = elem.text.strip()
            if text:
                return text
        except NoSuchElementException:
            continue

    return ""


def _get_review_info(driver: webdriver.Chrome) -> dict:
    """후기 정보 추출"""
    review_info = {'count': 0, 'average': ""}

    # 후기 개수
    count_selectors = [
        DETAIL_SELECTORS.get('review_count', ''),
        "[class*='review-count']",
        "[class*='review'] [class*='count']",
        ".reviews-count",
    ]

    for selector in count_selectors:
        if not selector:
            continue
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            text = elem.text.strip()
            # 숫자 추출
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                review_info['count'] = int(numbers[0])
                break
        except NoSuchElementException:
            continue

    # 평균 평점
    rating_selectors = [
        DETAIL_SELECTORS.get('average_rating', ''),
        "[class*='rating']",
        "[class*='score']",
        ".review-rating",
        ".average-rating",
    ]

    for selector in rating_selectors:
        if not selector:
            continue
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            text = elem.text.strip()
            if text:
                review_info['average'] = text
                break
        except NoSuchElementException:
            continue

    return review_info


def _get_host_info(driver: webdriver.Chrome) -> str:
    """호스트 정보 추출"""
    selectors = [
        "[class*='host']",
        "[class*='owner']",
        ".host-info",
        ".owner-info",
    ]

    for selector in selectors:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            text = elem.text.strip()
            if text:
                return text
        except NoSuchElementException:
            continue

    return ""


def _get_price_details(driver: webdriver.Chrome) -> dict:
    """가격 상세 정보 추출"""
    price_info = {}

    selectors = [
        "[class*='price']",
        ".room-price",
        ".property-price",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip()
                if '1박' in text or '박' in text:
                    price_info['per_night'] = text
                elif '청소비' in text:
                    price_info['cleaning_fee'] = text
                elif '총' in text:
                    price_info['total'] = text
        except NoSuchElementException:
            continue

    return price_info


def _get_check_in_out(driver: webdriver.Chrome) -> dict:
    """체크인/체크아웃 시간 추출"""
    check_info = {'check_in': "", 'check_out': ""}

    selectors = [
        "[class*='check']",
        "[class*='time']",
        ".check-in-out",
    ]

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip().lower()
                if '체크인' in text or 'check-in' in text or 'checkin' in text:
                    check_info['check_in'] = elem.text.strip()
                elif '체크아웃' in text or 'check-out' in text or 'checkout' in text:
                    check_info['check_out'] = elem.text.strip()
        except NoSuchElementException:
            continue

    return check_info

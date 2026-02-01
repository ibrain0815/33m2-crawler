"""
크롤러 쓰레드 모듈
GUI가 멈추지 않도록 크롤링 작업을 별도 쓰레드로 처리합니다.
"""

import logging
from datetime import datetime
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .driver_setup import random_delay
from .config import (
    SEARCH_URL,
    SELECTORS,
    DELAY_MIN,
    DELAY_MAX,
    PAGE_LOAD_TIMEOUT,
    SCROLL_DELAY_MIN,
    SCROLL_DELAY_MAX,
)

logger = logging.getLogger(__name__)


class CrawlerWorker(QThread):
    """
    크롤링 작업을 수행하는 워커 쓰레드

    Signals:
        progress_signal: 진행률 전달 (current, total)
        log_signal: 로그 메시지 전달
        finished_signal: 작업 완료 알림 (data)
        error_signal: 에러 발생 알림 (error_msg)
    """

    progress_signal = pyqtSignal(int, int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, driver: webdriver.Chrome, max_count: int):
        """
        Args:
            driver: Selenium WebDriver 인스턴스
            max_count: 수집할 숙소 개수
        """
        super().__init__()
        self.driver = driver
        self.max_count = max_count
        self._is_running = True

    def run(self):
        """쓰레드 실행"""
        rooms = []
        collected = 0
        collected_ids = set()  # 이미 수집한 room_id (중복 방지)

        try:
            self._log(f"크롤링 시작: 목표 {self.max_count}개")

            # 현재 페이지 URL 확인
            current_url = self.driver.current_url
            if SEARCH_URL not in current_url:
                self._log(f"검색 페이지로 이동합니다: {SEARCH_URL}")
                self.driver.get(SEARCH_URL)
                random_delay(DELAY_MIN, DELAY_MAX)

            wait = WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT)

            while collected < self.max_count and self._is_running:
                # 숙소 카드 요소 탐색
                room_cards = self._find_room_cards()

                if not room_cards:
                    self._log("숙소 카드를 찾을 수 없습니다. 페이지 구조를 확인해주세요.")
                    break

                self._log(f"현재 페이지에서 {len(room_cards)}개의 숙소 카드 발견")

                # 각 숙소 카드에서 정보 추출 (이미 수집한 ID는 건너뜀)
                for card in room_cards:
                    if not self._is_running:
                        break

                    if collected >= self.max_count:
                        break

                    room_info = self._extract_room_info(card, collected + 1)
                    if room_info:
                        rid = room_info.get('room_id') or room_info.get('url') or ''
                        if rid and rid in collected_ids:
                            continue
                        if rid:
                            collected_ids.add(rid)
                        rooms.append(room_info)
                        collected += 1
                        self.progress_signal.emit(collected, self.max_count)
                        self._log(f"[{collected}/{self.max_count}] {room_info.get('title', 'Unknown')}")

                # 다음 페이지 로드
                if collected < self.max_count and self._is_running:
                    if not self._load_more():
                        self._log("더 이상 로드할 숙소가 없습니다.")
                        break
                    random_delay(SCROLL_DELAY_MIN, SCROLL_DELAY_MAX)

            self._log(f"크롤링 완료: 총 {len(rooms)}개 수집")
            self.finished_signal.emit(rooms)

        except Exception as e:
            self._log(f"크롤링 오류: {str(e)}")
            self.error_signal.emit(str(e))

    def stop(self):
        """크롤링 중지"""
        self._is_running = False
        self._log("크롤링 중단 요청됨")

    def _log(self, message: str):
        """로그 메시지 전송"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] [INFO] {message}"
        self.log_signal.emit(formatted_msg)
        logger.info(message)

    def _find_room_cards(self) -> list:
        """숙소 카드 요소 찾기 (33m2: ul.grid 내 li.h-fit)"""
        # 33m2 메인 선택자 (쉼표로 구분된 복수 선택자 각각 시도)
        for sel in SELECTORS['room_card'].split(', '):
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, sel.strip())
                if cards:
                    return cards
            except Exception:
                continue

        # 대체 선택자
        for selector in ["li.h-fit", "ul[class*='grid'] li", "[class*='room'], article"]:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards and len(cards) > 1:
                    return cards
            except Exception:
                continue

        return []

    def _extract_room_info(self, card, index: int) -> Optional[dict]:
        """숙소 카드에서 정보 추출 (33m2 HTML 구조 기준)"""
        try:
            room_info = {'index': index}

            # 숙소명 (h3.typo-body1)
            room_info['title'] = self._get_text(card, SELECTORS['room_title']) or f"숙소 {index}"

            # 세부 위치/특징 (예: 공덕/광화문/여의도)
            room_info['location'] = self._get_text(card, SELECTORS['room_location'])

            # 방 구성 (방1 화장실1 주방1) - 첫 번째 typo-label1.flex.gap-2
            room_info['room_composition'] = self._get_text_first(card, SELECTORS['room_composition'])

            # 주요 가격: "330,000 원 / 1주" 형태 (부모 p 전체 텍스트)
            price_text = self._get_text(card, SELECTORS['room_price'])
            if not price_text:
                # strong.typo-headline3 + 기간 조합
                price_num = self._get_text(card, 'strong.typo-headline3')
                period = self._get_text(card, SELECTORS.get('room_price_period', 'span.text-purple-500'))
                if price_num:
                    price_text = f"{price_num}원" + (f" / {period}" if period else "")
            room_info['price'] = price_text or ""

            # 가격 상세 (임대료/관리비)
            room_info['price_detail'] = self._get_text_first(card, SELECTORS.get('room_price_detail', ''))

            # 할인 정보
            room_info['discount'] = self._get_text_first(card, SELECTORS.get('room_discount', ''))

            # 썸네일 이미지 URL
            room_info['image_url'] = self._get_image(card, SELECTORS['room_image'])

            # 평점 (목록에 없을 수 있음)
            room_info['rating'] = self._get_text(card, SELECTORS['room_rating'])

            # 숙소 타입
            room_info['room_type'] = self._get_text(card, SELECTORS['room_type'])

            # 숙소 링크 및 room_id
            room_info['url'] = self._get_link(card)
            if room_info.get('url') and '/room/' in room_info['url']:
                room_info['room_id'] = room_info['url'].split('/room/')[-1].split('?')[0]
            else:
                room_info['room_id'] = ""

            return room_info

        except Exception as e:
            logger.warning(f"숙소 정보 추출 실패: {str(e)}")
            return None

    def _get_text(self, parent, selector: str) -> str:
        """요소에서 텍스트 추출 (여러 선택자 시도)"""
        if not selector:
            return ""
        selectors = selector.split(', ')
        for sel in selectors:
            try:
                elem = parent.find_element(By.CSS_SELECTOR, sel.strip())
                text = elem.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
        return ""

    def _get_text_first(self, parent, selector: str) -> str:
        """여러 요소 중 첫 번째 요소의 텍스트만 추출 (방구성/가격상세 등)"""
        if not selector:
            return ""
        selectors = selector.split(', ')
        for sel in selectors:
            try:
                elems = parent.find_elements(By.CSS_SELECTOR, sel.strip())
                for elem in elems:
                    text = elem.text.strip()
                    if text:
                        return text
            except NoSuchElementException:
                continue
        return ""

    def _get_image(self, parent, selector: str) -> str:
        """요소에서 이미지 URL 추출"""
        selectors = selector.split(', ')
        for sel in selectors:
            try:
                elem = parent.find_element(By.CSS_SELECTOR, sel.strip())
                src = elem.get_attribute('src') or elem.get_attribute('data-src')
                if src and not src.startswith('data:'):
                    return src
            except NoSuchElementException:
                continue

        # img 태그 전체 검색
        try:
            img = parent.find_element(By.TAG_NAME, 'img')
            src = img.get_attribute('src') or img.get_attribute('data-src')
            if src and not src.startswith('data:'):
                return src
        except NoSuchElementException:
            pass

        return ""

    def _get_link(self, parent) -> str:
        """요소에서 링크 URL 추출"""
        try:
            link = parent.find_element(By.TAG_NAME, 'a')
            return link.get_attribute('href') or ""
        except NoSuchElementException:
            return ""

    def _load_more(self) -> bool:
        """더 많은 숙소 로드 (목록 영역 스크롤 우선, 속도 개선)"""
        try:
            # 방법 1: "더보기" 버튼
            for selector in [SELECTORS.get('load_more', ''), "[class*='more']", ".load-more"]:
                if not selector:
                    continue
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        self._log("더보기 버튼 클릭")
                        random_delay(SCROLL_DELAY_MIN, SCROLL_DELAY_MAX)
                        return True
                except NoSuchElementException:
                    continue

            # 방법 2: 목록 스크롤 컨테이너(ul)만 스크롤 (33m2 무한 스크롤, 더 빠름)
            scroll_sel = SELECTORS.get('scroll_container', '')
            if scroll_sel:
                for sel in scroll_sel.split(', '):
                    try:
                        container = self.driver.find_element(By.CSS_SELECTOR, sel.strip())
                        last = container.get_attribute("scrollHeight") or "0"
                        self.driver.execute_script(
                            "arguments[0].scrollTop = arguments[0].scrollHeight;", container
                        )
                        random_delay(SCROLL_DELAY_MIN, SCROLL_DELAY_MAX)
                        return True
                    except NoSuchElementException:
                        continue

            # 방법 3: 창 전체 스크롤
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            random_delay(SCROLL_DELAY_MIN, SCROLL_DELAY_MAX)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height > last_height:
                self._log("스크롤 완료")
                return True

            return False

        except Exception as e:
            logger.warning(f"추가 로드 실패: {str(e)}")
            return False

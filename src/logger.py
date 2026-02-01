"""
로깅 시스템 모듈
파일 로그 및 GUI 연동 로깅을 제공합니다.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

# 로그 폴더 경로
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 로그 파일 경로
LOG_FILE = LOG_DIR / "crawler.log"

# 로그 포맷
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class GUILogHandler(logging.Handler):
    """
    GUI 텍스트 위젯으로 로그를 출력하는 핸들러
    """

    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        """
        Args:
            callback: 로그 메시지를 받을 콜백 함수
        """
        super().__init__()
        self.callback = callback
        self.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    def emit(self, record: logging.LogRecord) -> None:
        """로그 레코드 처리"""
        if self.callback:
            try:
                msg = self.format(record)
                self.callback(msg)
            except Exception:
                self.handleError(record)

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """콜백 함수 설정"""
        self.callback = callback


class CrawlerLogger:
    """
    크롤러 전용 로거 클래스
    """

    _instance = None
    _gui_handler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = logging.getLogger("33m2_crawler")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        # 파일 핸들러
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        self.logger.addHandler(file_handler)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        self.logger.addHandler(console_handler)

        # GUI 핸들러 (초기에는 콜백 없음)
        self._gui_handler = GUILogHandler()
        self._gui_handler.setLevel(logging.INFO)
        self.logger.addHandler(self._gui_handler)

        self._initialized = True

    def set_gui_callback(self, callback: Callable[[str], None]) -> None:
        """GUI 로그 콜백 설정"""
        if self._gui_handler:
            self._gui_handler.set_callback(callback)

    def info(self, msg: str) -> None:
        """INFO 레벨 로그"""
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        """WARNING 레벨 로그"""
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        """ERROR 레벨 로그"""
        self.logger.error(msg)

    def debug(self, msg: str) -> None:
        """DEBUG 레벨 로그"""
        self.logger.debug(msg)

    def get_logger(self) -> logging.Logger:
        """내부 로거 반환"""
        return self.logger


def setup_logging(gui_callback: Optional[Callable[[str], None]] = None) -> CrawlerLogger:
    """
    로깅 시스템 초기화

    Args:
        gui_callback: GUI 로그 콜백 함수 (선택사항)

    Returns:
        CrawlerLogger 인스턴스
    """
    crawler_logger = CrawlerLogger()

    if gui_callback:
        crawler_logger.set_gui_callback(gui_callback)

    # 다른 모듈에서 사용할 수 있도록 루트 로거도 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    # selenium, urllib3 등 외부 라이브러리 로그 레벨 조정
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("webdriver_manager").setLevel(logging.WARNING)

    return crawler_logger


def get_logger() -> CrawlerLogger:
    """싱글톤 로거 인스턴스 반환"""
    return CrawlerLogger()


def clear_old_logs(days: int = 7) -> None:
    """
    오래된 로그 파일 정리

    Args:
        days: 보관 기간 (일)
    """
    import os
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(days=days)

    for log_file in LOG_DIR.glob("*.log"):
        if log_file.name == "crawler.log":
            continue

        try:
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff:
                log_file.unlink()
        except Exception:
            pass


def get_log_content(lines: int = 100) -> str:
    """
    최근 로그 내용 반환

    Args:
        lines: 반환할 라인 수

    Returns:
        로그 내용 문자열
    """
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except Exception:
        return ""

"""
GUI 메인 윈도우 모듈
PyQt5로 구현된 크롤러 GUI입니다.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit,
    QComboBox, QFileDialog, QMessageBox, QGroupBox,
    QSpacerItem, QSizePolicy, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont, QTextCursor

from .config import (
    APP_NAME, APP_VERSION, STYLE_SHEET,
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_X, WINDOW_Y,
    CRAWL_COUNT_OPTIONS, DEFAULT_CRAWL_COUNT, MAX_CRAWL_COUNT, SEARCH_URL,
    DATA_DIR, ASSETS_DIR
)
from .driver_setup import create_driver, close_driver
from .crawler_thread import CrawlerWorker
from .excel_saver import save_to_excel, generate_filename
from .logger import setup_logging, get_logger


class CrawlerMainWindow(QMainWindow):
    """삼삼엠투 숙박정보 크롤러 메인 윈도우"""

    def __init__(self):
        super().__init__()
        self.driver = None
        self.crawler_worker = None
        self.crawled_data = []
        self.is_crawling = False

        # 로거 초기화
        self.logger = setup_logging(self._append_log)

        self._init_ui()
        self._connect_signals()

        self.logger.info("프로그램이 시작되었습니다.")

    def _init_ui(self):
        """UI 초기화"""
        # 윈도우 기본 설정
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(700, 500)

        # 아이콘 설정
        icon_path = ASSETS_DIR / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 스타일 시트 적용
        self.setStyleSheet(STYLE_SHEET)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 타이틀
        title_label = QLabel(f"{APP_NAME} v{APP_VERSION}")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 컨트롤 그룹
        control_group = self._create_control_group()
        main_layout.addWidget(control_group)

        # 진행률 그룹
        progress_group = self._create_progress_group()
        main_layout.addWidget(progress_group)

        # 로그 그룹
        log_group = self._create_log_group()
        main_layout.addWidget(log_group)

        # 하단 버튼 그룹
        bottom_buttons = self._create_bottom_buttons()
        main_layout.addLayout(bottom_buttons)

    def _create_control_group(self) -> QGroupBox:
        """컨트롤 그룹 생성"""
        group = QGroupBox("크롤링 설정")
        layout = QHBoxLayout(group)

        # 홈페이지 접속 버튼
        self.btn_connect = QPushButton("홈페이지 접속")
        self.btn_connect.setFixedWidth(130)
        layout.addWidget(self.btn_connect)

        # 크롤링 시작 버튼
        self.btn_start = QPushButton("크롤링 시작")
        self.btn_start.setFixedWidth(130)
        self.btn_start.setEnabled(False)
        layout.addWidget(self.btn_start)

        # 크롤링 중단 버튼
        self.btn_stop = QPushButton("중단")
        self.btn_stop.setObjectName("stopButton")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # 수집 개수 설정: 숫자 직접 입력 + 빠른 선택
        count_label = QLabel("수집할 숙소 개수:")
        layout.addWidget(count_label)

        self.spin_count = QSpinBox()
        self.spin_count.setMinimum(1)
        self.spin_count.setMaximum(MAX_CRAWL_COUNT)
        self.spin_count.setValue(DEFAULT_CRAWL_COUNT)
        self.spin_count.setSuffix(" 개")
        self.spin_count.setMinimumWidth(90)
        layout.addWidget(self.spin_count)

        self.combo_count_preset = QComboBox()
        self.combo_count_preset.addItem("빠른 선택", None)
        for count in CRAWL_COUNT_OPTIONS:
            self.combo_count_preset.addItem(f"{count}개", count)
        self.combo_count_preset.currentIndexChanged.connect(self._on_preset_selected)
        layout.addWidget(self.combo_count_preset)

        return group

    def _create_progress_group(self) -> QGroupBox:
        """진행률 그룹 생성"""
        group = QGroupBox("진행 상황")
        layout = QVBoxLayout(group)

        # 상태 라벨
        status_layout = QHBoxLayout()
        self.status_label = QLabel("대기 중")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)

        self.count_label = QLabel("0 / 0")
        self.count_label.setAlignment(Qt.AlignRight)
        status_layout.addWidget(self.count_label)
        layout.addLayout(status_layout)

        # 프로그레스바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        return group

    def _create_log_group(self) -> QGroupBox:
        """로그 그룹 생성 (스크롤바가 가리지 않도록 높이 제한)"""
        group = QGroupBox("로그")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(260)
        self.log_text.setMaximumHeight(360)  # 스크롤바가 하단 버튼에 가리지 않도록
        self.log_text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # 세로 스크롤바 항상 표시 (로그를 스크롤하여 모두 볼 수 있도록)
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self.log_text)

        return group

    def _create_bottom_buttons(self) -> QHBoxLayout:
        """하단 버튼 레이아웃 생성 (로그 지우기는 중앙)"""
        layout = QHBoxLayout()

        # 엑셀로 저장 버튼
        self.btn_save = QPushButton("엑셀로 저장")
        self.btn_save.setObjectName("saveButton")
        self.btn_save.setFixedWidth(130)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # 로그 지우기 버튼 (하단 중앙)
        self.btn_clear_log = QPushButton("로그 지우기")
        self.btn_clear_log.setFixedWidth(180)
        layout.addWidget(self.btn_clear_log, alignment=Qt.AlignCenter)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # 프로그램 종료 버튼
        self.btn_exit = QPushButton("프로그램 종료")
        self.btn_exit.setFixedWidth(130)
        layout.addWidget(self.btn_exit)

        return layout

    def _connect_signals(self):
        """시그널 연결"""
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_save.clicked.connect(self._on_save_clicked)
        self.btn_clear_log.clicked.connect(self._clear_log)
        self.btn_exit.clicked.connect(self._on_exit_clicked)

    def _append_log(self, message: str):
        """로그 메시지 추가"""
        self.log_text.append(message)
        # 스크롤을 맨 아래로 (많은 로그에서도 최신 정보를 볼 수 있도록)
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_log(self):
        """로그 지우기"""
        self.log_text.clear()

    def _update_status(self, status: str):
        """상태 업데이트"""
        self.status_label.setText(status)

    def _update_progress(self, current: int, total: int):
        """진행률 업데이트"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.count_label.setText(f"{current} / {total}")

    def _set_crawling_state(self, is_crawling: bool):
        """크롤링 상태 설정"""
        self.is_crawling = is_crawling
        self.btn_connect.setEnabled(not is_crawling)
        self.btn_start.setEnabled(not is_crawling and self.driver is not None)
        self.btn_stop.setEnabled(is_crawling)
        self.spin_count.setEnabled(not is_crawling)
        self.combo_count_preset.setEnabled(not is_crawling)

    def _on_preset_selected(self, index: int):
        """빠른 선택 콤보에서 선택 시 스핀박스 값 적용"""
        value = self.combo_count_preset.currentData()
        if value is not None:
            self.spin_count.setValue(value)

    # ============================================================
    # 버튼 이벤트 핸들러
    # ============================================================

    def _on_connect_clicked(self):
        """홈페이지 접속 버튼 클릭"""
        try:
            self._update_status("브라우저 시작 중...")
            self.logger.info("브라우저를 시작합니다...")
            self.btn_connect.setEnabled(False)

            # 드라이버 생성
            self.driver = create_driver(headless=False)

            # 검색 페이지 접속
            self._update_status("페이지 접속 중...")
            self.logger.info(f"페이지 접속 중: {SEARCH_URL}")
            self.driver.get(SEARCH_URL)

            self._update_status("접속 완료")
            self.logger.info("페이지 접속이 완료되었습니다.")
            self.btn_start.setEnabled(True)

            QMessageBox.information(
                self, "접속 완료",
                "삼삼엠투 검색 페이지에 접속했습니다.\n크롤링을 시작하려면 '크롤링 시작' 버튼을 클릭하세요."
            )

        except Exception as e:
            self.logger.error(f"접속 실패: {str(e)}")
            self._update_status("접속 실패")
            self.btn_connect.setEnabled(True)
            QMessageBox.critical(self, "오류", f"페이지 접속에 실패했습니다.\n{str(e)}")

    def _on_start_clicked(self):
        """크롤링 시작 버튼 클릭"""
        if not self.driver:
            QMessageBox.warning(self, "경고", "먼저 홈페이지에 접속해주세요.")
            return

        # 크롤링 개수 가져오기 (직접 입력값 사용)
        max_count = self.spin_count.value()

        # 확인 메시지
        reply = QMessageBox.question(
            self, "크롤링 시작",
            f"{max_count}개의 숙소 정보를 수집합니다.\n계속하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        # 크롤링 시작
        self._set_crawling_state(True)
        self._update_status("크롤링 중...")
        self.progress_bar.setValue(0)
        self.crawled_data = []

        self.logger.info(f"크롤링을 시작합니다. 목표: {max_count}개")

        # 워커 스레드 생성 및 시작
        self.crawler_worker = CrawlerWorker(self.driver, max_count)
        self.crawler_worker.progress_signal.connect(self._on_crawl_progress)
        self.crawler_worker.log_signal.connect(self._append_log)
        self.crawler_worker.finished_signal.connect(self._on_crawl_finished)
        self.crawler_worker.error_signal.connect(self._on_crawl_error)
        self.crawler_worker.start()

    def _on_stop_clicked(self):
        """크롤링 중단 버튼 클릭"""
        reply = QMessageBox.question(
            self, "크롤링 중단",
            "크롤링을 중단하시겠습니까?\n현재까지 수집된 데이터는 유지됩니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.crawler_worker:
                self.crawler_worker.stop()
            self.logger.warning("크롤링이 사용자에 의해 중단되었습니다.")

    def _on_save_clicked(self):
        """엑셀로 저장 버튼 클릭"""
        if not self.crawled_data:
            QMessageBox.warning(self, "경고", "저장할 데이터가 없습니다.")
            return

        # 기본 파일명 생성
        default_filename = generate_filename()
        default_path = str(DATA_DIR / default_filename)

        # 파일 저장 다이얼로그
        filepath, _ = QFileDialog.getSaveFileName(
            self, "엑셀 파일 저장",
            default_path,
            "Excel Files (*.xlsx);;All Files (*)"
        )

        if not filepath:
            return

        # 확장자 확인
        if not filepath.endswith('.xlsx'):
            filepath += '.xlsx'

        try:
            self._update_status("저장 중...")
            if save_to_excel(self.crawled_data, filepath):
                self.logger.info(f"엑셀 파일 저장 완료: {filepath}")
                self._update_status("저장 완료")
                QMessageBox.information(
                    self, "저장 완료",
                    f"엑셀 파일이 저장되었습니다.\n{filepath}"
                )
            else:
                raise Exception("저장 실패")
        except Exception as e:
            self.logger.error(f"저장 실패: {str(e)}")
            self._update_status("저장 실패")
            QMessageBox.critical(self, "오류", f"파일 저장에 실패했습니다.\n{str(e)}")

    def _on_exit_clicked(self):
        """프로그램 종료 버튼 클릭"""
        if self.is_crawling:
            reply = QMessageBox.warning(
                self, "경고",
                "크롤링이 진행 중입니다.\n정말로 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        self.close()

    # ============================================================
    # 크롤러 워커 시그널 핸들러
    # ============================================================

    def _on_crawl_progress(self, current: int, total: int):
        """크롤링 진행률 업데이트"""
        self._update_progress(current, total)

    def _on_crawl_finished(self, data: list):
        """크롤링 완료 - 결과를 인터페이스 테이블에 표시"""
        self.crawled_data = data
        self._set_crawling_state(False)
        self._update_status("크롤링 완료")

        self.logger.info(f"크롤링이 완료되었습니다. 총 {len(data)}개 수집")

        if data:
            self.btn_save.setEnabled(True)
        else:
            self.logger.warning("수집된 데이터가 없습니다.")

    def _on_crawl_error(self, error_msg: str):
        """크롤링 에러"""
        self._set_crawling_state(False)
        self._update_status("오류 발생")
        self.logger.error(f"크롤링 오류: {error_msg}")
        QMessageBox.critical(self, "오류", f"크롤링 중 오류가 발생했습니다.\n{error_msg}")

    # ============================================================
    # 윈도우 이벤트
    # ============================================================

    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        # 크롤링 중이면 워커 중지
        if self.crawler_worker and self.crawler_worker.isRunning():
            self.crawler_worker.stop()
            self.crawler_worker.wait()

        # 드라이버 종료
        if self.driver:
            self.logger.info("브라우저를 종료합니다.")
            close_driver(self.driver)
            self.driver = None

        self.logger.info("프로그램이 종료되었습니다.")
        event.accept()

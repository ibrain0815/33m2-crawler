"""
삼삼엠투 숙박정보 크롤러
메인 실행 파일

사용법:
    python main.py
    또는 EXE 파일 직접 실행
"""

import sys
import os
import traceback
from pathlib import Path

# 현재 디렉토리를 path에 추가 (EXE 빌드 시 필요)
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 경우
    BASE_DIR = Path(sys._MEIPASS)
    os.chdir(Path(sys.executable).parent)
else:
    # 일반 Python 실행
    BASE_DIR = Path(__file__).parent

sys.path.insert(0, str(BASE_DIR))


def main():
    """메인 함수"""
    # PyQt5 임포트
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont

    # 고DPI 스케일링 설정
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 애플리케이션 생성
    app = QApplication(sys.argv)

    # 기본 폰트 설정
    font = QFont("맑은 고딕", 10)
    app.setFont(font)

    # 애플리케이션 정보 설정
    app.setApplicationName("33m2 크롤러")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("33m2 Crawler")

    try:
        # 메인 윈도우 임포트 및 생성
        from src.main_window import CrawlerMainWindow

        window = CrawlerMainWindow()
        window.show()

        # 이벤트 루프 실행
        sys.exit(app.exec_())

    except ImportError as e:
        error_msg = f"필요한 모듈을 찾을 수 없습니다.\n\n{str(e)}"
        QMessageBox.critical(None, "모듈 오류", error_msg)
        sys.exit(1)

    except Exception as e:
        error_msg = f"프로그램 실행 중 오류가 발생했습니다.\n\n{str(e)}\n\n{traceback.format_exc()}"
        QMessageBox.critical(None, "실행 오류", error_msg)
        sys.exit(1)


def setup_exception_hook():
    """전역 예외 처리기 설정"""
    def exception_hook(exc_type, exc_value, exc_tb):
        """예외 발생 시 호출되는 함수"""
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

        # 로그 파일에 기록
        try:
            log_dir = BASE_DIR / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "crash.log"

            with open(log_file, 'a', encoding='utf-8') as f:
                from datetime import datetime
                f.write(f"\n{'='*50}\n")
                f.write(f"Crash at {datetime.now()}\n")
                f.write(error_msg)
        except Exception:
            pass

        # 기본 예외 처리기 호출
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = exception_hook


if __name__ == '__main__':
    # 전역 예외 처리기 설정
    setup_exception_hook()

    # 메인 함수 실행
    main()

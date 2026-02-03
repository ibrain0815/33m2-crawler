"""Streamlit용 33m2 숙박정보 크롤러

PyQt5 GUI를 쓰지 않고, 순수 크롤링 로직만 사용해
웹에서 실행할 수 있도록 만든 전용 스크립트입니다.
"""

from pathlib import Path
from typing import List, Dict

import streamlit as st

from src.driver_setup import create_driver, close_driver
from src.room_crawler import crawl_rooms
from src.config import DEFAULT_CRAWL_COUNT, MAX_CRAWL_COUNT, DATA_DIR
from src.excel_saver import save_to_excel, generate_filename


def run_crawl(max_count: int) -> List[Dict]:
    """Selenium 드라이버를 생성해 목록 크롤링을 수행."""
    driver = None
    rooms: List[Dict] = []

    try:
        # Streamlit 환경에서는 headless 모드 권장
        driver = create_driver(headless=True)

        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def on_progress(current: int, total: int):
            ratio = current / total if total else 0.0
            progress_bar.progress(ratio)
            status_text.text(f"{current} / {total}")

        rooms = crawl_rooms(driver, max_count=max_count, progress_callback=on_progress)

    finally:
        if driver is not None:
            close_driver(driver)

    return rooms


def main():
    st.set_page_config(page_title="33m2 숙박정보 크롤러 (Streamlit)", layout="centered")

    st.title("33m2 숙박정보 크롤러 (Streamlit 전용)")
    st.write("PyQt5 GUI 없이, 웹에서 목록 크롤링과 엑셀 저장만 수행합니다.")

    # 수집 개수 설정
    max_count = st.number_input(
        "수집할 숙소 개수",
        min_value=1,
        max_value=MAX_CRAWL_COUNT,
        value=DEFAULT_CRAWL_COUNT,
        step=1,
    )

    if st.button("크롤링 시작"):
        with st.spinner("크롤링 중입니다. 잠시만 기다려 주세요..."):
            rooms = run_crawl(int(max_count))

        if not rooms:
            st.warning("수집된 데이터가 없습니다.")
            return

        st.success(f"크롤링 완료: {len(rooms)}개 수집됨")

        # 간단히 상위 몇 개를 화면에 표로 보여주기
        st.dataframe(rooms[:20])

        # 엑셀 저장 및 다운로드 버튼 제공
        save_path = Path(DATA_DIR) / generate_filename()
        if save_to_excel(rooms, str(save_path)):
            st.info(f"엑셀 파일이 저장되었습니다: {save_path}")
            with open(save_path, "rb") as f:
                st.download_button(
                    label="엑셀 다운로드",
                    data=f,
                    file_name=save_path.name,
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                )
        else:
            st.error("엑셀 저장에 실패했습니다.")


if __name__ == "__main__":
    main()


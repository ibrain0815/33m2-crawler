"""
프로그램 아이콘 생성 스크립트
간단한 아이콘을 생성합니다.
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Pillow가 설치되어 있지 않습니다. pip install pillow로 설치하세요.")

ASSETS_DIR = Path(__file__).parent / "assets"


def create_simple_icon():
    """간단한 아이콘 생성"""
    if not HAS_PIL:
        print("Pillow가 필요합니다.")
        return

    # 256x256 크기의 이미지 생성
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 배경 원 (파란색)
    margin = 10
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill='#4472C4',
        outline='#2850a2',
        width=3
    )

    # 집 모양 그리기 (흰색)
    # 지붕
    roof_points = [
        (size // 2, 50),  # 꼭대기
        (60, 120),  # 왼쪽
        (size - 60, 120),  # 오른쪽
    ]
    draw.polygon(roof_points, fill='white')

    # 집 본체
    draw.rectangle([80, 120, size - 80, 200], fill='white')

    # 문
    draw.rectangle([110, 150, 146, 200], fill='#4472C4')

    # 창문
    draw.rectangle([160, 140, 190, 170], fill='#4472C4')

    # "33" 텍스트
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    text = "33"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (size - text_width) // 2
    draw.text((text_x, 205), text, fill='white', font=font)

    # PNG로 저장
    png_path = ASSETS_DIR / "icon.png"
    img.save(png_path, 'PNG')
    print(f"PNG 아이콘 생성: {png_path}")

    # ICO로 저장 (여러 크기 포함)
    ico_path = ASSETS_DIR / "icon.ico"
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    for icon_size in icon_sizes:
        resized = img.resize(icon_size, Image.LANCZOS)
        icons.append(resized)

    icons[0].save(
        ico_path,
        format='ICO',
        sizes=[(i.width, i.height) for i in icons],
        append_images=icons[1:]
    )
    print(f"ICO 아이콘 생성: {ico_path}")

    print("아이콘 생성 완료!")


def create_placeholder_icon():
    """Pillow 없이 플레이스홀더 메시지 생성"""
    readme_path = ASSETS_DIR / "ICON_README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""아이콘 파일 안내
================

icon.ico 파일과 icon.png 파일이 필요합니다.

아이콘 생성 방법:
1. pip install pillow 설치 후 python create_icon.py 실행
2. 또는 직접 아이콘 파일을 이 폴더에 추가

권장 크기:
- icon.ico: 256x256 (멀티 해상도 포함)
- icon.png: 256x256

아이콘이 없어도 프로그램 실행에는 문제 없습니다.
""")
    print(f"안내 파일 생성: {readme_path}")


if __name__ == "__main__":
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    if HAS_PIL:
        create_simple_icon()
    else:
        create_placeholder_icon()
        print("\nPillow 설치 후 다시 실행하세요:")
        print("pip install pillow")

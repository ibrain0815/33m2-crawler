# 삼삼엠투 웹사이트 구조 분석

## 기본 정보
- 메인 URL: https://web.33m2.co.kr/guest/main
- 검색 URL: https://web.33m2.co.kr/guest/search
- 봇 감지: 403 Forbidden (User-Agent 및 자동화 감지 적용)

## 분석 필요 항목

### 1. 숙소 카드 구조 (Selenium으로 확인 필요)
실제 접속 후 개발자 도구(F12)로 확인해야 할 항목:

```
예상 구조:
<div class="room-card" 또는 "property-item">
  <div class="room-image">
    <img src="..." alt="숙소 이미지">
  </div>
  <div class="room-info">
    <h3 class="room-title">숙소명</h3>
    <p class="room-location">위치</p>
    <span class="room-price">가격</span>
    <span class="room-rating">평점</span>
  </div>
</div>
```

### 2. 확인해야 할 선택자
- 숙소 제목: `.room-title`, `h2`, `h3` 등
- 가격 정보: `.price`, `.room-price` 등
- 위치: `.location`, `.address` 등
- 이미지: `img` 태그의 `src` 속성
- 평점: `.rating`, `.score` 등

### 3. 페이지 로딩 방식
확인 필요:
- [ ] 페이지네이션 (1, 2, 3... 페이지 버튼)
- [ ] 무한 스크롤 (스크롤 시 자동 로딩)
- [ ] "더보기" 버튼 클릭 방식

### 4. API 분석
개발자 도구 Network 탭에서 확인:
- XHR/Fetch 요청 확인
- API 엔드포인트 URL
- 요청/응답 데이터 구조

## 크롤링 전략

### 봇 감지 우회
1. User-Agent 설정 (실제 Chrome 브라우저와 동일하게)
2. webdriver 속성 숨기기
3. 랜덤 딜레이 적용 (2-5초)
4. navigator.webdriver 플래그 비활성화

### 데이터 수집 흐름
1. Chrome 브라우저로 검색 페이지 접속
2. 페이지 로딩 대기 (WebDriverWait)
3. 숙소 카드 요소 탐색
4. 각 카드에서 필요한 정보 추출
5. 다음 페이지/스크롤로 추가 데이터 수집
6. 수집된 데이터 저장

## 주의사항
- 과도한 요청 자제 (서버 부하 방지)
- robots.txt 확인
- 개인정보 수집 금지
- 수집된 데이터는 개인 학습 목적으로만 사용

---
작성일: 2026-02-01
상태: 실제 접속 후 업데이트 필요

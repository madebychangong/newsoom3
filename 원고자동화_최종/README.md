# 원고 자동화 시스템

블로그 원고를 회사 검수 기준에 맞게 자동으로 수정하는 시스템입니다.

## 📁 필수 파일

1. **auto_manuscript_rewriter.py** - 핵심 수정 엔진
2. **batch_rewrite_manuscripts.py** - 배치 처리 (여러 원고 한번에 처리)
3. **manuscript_gui.py** - GUI 인터페이스
4. **블로그 작업_엑셀템플릿.xlsx** - 입력 데이터 (검수전 시트 사용)
5. **금칙어 리스트.xlsx** - 금칙어와 대체어 목록

## 🎯 검수 기준 (ALL 7개 정확히 충족)

1. ✅ 첫 문단에 통키워드 정확히 2회
2. ✅ 통키워드로 시작하는 문장 정확히 2개
3. ✅ 첫 문단 키워드 사이 최소 2문장
4. ✅ 글자수 300~900자
5. ✅ 나머지 통키워드 (엑셀 D열)
6. ✅ 조각키워드 (엑셀 E열)
7. ✅ 서브키워드 목록수 (2회 이상 등장, ^^, ??, ... 포함)

## 📌 추가 가이드라인

- **금칙어 치환**: 금칙어 리스트.xlsx의 대체어로 자동 변환
- **조사 처리**:
  - 한 글자 조사 (에, 를, 가): 우회 문장으로 작성
  - 두 글자 이상 조사 (에서, 으로): 띄어쓰기 사용
- **글 구조**:
  - 도입부: 불편함/고민 표현
  - 마무리: 댓글 유도/정보 공유 요청

## 🚀 사용법

### 1. API 키 설정

```bash
export GEMINI_API_KEY='your-api-key-here'
```

### 2. GUI로 실행 (단일 원고 수정)

```bash
python manuscript_gui.py
```

### 3. 배치 처리 (여러 원고 한번에)

```bash
# 전체 처리
python batch_rewrite_manuscripts.py

# 처음 3개만 테스트
python batch_rewrite_manuscripts.py --max-rows 3

# 다른 파일 사용
python batch_rewrite_manuscripts.py --input 다른파일.xlsx

# API 키를 파라미터로 전달
python batch_rewrite_manuscripts.py --api-key 'your-api-key'
```

## 📊 출력 형식

- **개별 txt 파일**: 각 키워드별로 `키워드.txt` 파일 생성
- **제목 제외**: # 으로 시작하는 제목 라인 자동 제거
- **통계 파일**: `통계.txt` 파일에 전체 결과 요약

## ⚙️ 모델 정보

- **사용 모델**: gemini-2.5-pro
- **재시도 횟수**: 최대 1회 (batch_rewrite_manuscripts.py에서 max_retries=1로 설정)

## 📝 주의사항

1. 기준 충족이 1순위, 자연스러움은 2순위입니다.
2. 원본 글 내용을 최대한 유지하고 키워드만 추가/수정합니다.
3. 조사 붙으면 카운팅되지 않으므로 반드시 띄어쓰기 사용하세요.

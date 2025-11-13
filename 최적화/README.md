# 원고 자동 검수 및 수정 시스템

회사 기준에 맞게 블로그 원고를 자동으로 검수하고 수정하는 시스템입니다.

## 주요 기능

1. **원고 자동 검수**: 회사 기준에 맞는지 자동으로 체크
2. **원고 자동 수정**: Gemini API를 사용하여 자연스럽게 키워드 추가/삭제
3. **배치 처리**: 엑셀 파일의 여러 원고를 한번에 처리
4. **금칙어 치환**: 금칙어를 자동으로 대체어로 변경

## 회사 검수 기준

### 1. 글자수
- **목표**: 300~900자 (공백/줄바꿈 제외)
- 너무 길면 축약, 짧으면 내용 추가

### 2. 첫 문단 규칙
- **통키워드 정확히 2회** 출현
- **통키워드로 시작하는 문장(줄) 2개**
- 예: "강남 맛집 추천 때문에..." (1번째)
      "강남 맛집 추천 이렇게..." (2번째)

### 3. 나머지 부분 키워드 (첫 문단 제외)
- D열: 통키워드 반복수 (예: "강남 맛집 추천 : 0")
- E열: 조각키워드 반복수 (예: "강남 : 2\n맛집 : 3\n추천 : 1")

### 4. 서브키워드
- F열: 서브키워드 목록 수
- 2회 이상 등장하는 단어 개수
- 통키워드, 조각키워드는 제외

### 5. 키워드 카운팅 규칙 (매우 중요!)
- 키워드 뒤에 **조사가 바로 붙으면 카운팅 X**
- 키워드 뒤에 **띄어쓰기나 문장부호**가 있어야 카운팅 O

**예시:**
- ❌ "강남 맛집 추천을 찾아서" → 카운팅 X (조사 '을' 붙음)
- ✅ "강남 맛집 추천 찾아서" → 카운팅 O (띄어쓰기)
- ✅ "강남 맛집 추천." → 카운팅 O (문장부호)
- ✅ "강남 맛집 추천 관련해서" → 카운팅 O (자연스러움)

### 6. 금칙어 치환
- 금칙어 절대 사용 금지
- 자연스러운 대체어로 교체
- 금칙어 리스트.xlsx 파일에서 로드

## 설치

```bash
pip install pandas openpyxl google-generativeai
```

## 사용법

### 1. GUI로 사용하기 (가장 쉬운 방법) ⭐

GUI를 사용하면 명령어 없이 쉽게 원고를 수정할 수 있습니다.

**Windows:**
```
run_gui.bat 더블클릭
```

**Linux/Mac:**
```bash
./run_gui.sh
```

**또는 직접 실행:**
```bash
python manuscript_gui.py
```

**GUI 사용 방법:**
1. **Gemini API 키** 입력 (필수)
2. **엑셀 파일** 선택 (블로그 작업_엑셀템플릿.xlsx)
3. **처리할 행수** 설정 (0 = 전체)
4. **시작** 버튼 클릭
5. 진행 상황을 실시간으로 확인
6. 완료 후 결과 파일 자동 저장

### 2. 명령줄로 사용하기

#### 2-1. Gemini API 키 설정

```bash
export GEMINI_API_KEY='your-api-key-here'
```

#### 2-2. 단일 원고 검수

```bash
cd 최적화
python auto_manuscript_rewriter.py
```

#### 2-3. 배치 처리

```bash
# 기본 사용 (검수전 시트의 모든 원고 처리)
python batch_rewrite_manuscripts.py

# 최대 5개만 처리
python batch_rewrite_manuscripts.py --max-rows 5

# API 키를 직접 전달
python batch_rewrite_manuscripts.py --api-key 'your-api-key-here'

# 출력 파일명 지정
python batch_rewrite_manuscripts.py --output '수정결과.xlsx'
```

#### 2-4. 원고 검수만 (수정 없이)

```bash
python manuscript_checker.py
```

## 파일 구조

```
최적화/
├── manuscript_gui.py                 # GUI 애플리케이션 ⭐
├── run_gui.bat                       # Windows GUI 실행 스크립트
├── run_gui.sh                        # Linux/Mac GUI 실행 스크립트
├── auto_manuscript_rewriter.py       # 자동 원고 수정 (Gemini API)
├── batch_rewrite_manuscripts.py      # 배치 처리 (CLI)
├── manuscript_checker.py             # 원고 검수 (분석만)
├── demo_analysis.py                  # 데모 분석 (API 키 불필요)
├── forbidden_words_loader.py         # 금칙어 로더
├── 블로그 작업_엑셀템플릿.xlsx         # 원고 데이터
├── 금칙어 리스트.xlsx                 # 금칙어 및 대체어
└── README.md                         # 이 파일
```

## 출력 예시

```
====================================================================================================
원고 분석 - 키워드: 강남 맛집 추천
====================================================================================================
글자수: 356자 (목표: 300~900자)
첫문단 통키워드: 2회 (목표: 2회)
통키워드 문장 시작: 2개 (목표: 2개)

🤖 Gemini가 원고를 수정 중...

✅ 수정 완료!
====================================================================================================
수정 후 상태:
  글자수: 462자
  첫문단 통키워드: 2회
  통키워드 문장 시작: 2개
```

## 주요 클래스 및 함수

### AutoManuscriptRewriter

```python
from auto_manuscript_rewriter import AutoManuscriptRewriter

# 초기화
rewriter = AutoManuscriptRewriter(
    forbidden_words_file='금칙어 리스트.xlsx',
    gemini_api_key='your-api-key'
)

# 원고 수정
result = rewriter.rewrite_manuscript(
    manuscript="원고 텍스트...",
    keyword="강남 맛집 추천",
    target_whole_str="강남 맛집 추천 : 0",
    target_pieces_str="강남 : 2\n맛집 : 3\n추천 : 1",
    target_subkeywords=5
)

if result['success']:
    print(result['rewritten'])
```

### ManuscriptChecker

```python
from manuscript_checker import ManuscriptChecker

# 초기화
checker = ManuscriptChecker(forbidden_words_file='금칙어 리스트.xlsx')

# 원고 검수
result = checker.check_manuscript(
    manuscript="원고 텍스트...",
    keyword="강남 맛집 추천",
    target_whole_str="강남 맛집 추천 : 0",
    target_pieces_str="강남 : 2\n맛집 : 3",
    target_subkeywords=5
)

# 검수 결과
print(f"합격: {result['pass']}")
print(f"문제점: {result['issues']}")
```

## 분석 도구

다음 스크립트들은 회사 기준을 발견하기 위해 사용한 분석 도구입니다:

- `find_c_meaning.py` - C열 글자수 의미 분석
- `find_sentence_pattern.py` - 문장 패턴 분석
- `verify_rest_paragraph.py` - 첫 문단/나머지 부분 검증
- `check_avg_chars.py` - 평균 글자수 계산
- `analyze_excel.py` - 엑셀 구조 분석

## 통계

검수 후 원고 분석 결과 (20개 샘플):
- **평균 글자수**: 462자
- **중간값**: 430자
- **범위**: 174~1012자
- **가장 많은 범위**: 300~500자 (55%)

## 주의사항

1. **자연스러운 키워드 추가**: 억지로 반복하지 말고, 문맥에 맞게 자연스럽게 추가
2. **띄어쓰기 규칙**: 조사를 억지로 띄우지 말고, 문장을 우회해서 작성
3. **문체 유지**: 원본의 말투와 느낌 유지
4. **금칙어 주의**: 금칙어는 절대 사용 금지

## 라이선스

Company Internal Use Only

---

**버전**: 2.0 (회사 기준 기반)
**최종 업데이트**: 2025-11-13

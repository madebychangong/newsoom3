#!/usr/bin/env python3
"""
Gemini API를 사용한 자동 원고 수정 시스템
- 회사 검수 기준에 맞게 자동으로 원고 수정
- 자연스러운 문맥으로 키워드 추가/삭제
"""

import os
import re
import pandas as pd
from typing import Dict, List, Tuple
from collections import Counter
import google.generativeai as genai


class AutoManuscriptRewriter:
    """원고 자동 검수 및 수정 시스템"""

    def __init__(self, forbidden_words_file='금칙어 리스트.xlsx', gemini_api_key=None):
        """초기화"""
        self.forbidden_words_file = forbidden_words_file
        self.load_forbidden_words()

        # Gemini API 설정
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY 환경변수를 설정하거나 gemini_api_key 파라미터를 전달하세요.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def load_forbidden_words(self):
        """금칙어 리스트 로드"""
        try:
            df = pd.read_excel(self.forbidden_words_file)
            self.forbidden_words = {}

            for idx, row in df.iterrows():
                forbidden = row.iloc[1]  # B열
                if pd.notna(forbidden) and forbidden != '금칙어':
                    alternatives = []
                    for i in range(2, len(row)):  # C열 이후
                        if pd.notna(row.iloc[i]):
                            alternatives.append(str(row.iloc[i]))
                    if alternatives:
                        self.forbidden_words[str(forbidden)] = alternatives

            print(f"✅ 금칙어 {len(self.forbidden_words)}개 로드됨")
        except Exception as e:
            print(f"⚠️ 금칙어 로드 실패: {e}")
            self.forbidden_words = {}

    def get_first_paragraph(self, text: str) -> str:
        """첫 문단 추출"""
        lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
        text_no_title = '\n'.join(lines)
        paragraphs = text_no_title.split('\n\n')
        return paragraphs[0].strip() if paragraphs else ""

    def get_rest_paragraphs(self, text: str) -> str:
        """첫 문단 제외한 나머지"""
        lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
        text_no_title = '\n'.join(lines)
        paragraphs = text_no_title.split('\n\n')
        return '\n\n'.join(paragraphs[1:]).strip() if len(paragraphs) > 1 else ""

    def count_keyword(self, text: str, keyword: str) -> int:
        """키워드 카운팅 (띄어쓰기 기준)"""
        if not keyword or pd.isna(keyword):
            return 0
        pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
        return len(re.findall(pattern, text))

    def count_sentences_starting_with(self, text: str, keyword: str) -> int:
        """키워드로 시작하는 문장(줄) 개수"""
        if not keyword:
            return 0
        count = 0
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith(keyword):
                count += 1
        return count

    def count_subkeywords(self, text: str, exclude_keywords: List[str] = None) -> int:
        """서브키워드 목록 수 (2회 이상 등장하는 단어)"""
        if exclude_keywords is None:
            exclude_keywords = []

        words = re.findall(r'[가-힣]+', text)
        punctuations = re.findall(r'([^\w\s가-힣])\1+', text)

        word_counter = Counter(words)
        punct_counter = Counter(punctuations)

        subkeywords = set()
        for word, count in word_counter.items():
            if count >= 2 and len(word) >= 2 and word not in exclude_keywords:
                subkeywords.add(word)

        for punct, count in punct_counter.items():
            if count >= 2:
                subkeywords.add(punct * 2)

        return len(subkeywords)

    def parse_target_value(self, value_str) -> Dict[str, int]:
        """D, E열 목표값 파싱"""
        if pd.isna(value_str) or value_str == '-':
            return {}

        result = {}
        lines = str(value_str).split('\n')
        for line in lines:
            if ':' in line:
                parts = line.split(':')
                kw = parts[0].strip()
                count = int(parts[1].strip())
                result[kw] = count
        return result

    def analyze_manuscript(self, manuscript: str, keyword: str,
                          target_whole_str: str, target_pieces_str: str,
                          target_subkeywords: int) -> Dict:
        """원고 분석"""
        text_no_title = '\n'.join([line for line in manuscript.split('\n')
                                   if not line.strip().startswith('#')])

        첫문단 = self.get_first_paragraph(manuscript)
        나머지 = self.get_rest_paragraphs(manuscript)

        target_whole = self.parse_target_value(target_whole_str)
        target_pieces = self.parse_target_value(target_pieces_str)

        # 현재 상태
        actual_chars = len(text_no_title.replace(' ', '').replace('\n', ''))
        첫문단_통키워드 = self.count_keyword(첫문단, keyword)
        전체_통키워드_문장시작 = self.count_sentences_starting_with(text_no_title, keyword)

        # 나머지 부분 통키워드
        나머지_통키워드 = {}
        for kw, target in target_whole.items():
            actual = self.count_keyword(나머지, kw)
            나머지_통키워드[kw] = {'target': target, 'actual': actual, 'diff': target - actual}

        # 나머지 부분 조각키워드
        나머지_조각키워드 = {}
        for kw, target in target_pieces.items():
            actual = self.count_keyword(나머지, kw)
            나머지_조각키워드[kw] = {'target': target, 'actual': actual, 'diff': target - actual}

        # 서브키워드
        exclude_list = [keyword] if keyword else []
        if target_pieces:
            exclude_list.extend(target_pieces.keys())
        actual_subkeywords = self.count_subkeywords(text_no_title, exclude_list)

        return {
            'chars': actual_chars,
            'chars_in_range': 300 <= actual_chars <= 900,
            '첫문단_통키워드': 첫문단_통키워드,
            '통키워드_문장시작': 전체_통키워드_문장시작,
            '나머지_통키워드': 나머지_통키워드,
            '나머지_조각키워드': 나머지_조각키워드,
            'subkeywords': {'target': target_subkeywords, 'actual': actual_subkeywords}
        }

    def create_rewrite_prompt(self, manuscript: str, keyword: str, analysis: Dict,
                             target_whole_str: str, target_pieces_str: str) -> str:
        """Gemini용 수정 프롬프트 생성"""

        # 금칙어 리스트
        forbidden_list = list(self.forbidden_words.keys())[:30]  # 상위 30개만

        prompt = f"""당신은 블로그 원고를 회사 검수 기준에 맞게 수정하는 전문가입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 먼저 이해하세요: 통키워드란?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**통키워드: {keyword}**

이것은 이 원고의 핵심 주제입니다.
- 원고 전체가 "{keyword}"에 대한 내용이어야 합니다
- 억지로 개수만 맞추지 말고, **자연스럽게 주제에 맞게** 작성하세요
- 예: "{keyword}"가 주제인 원고에서 "{keyword}"를 자연스럽게 언급하는 것

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 절대적 규칙 - 반드시 지켜야 합니다! 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 우선순위: 회사 기준 준수 > 자연스러움

## 규칙 1: 첫 문단에 통키워드 정확히 2회
- **왜?** 원고 시작부터 주제를 명확히 하기 위해
- **어떻게?** 첫 문단(빈 줄 전까지)에서 "{keyword}"를 자연스럽게 2번 언급
- **검증:** 1번 ❌ / 2번 ✅ / 3번 ❌

⚠️⚠️⚠️ **극도로 중요: 키워드 뒤에 조사 붙으면 카운팅 안 됨!**

❌ **이렇게 쓰면 카운팅 안 됨 (조사 붙음):**
- "{keyword}에 대한" → X
- "{keyword}에 대해" → X
- "{keyword}이라는" → X
- "{keyword}라는" → X
- "{keyword}를" → X
- "{keyword}을" → X
- "{keyword}가" → X
- "{keyword}이" → X

✅ **이렇게 써야 카운팅 됨 (조사 없음):**
- "{keyword} 관련해서" → O
- "{keyword} 때문에" → O
- "{keyword} 알아보다가" → O
- "{keyword} 정보를" → O
- "{keyword} 후기가" → O
- "{keyword}," → O (쉼표 뒤 띄어쓰기)
- "{keyword}." → O (마침표)

## 규칙 2: 전체 원고에서 통키워드로 시작하는 문장 정확히 2개
- **왜?** 주제를 강조하기 위해
- **어떻게?** 줄 맨 앞에 "{keyword}"로 시작하는 문장 2개 작성
- **검증:** 0개 ❌ / 1개 ❌ / 2개 ✅ / 3개 ❌

✅ **올바른 예시 (조사 없음):**
  * "{keyword} 관련해서 고민이 많아서..."
  * "{keyword} 알아보다가 막막해서..."
  * "{keyword} 후기를 찾아보니..."

❌ **잘못된 예시 (조사 붙음 - 카운팅 안 됨!):**
  * "{keyword}에 대해..." → "에 대해" 붙음 X
  * "{keyword}에 대한..." → "에 대한" 붙음 X
  * "{keyword}이라는..." → "이라는" 붙음 X
  * "{keyword}를..." → "를" 붙음 X

## 규칙 3: 글자수 300~900자 (공백/줄바꿈 제외)

## 규칙 4: 나머지 부분 키워드 목표 달성
- {target_whole_str}
- {target_pieces_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 원본 원고
{manuscript}

# 금칙어 (절대 사용 금지)
{', '.join(forbidden_list)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 수정 방법

1. 원본 원고의 말투/스타일 유지
2. 키워드 주제에 맞게 내용 조정 (억지로 안 맞는 내용 유지 금지)
3. 위 4가지 절대적 규칙 준수

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 📤 출력 전 검증 (반드시!)

작성 후 직접 세어보세요:

1. 첫 문단에 "{keyword}" 몇 번? → 정확히 2번이어야 함!
   (조사 붙은 건 카운팅 안 됨!)

2. 전체 원고에서 "{keyword}"로 시작하는 줄 몇 개? → 정확히 2개여야 함!
   (조사 붙은 건 카운팅 안 됨!)

3. "{keyword}에", "{keyword}를" 같은 표현 있나? → 없어야 함!

4. 글자수 300~900자 범위 내? (공백/줄바꿈 제외)

**위 4가지 중 하나라도 실패면 다시 작성하세요!**

# 📤 출력
수정된 원고만 출력하세요 (설명 금지).
"""
        return prompt

    def rewrite_manuscript(self, manuscript: str, keyword: str,
                          target_whole_str: str, target_pieces_str: str,
                          target_subkeywords: int) -> Dict:
        """원고 자동 수정"""

        # 1. 분석
        analysis = self.analyze_manuscript(manuscript, keyword, target_whole_str,
                                          target_pieces_str, target_subkeywords)

        print(f"\n{'=' * 100}")
        print(f"원고 분석 - 키워드: {keyword}")
        print(f"{'=' * 100}")
        print(f"글자수: {analysis['chars']}자 (목표: 300~900자)")
        print(f"첫문단 통키워드: {analysis['첫문단_통키워드']}회 (목표: 2회)")
        print(f"통키워드 문장 시작: {analysis['통키워드_문장시작']}개 (목표: 2개)")

        # 2. 프롬프트 생성
        prompt = self.create_rewrite_prompt(manuscript, keyword, analysis,
                                           target_whole_str, target_pieces_str)

        # 3. Gemini로 수정
        print(f"\n🤖 Gemini가 원고를 수정 중...")
        try:
            response = self.model.generate_content(prompt)
            rewritten = response.text.strip()

            # 4. 수정 후 재분석
            after_analysis = self.analyze_manuscript(rewritten, keyword, target_whole_str,
                                                    target_pieces_str, target_subkeywords)

            print(f"\n✅ 수정 완료!")
            print(f"{'=' * 100}")
            print(f"수정 후 상태:")
            print(f"  글자수: {after_analysis['chars']}자")
            print(f"  첫문단 통키워드: {after_analysis['첫문단_통키워드']}회")
            print(f"  통키워드 문장 시작: {after_analysis['통키워드_문장시작']}개")

            return {
                'success': True,
                'original': manuscript,
                'rewritten': rewritten,
                'before_analysis': analysis,
                'after_analysis': after_analysis
            }

        except Exception as e:
            print(f"❌ 수정 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'original': manuscript
            }


def test_rewriter():
    """테스트"""

    # API 키 확인
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수를 설정해주세요.")
        return

    rewriter = AutoManuscriptRewriter()

    # 테스트 원고
    test_manuscript = """갱년기홍조 때문에 정말 고민이 많습니다.
저는 50대 중반인데 요즘 너무 힘들어요.
갱년기홍조가 시작된 지 6개월이 넘었는데 증상이 심해요.
얼굴이 화끈거리고 열이 올라요.
병원에서 치료도 받아봤는데 부작용이 걱정되더라고요.
효과가 있는 방법 좀 알려주세요."""

    keyword = "갱년기홍조"
    target_whole = "갱년기홍조 : 0"
    target_pieces = "-"
    target_subkeywords = 5

    result = rewriter.rewrite_manuscript(test_manuscript, keyword, target_whole,
                                        target_pieces, target_subkeywords)

    if result['success']:
        print(f"\n\n{'=' * 100}")
        print("수정된 원고:")
        print(f"{'=' * 100}")
        print(result['rewritten'])


if __name__ == '__main__':
    test_rewriter()

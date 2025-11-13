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
        self.model = genai.GenerativeModel('gemini-2.5-pro')

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

        prompt = f"""당신은 블로그 원고 수정 전문가입니다.

⚠️ **최우선 목표**: 아래 3가지 규칙을 정확히 지키세요.
**우선순위**: 1순위 규칙 준수 → 2순위 자연스러움

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 필수 규칙 3가지 (반드시 정확히 지켜야 함!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

키워드: **{keyword}**

**규칙 1: 첫 문단에 [{keyword}] 정확히 2번**
- 정확히 2번! (0번❌ 1번❌ 2번✅ 3번❌ 4번❌)
- 필수! 원본에 없어도 2번 만들어야 함!

**규칙 2: 전체 원고에서 [{keyword}]로 시작하는 문장 정확히 2개**
- 정확히 2개! (0개❌ 1개❌ 2개✅ 3개❌ 4개❌)
- 필수! 원본에 없어도 2개 만들어야 함!

**규칙 3: 글자수 300~900자** (공백/줄바꿈 제외)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 절대 금지 패턴 (카운팅 안 됨!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ {keyword}**에** 대해 (조사 붙음)
❌ {keyword}**에** 대한 (조사 붙음)
❌ {keyword}**에서** (조사 붙음)
❌ {keyword}**이라는** (조사 붙음)
❌ {keyword}**라는** (조사 붙음)
❌ {keyword}**를** (조사 붙음)
❌ {keyword}**을** (조사 붙음)
❌ {keyword}**가** (조사 붙음)
❌ {keyword}**이** (조사 붙음)
❌ {keyword}**도** (조사 붙음)

✅ {keyword} 관련해서 (띄어쓰기!)
✅ {keyword} 때문에 (띄어쓰기!)
✅ {keyword} 후기를 (띄어쓰기!)
✅ {keyword} 정보가 (띄어쓰기!)
✅ {keyword}, (마침표/쉼표 OK)
✅ {keyword}. (마침표/쉼표 OK)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 구체적 예시 (이렇게 작성하세요)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**올바른 첫 문단 예시 (2번 카운팅됨):**

{keyword} 관련해서 고민이 많습니다. 저는 50대 중반인데요, 최근 여러 증상으로 힘들어하고 있습니다. {keyword} 정보를 찾아보니 여러 방법이 있더라고요.

→ [{keyword} 관련해서] (1번 카운팅 ✅)
→ [{keyword} 정보를] (2번 카운팅 ✅)

**잘못된 첫 문단 예시 (0번 카운팅됨):**

{keyword}에 대해 궁금한 점이 있습니다. {keyword}에서 상담을 받으려고 하는데요.

→ [{keyword}에] (조사 붙음 ❌ 카운팅 안됨!)
→ [{keyword}에서] (조사 붙음 ❌ 카운팅 안됨!)

**문장 시작 예시 (정확히 2개만!):**

{keyword} 후기를 찾아보다가 이렇게 글을 남깁니다.
...
{keyword} 관련해서 궁금한 점이 있으면 언제든지 문의해주세요.

⚠️ 주의: 3개 이상 만들면 안 됩니다! 정확히 2개만!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 원본 원고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{manuscript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 출력 전 스스로 검증하세요!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작성 후 직접 세어보세요:

1. 첫 문단에서 [{keyword} ] (띄어쓰기) 또는 [{keyword}.] (마침표) 패턴이 정확히 2번?
   → [{keyword}에], [{keyword}를] 같은 건 카운팅 안 됨!
   → 3번 이상 쓰면 실격!

2. 줄 맨 앞에 [{keyword}]로 시작하는 문장이 정확히 2개?
   → [{keyword}에 대해...]로 시작하면 안 됨!
   → 3개 이상 쓰면 실격!

3. 글자수 300~900자? (공백/줄바꿈 제외)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✍️ 작성 방법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**우선순위 1번: 규칙 준수**
- 첫 문단에 [{keyword}] 정확히 2번
- 문장 시작 [{keyword}] 정확히 2개
- 이 두 가지는 절대 타협 불가!

**우선순위 2번: 가능하면 자연스럽게**
- 규칙을 지킨 상태에서, 최대한 자연스럽게 작성
- 원본의 주요 내용 유지
- 단, 규칙과 충돌하면 규칙이 우선!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 출력
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

수정된 원고만 출력하세요 (설명이나 메모 없이).
"""
        return prompt

    def rewrite_manuscript(self, manuscript: str, keyword: str,
                          target_whole_str: str, target_pieces_str: str,
                          target_subkeywords: int, max_retries: int = 3) -> Dict:
        """원고 자동 수정 (재시도 로직 포함)"""

        # 1. 분석
        analysis = self.analyze_manuscript(manuscript, keyword, target_whole_str,
                                          target_pieces_str, target_subkeywords)

        print(f"\n{'=' * 100}")
        print(f"원고 분석 - 키워드: {keyword}")
        print(f"{'=' * 100}")
        print(f"글자수: {analysis['chars']}자 (목표: 300~900자)")
        print(f"첫문단 통키워드: {analysis['첫문단_통키워드']}회 (목표: 2회)")
        print(f"통키워드 문장 시작: {analysis['통키워드_문장시작']}개 (목표: 2개)")

        # 재시도 루프
        rewritten = None  # 초기화
        after_analysis = None  # 초기화

        for attempt in range(max_retries):
            print(f"\n🤖 Gemini가 원고를 수정 중... (시도 {attempt + 1}/{max_retries})")

            try:
                # 2. 프롬프트 생성
                if attempt == 0 or rewritten is None:
                    # 첫 시도이거나 이전 시도에서 rewritten이 없으면 기본 프롬프트
                    prompt = self.create_rewrite_prompt(manuscript, keyword, analysis,
                                                       target_whole_str, target_pieces_str)
                else:
                    # 재시도 시 이전 실패 이유 포함
                    prompt = self.create_retry_prompt(manuscript, keyword, rewritten,
                                                     after_analysis, target_whole_str,
                                                     target_pieces_str)

                # 3. Gemini로 수정
                response = self.model.generate_content(prompt)
                rewritten = response.text.strip()

                # 4. 수정 후 재분석
                after_analysis = self.analyze_manuscript(rewritten, keyword, target_whole_str,
                                                        target_pieces_str, target_subkeywords)

                # 5. 검증
                first_para_ok = after_analysis['첫문단_통키워드'] == 2
                sentence_start_ok = after_analysis['통키워드_문장시작'] == 2
                chars_ok = after_analysis['chars_in_range']

                print(f"\n{'=' * 100}")
                print(f"수정 후 상태:")
                print(f"  글자수: {after_analysis['chars']}자 {'✅' if chars_ok else '❌'}")
                print(f"  첫문단 통키워드: {after_analysis['첫문단_통키워드']}회 {'✅' if first_para_ok else '❌'}")
                print(f"  통키워드 문장 시작: {after_analysis['통키워드_문장시작']}개 {'✅' if sentence_start_ok else '❌'}")

                # 핵심 규칙 2개가 모두 충족되면 성공
                if first_para_ok and sentence_start_ok:
                    print(f"✅ 성공! 기준 충족")
                    return {
                        'success': True,
                        'original': manuscript,
                        'rewritten': rewritten,
                        'before_analysis': analysis,
                        'after_analysis': after_analysis,
                        'attempts': attempt + 1
                    }
                else:
                    print(f"⚠️ 기준 미달, 재시도 필요...")
                    continue

            except Exception as e:
                print(f"❌ 수정 실패: {e}")
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': str(e),
                        'original': manuscript
                    }
                continue

        # 최대 재시도 횟수 초과
        print(f"⚠️ {max_retries}회 시도 후에도 기준 미달")
        return {
            'success': False,
            'error': f'{max_retries}회 재시도 후에도 기준 충족 실패',
            'original': manuscript,
            'rewritten': rewritten,
            'after_analysis': after_analysis,
            'attempts': max_retries
        }

    def create_retry_prompt(self, original: str, keyword: str, failed_text: str,
                           failed_analysis: Dict, target_whole_str: str,
                           target_pieces_str: str) -> str:
        """재시도용 프롬프트 (이전 실패 이유 포함)"""

        first_para_count = failed_analysis['첫문단_통키워드']
        sentence_start_count = failed_analysis['통키워드_문장시작']

        prompt = f"""이전 수정이 실패했습니다. 다시 수정해주세요.

⚠️ **최우선**: 규칙을 정확히 지키세요! 규칙 준수가 1순위입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 이전 실패 이유
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

키워드: **{keyword}**

첫 문단 [{keyword}] 카운팅: {first_para_count}회 (목표: 정확히 2회) {'✅' if first_para_count == 2 else '❌'}
문장 시작 [{keyword}] 개수: {sentence_start_count}개 (목표: 정확히 2개) {'✅' if sentence_start_count == 2 else '❌'}

**이전에 작성한 원고:**
{failed_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 다시 작성 시 주의사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**규칙 1: 첫 문단에 [{keyword}] 정확히 2번**
- 현재: {first_para_count}번 → 목표: 2번
- ⚠️ 3번 이상 절대 안 됨!

**규칙 2: [{keyword}]로 시작하는 문장 정확히 2개**
- 현재: {sentence_start_count}개 → 목표: 2개
- ⚠️ 3개 이상 절대 안 됨!

**절대 금지 패턴 (조사 붙으면 카운팅 안 됨!):**
❌ {keyword}에 ❌ {keyword}에서 ❌ {keyword}를 ❌ {keyword}가

**올바른 패턴 (띄어쓰기!):**
✅ {keyword} 관련해서 ✅ {keyword} 때문에 ✅ {keyword} 후기를

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 원본 원고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{original}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 이번엔 반드시 규칙 준수!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**필수 체크리스트: (절대 준수!)**
1. 첫 문단에서 [{keyword} ] (띄어쓰기) 패턴을 정확히 2번 사용 (1번❌ 3번❌)
2. 줄 맨 앞에 [{keyword} ]로 시작하는 문장을 정확히 2개 작성 (1개❌ 3개❌)
3. 조사 절대 금지!

**우선순위:**
1순위: 위 규칙 정확히 지키기 (필수!)
2순위: 가능하면 자연스럽게 (규칙 지킨 상태에서만)

수정된 원고만 출력하세요 (설명 없이).
"""
        return prompt


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

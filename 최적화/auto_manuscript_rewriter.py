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

    def count_sentences_between_keywords(self, paragraph: str, keyword: str) -> int:
        """첫 문단에서 키워드 사이 문장 개수"""
        if not keyword or not paragraph:
            return 0

        sentences = []
        for line in paragraph.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # 문장 분리 (., !, ? 기준)
                parts = re.split(r'[.!?]\s*', line)
                sentences.extend([s.strip() for s in parts if s.strip()])

        # 키워드 포함 문장 인덱스 찾기
        keyword_indices = []
        for i, sentence in enumerate(sentences):
            if keyword in sentence:
                keyword_indices.append(i)

        # 첫 번째와 두 번째 키워드 사이 문장 개수
        if len(keyword_indices) >= 2:
            return keyword_indices[1] - keyword_indices[0] - 1

        return 0

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
        첫문단_키워드사이_문장수 = self.count_sentences_between_keywords(첫문단, keyword)

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
            '첫문단_키워드사이_문장수': 첫문단_키워드사이_문장수,
            '나머지_통키워드': 나머지_통키워드,
            '나머지_조각키워드': 나머지_조각키워드,
            'subkeywords': {'target': target_subkeywords, 'actual': actual_subkeywords}
        }

    def create_rewrite_prompt(self, manuscript: str, keyword: str, analysis: Dict,
                             target_whole_str: str, target_pieces_str: str) -> str:
        """Gemini용 수정 프롬프트 생성"""

        # 금칙어 리스트
        forbidden_list = list(self.forbidden_words.keys())[:30]  # 상위 30개만

        # 나머지 통키워드 목록
        나머지_통키워드_rules = []
        for kw, data in analysis['나머지_통키워드'].items():
            나머지_통키워드_rules.append(f"  - [{kw}] 정확히 {data['target']}회 (첫 문단 이후 부분에서)")

        # 조각키워드 목록
        조각키워드_rules = []
        for kw, data in analysis['나머지_조각키워드'].items():
            조각키워드_rules.append(f"  - [{kw}] 정확히 {data['target']}회 (첫 문단 이후 부분에서)")

        # 서브키워드 목표
        서브키워드_target = analysis['subkeywords']['target']

        # 총 규칙 개수
        rule_count = 4  # 기본 4개: 첫문단 2회, 문장시작 2개, 키워드사이 2문장, 글자수
        if 나머지_통키워드_rules:
            rule_count += 1
        if 조각키워드_rules:
            rule_count += 1
        if 서브키워드_target > 0:
            rule_count += 1

        prompt = f"""🔴 절대 규칙: 아래 {rule_count}개 기준을 정확히 지켜야 합니다. 1개라도 어기면 실격입니다.

작업 방식:
- 원본 글 내용 최대한 유지
- 키워드만 추가하거나 위치 조정
- 글을 처음부터 새로 쓰지 말 것!

글 구조 (필수):
✅ 도입부: 불편함이나 고민 표현 (예: "~때문에 고민이 많습니다", "~로 힘들어요")
✅ 마무리: 댓글 유도 또는 정보 공유 요청 (예: "정보 공유 부탁드려요", "댓글로 알려주세요")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 엄격한 기준 ({rule_count}개 모두 정확히 지켜야 함!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

키워드: {keyword}

🔴 규칙 1: 첫 문단에 [{keyword}] 정확히 2번
   - 1번 ❌, 2번 ✅, 3번 ❌
   - 조사 붙으면 카운팅 안 됨!
   - 첫 번째와 두 번째 [{keyword}] 사이에 최소 2문장 이상 있어야 함!

🔴 규칙 2: [{keyword}]로 시작하는 문장 정확히 2개
   - 1개 ❌, 2개 ✅, 3개 ❌
   - 줄 맨 앞에서 시작해야 함!

🔴 규칙 3: 첫 문단 키워드 사이에 2문장 이상
   - 첫 번째 [{keyword}]와 두 번째 [{keyword}] 사이 최소 2문장

🔴 규칙 4: 글자수 300~900자 (공백 제외)"""

        # 나머지 통키워드
        rule_num = 5
        if 나머지_통키워드_rules:
            prompt += f"""

🔴 규칙 {rule_num}: 나머지 통키워드 (첫 문단 이후)"""
            for kw, data in analysis['나머지_통키워드'].items():
                prompt += f"""
   - [{kw}] 정확히 {data['target']}회 (±1도 안 됨!)"""
            rule_num += 1

        # 조각키워드
        if 조각키워드_rules:
            prompt += f"""

🔴 규칙 {rule_num}: 조각키워드 (첫 문단 이후)"""
            for kw, data in analysis['나머지_조각키워드'].items():
                prompt += f"""
   - [{kw}] 정확히 {data['target']}회 (±1도 안 됨!)"""
            rule_num += 1

        # 서브키워드
        if 서브키워드_target > 0:
            prompt += f"""

🔴 규칙 {rule_num}: 서브키워드 {서브키워드_target}개 이상
   - 2회 이상 등장하는 단어가 {서브키워드_target}개 이상
   - ^^, ??, ..., ;;, !! 같은 중복 문장부호도 2회 이상 사용하면 카운팅됨"""

        # 금칙어
        forbidden_list = list(self.forbidden_words.keys())[:10]
        if forbidden_list:
            prompt += f"""

🚫 금칙어 치환 필수:
{chr(10).join(f'   - {word} → {", ".join(self.forbidden_words[word][:2])}' for word in forbidden_list)}
(전체 {len(self.forbidden_words)}개)"""

        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 카운팅 규칙 (중요!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ 조사 붙으면 카운팅 안 됨:
   {keyword}에, {keyword}를, {keyword}가 등

✅ 띄어쓰기 있으면 카운팅됨:
   {keyword} 관련해서, {keyword} 때문에, {keyword} 정보를

📌 조사 처리 가이드:
   - 한 글자 조사 (에, 를, 가, 은, 이): 우회 문장으로 작성
     예) "{keyword}에 대해" → "{keyword} 관련해서"
   - 두 글자 이상 조사 (에서, 에게, 으로): 띄어쓰기로 가능
     예) "{keyword}에서" → "{keyword} 에서" (띄어쓰기)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 원본 원고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{manuscript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 출력 전 직접 세어보기!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

출력 전 반드시 확인:
✓ 첫 문단 [{keyword} ]: 정확히 2번?
✓ 문장 시작 [{keyword}]: 정확히 2개?
✓ 글자수: 300~900자?"""

        if 나머지_통키워드_rules:
            for kw, data in analysis['나머지_통키워드'].items():
                prompt += f"""
✓ [{kw}]: 정확히 {data['target']}회?"""

        if 조각키워드_rules:
            for kw, data in analysis['나머지_조각키워드'].items():
                prompt += f"""
✓ [{kw}]: 정확히 {data['target']}회?"""

        if 서브키워드_target > 0:
            prompt += f"""
✓ 서브키워드: {서브키워드_target}개 이상?"""

        prompt += """

수정된 원고만 출력하세요.
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

                # 5. 검증 - ALL 7개 기준을 정확히 체크
                first_para_ok = after_analysis['첫문단_통키워드'] == 2
                sentence_start_ok = after_analysis['통키워드_문장시작'] == 2
                키워드사이_문장수_ok = after_analysis['첫문단_키워드사이_문장수'] >= 2
                chars_ok = after_analysis['chars_in_range']

                # 나머지 통키워드 검증 (모든 키워드가 정확히 목표 횟수와 일치해야 함)
                나머지_통키워드_ok = True
                나머지_통키워드_errors = []
                for kw, data in after_analysis['나머지_통키워드'].items():
                    if data['actual'] != data['target']:
                        나머지_통키워드_ok = False
                        나머지_통키워드_errors.append(f"{kw}: {data['actual']}회 (목표: {data['target']}회)")

                # 조각키워드 검증 (모든 조각키워드가 정확히 목표 횟수와 일치해야 함)
                조각키워드_ok = True
                조각키워드_errors = []
                for kw, data in after_analysis['나머지_조각키워드'].items():
                    if data['actual'] != data['target']:
                        조각키워드_ok = False
                        조각키워드_errors.append(f"{kw}: {data['actual']}회 (목표: {data['target']}회)")

                # 서브키워드 검증 (목표 이상이어야 함)
                서브키워드_ok = after_analysis['subkeywords']['actual'] >= after_analysis['subkeywords']['target']

                # ALL 7개 기준이 모두 충족되어야 성공
                all_criteria_met = (first_para_ok and sentence_start_ok and 키워드사이_문장수_ok and
                                   chars_ok and 나머지_통키워드_ok and 조각키워드_ok and 서브키워드_ok)

                print(f"\n{'=' * 100}")
                print(f"수정 후 검증 결과:")
                print(f"  1. 글자수: {after_analysis['chars']}자 {'✅' if chars_ok else '❌'}")
                print(f"  2. 첫문단 통키워드: {after_analysis['첫문단_통키워드']}회 {'✅' if first_para_ok else '❌'}")
                print(f"  3. 통키워드 문장 시작: {after_analysis['통키워드_문장시작']}개 {'✅' if sentence_start_ok else '❌'}")
                print(f"  4. 첫문단 키워드 사이 문장: {after_analysis['첫문단_키워드사이_문장수']}개 (최소 2개) {'✅' if 키워드사이_문장수_ok else '❌'}")

                # 나머지 통키워드 출력
                print(f"  5. 나머지 통키워드: {'✅' if 나머지_통키워드_ok else '❌'}")
                if not 나머지_통키워드_ok:
                    for err in 나머지_통키워드_errors:
                        print(f"     - {err}")
                else:
                    for kw, data in after_analysis['나머지_통키워드'].items():
                        print(f"     - {kw}: {data['actual']}/{data['target']}회 ✅")

                # 조각키워드 출력
                print(f"  6. 조각키워드: {'✅' if 조각키워드_ok else '❌'}")
                if not 조각키워드_ok:
                    for err in 조각키워드_errors:
                        print(f"     - {err}")
                else:
                    for kw, data in after_analysis['나머지_조각키워드'].items():
                        print(f"     - {kw}: {data['actual']}/{data['target']}회 ✅")

                # 서브키워드 출력
                print(f"  7. 서브키워드 목록: {after_analysis['subkeywords']['actual']}개 (목표: {after_analysis['subkeywords']['target']}개 이상) {'✅' if 서브키워드_ok else '❌'}")

                # ALL 기준 충족 여부 확인
                if all_criteria_met:
                    print(f"\n✅ 성공! 모든 기준 충족 (7/7)")
                    return {
                        'success': True,
                        'original': manuscript,
                        'rewritten': rewritten,
                        'before_analysis': analysis,
                        'after_analysis': after_analysis,
                        'attempts': attempt + 1
                    }
                else:
                    # 실패한 기준 표시
                    failed_count = sum([
                        not chars_ok,
                        not first_para_ok,
                        not sentence_start_ok,
                        not 키워드사이_문장수_ok,
                        not 나머지_통키워드_ok,
                        not 조각키워드_ok,
                        not 서브키워드_ok
                    ])
                    print(f"\n⚠️ 기준 미달 ({7-failed_count}/7 충족), 재시도 필요...")
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
        """재시도용 프롬프트 (이전 실패 이유 포함 - ALL 7개 기준)"""

        first_para_count = failed_analysis['첫문단_통키워드']
        sentence_start_count = failed_analysis['통키워드_문장시작']
        키워드사이_문장수 = failed_analysis['첫문단_키워드사이_문장수']
        chars = failed_analysis['chars']
        chars_ok = failed_analysis['chars_in_range']

        # 나머지 통키워드 상태
        나머지_통키워드_status = []
        for kw, data in failed_analysis['나머지_통키워드'].items():
            icon = '✅' if data['actual'] == data['target'] else '❌'
            나머지_통키워드_status.append(f"{kw}: {data['actual']}회 (목표: {data['target']}회) {icon}")

        # 조각키워드 상태
        조각키워드_status = []
        for kw, data in failed_analysis['나머지_조각키워드'].items():
            icon = '✅' if data['actual'] == data['target'] else '❌'
            조각키워드_status.append(f"{kw}: {data['actual']}회 (목표: {data['target']}회) {icon}")

        # 서브키워드 상태
        sub_actual = failed_analysis['subkeywords']['actual']
        sub_target = failed_analysis['subkeywords']['target']
        sub_ok = sub_actual >= sub_target

        prompt = f"""이전 수정이 실패했습니다. 다시 수정해주세요.

⚠️ **최우선**: ALL 7개 규칙을 정확히 지키세요! 규칙 준수가 1순위입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 이전 실패 이유 (7개 기준 검증 결과)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

키워드: **{keyword}**

1. 글자수: {chars}자 (목표: 300-900자) {'✅' if chars_ok else '❌'}
2. 첫 문단 [{keyword}] 카운팅: {first_para_count}회 (목표: 정확히 2회) {'✅' if first_para_count == 2 else '❌'}
3. 문장 시작 [{keyword}] 개수: {sentence_start_count}개 (목표: 정확히 2개) {'✅' if sentence_start_count == 2 else '❌'}
4. 첫 문단 키워드 사이 문장: {키워드사이_문장수}개 (목표: 최소 2개) {'✅' if 키워드사이_문장수 >= 2 else '❌'}
5. 나머지 통키워드:
   {chr(10).join('   - ' + s for s in 나머지_통키워드_status) if 나머지_통키워드_status else '   (없음)'}
6. 조각키워드:
   {chr(10).join('   - ' + s for s in 조각키워드_status) if 조각키워드_status else '   (없음)'}
7. 서브키워드: {sub_actual}개 (목표: {sub_target}개 이상) {'✅' if sub_ok else '❌'}

**이전에 작성한 원고:**
{failed_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 다시 작성 시 주의사항 (ALL 7개 기준 충족 필수!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**기본 규칙 1: 첫 문단에 [{keyword}] 정확히 2번**
- 현재: {first_para_count}번 → 목표: 2번
- ⚠️ 3번 이상 절대 안 됨! 정확히 2번만!

**기본 규칙 2: [{keyword}]로 시작하는 문장 정확히 2개**
- 현재: {sentence_start_count}개 → 목표: 2개
- ⚠️ 3개 이상 절대 안 됨! 정확히 2개만!

**기본 규칙 3: 첫 문단 키워드 사이 문장 최소 2개**
- 현재: {키워드사이_문장수}개 → 목표: 최소 2개
- ⚠️ 첫 번째 [{keyword}]와 두 번째 [{keyword}] 사이에 문장 2개 이상!

**추가 규칙 4: 나머지 통키워드 정확한 횟수 사용**
{chr(10).join('- ' + s for s in 나머지_통키워드_status) if 나머지_통키워드_status else '(없음)'}

**추가 규칙 5: 조각키워드 정확한 횟수 사용**
{chr(10).join('- ' + s for s in 조각키워드_status) if 조각키워드_status else '(없음)'}

**추가 규칙 6: 서브키워드 목록 수 충족**
- 현재: {sub_actual}개 → 목표: {sub_target}개 이상

**추가 규칙 7: 글자수 범위**
- 현재: {chars}자 → 목표: 300-900자

**절대 금지 패턴 (조사 붙으면 카운팅 안 됨!):**
❌ {keyword}에 ❌ {keyword}에서 ❌ {keyword}를 ❌ {keyword}가

**올바른 패턴 (띄어쓰기!):**
✅ {keyword} 관련해서 ✅ {keyword} 때문에 ✅ {keyword} 후기를

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 원본 원고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{original}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 이번엔 반드시 ALL 7개 규칙 준수!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**필수 체크리스트: (모두 절대 준수!)**
1. 첫 문단에서 [{keyword} ] (띄어쓰기) 패턴을 정확히 2번 사용 (1번❌ 3번❌)
2. 줄 맨 앞에 [{keyword} ]로 시작하는 문장을 정확히 2개 작성 (1개❌ 3개❌)
3. 첫 문단에서 첫 번째와 두 번째 [{keyword}] 사이에 문장 최소 2개 배치
4. 나머지 통키워드를 정확히 지정된 횟수만큼 사용
5. 조각키워드를 정확히 지정된 횟수만큼 사용
6. 서브키워드를 지정된 개수 이상 사용 (^^, ??, ... 같은 중복 문장부호도 카운팅됨!)
7. 글자수를 300-900자 범위 내로 작성
8. 조사 절대 금지! (한 글자 조사는 우회, 두 글자 이상은 띄어쓰기)

**우선순위:**
1순위: 위 ALL 7개 규칙 정확히 지키기 (필수!)
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

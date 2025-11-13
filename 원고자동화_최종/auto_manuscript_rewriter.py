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

    def __init__(self, forbidden_words_file='금칙어 리스트.xlsx', gemini_api_key=None, model_choice=1):
        """초기화

        Args:
            forbidden_words_file: 금칙어 엑셀 파일 경로
            gemini_api_key: Gemini API 키
            model_choice: 1 = gemini-2.5-pro (고품질, 느림), 2 = gemini-2.0-flash-exp (빠름, 저렴)
        """
        self.forbidden_words_file = forbidden_words_file
        self.load_forbidden_words()

        # Gemini API 설정
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY 환경변수를 설정하거나 gemini_api_key 파라미터를 전달하세요.")

        genai.configure(api_key=api_key)

        # 모델 선택
        if model_choice == 2:
            model_name = 'gemini-2.0-flash-exp'
            print("🚀 모델: gemini-2.0-flash-exp (빠름, 저렴)")
        else:
            model_name = 'gemini-2.5-pro'
            print("🎯 모델: gemini-2.5-pro (고품질, 느림)")

        self.model = genai.GenerativeModel(model_name)

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
        """키워드로 시작하는 문장 개수 (., !, ? 기준으로 문장 분리)"""
        if not keyword:
            return 0

        # 문장 분리
        sentences = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # 문장 분리 (., !, ? 기준)
                parts = re.split(r'([.!?])\s*', line)
                current = ""
                for i, part in enumerate(parts):
                    if part in '.!?':
                        current += part
                        if current.strip():
                            sentences.append(current.strip())
                        current = ""
                    else:
                        current += part
                if current.strip():
                    sentences.append(current.strip())

        # 키워드로 시작하는 문장 카운팅
        count = 0
        for sentence in sentences:
            if sentence.startswith(keyword):
                count += 1

        return count

    def count_sentences_between_keywords(self, paragraph: str, keyword: str) -> int:
        """첫 문단에서 키워드 사이 문장 개수 (온점, 쉼표 기준)"""
        if not keyword or not paragraph:
            return 0

        # 제목 제거
        text = '\n'.join([line for line in paragraph.split('\n') if not line.strip().startswith('#')])

        # 온점(.)과 쉼표(,)로 문장 분리
        sentences = re.split(r'[.,]\s*', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # 정규식으로 정확한 키워드 매칭 (띄어쓰기 체크)
        keyword_pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'

        # 키워드 포함 문장 인덱스 찾기
        keyword_indices = []
        for i, sentence in enumerate(sentences):
            if re.search(keyword_pattern, sentence):
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

    def check_forbidden_words(self, text: str) -> List[Dict[str, str]]:
        """금칙어 체크 및 대체어 제안"""
        found = []
        for forbidden, alternatives in self.forbidden_words.items():
            if forbidden in text:
                found.append({
                    'word': forbidden,
                    'alternative': alternatives[0] if alternatives else '(대체어 없음)'
                })
        return found

    def create_action_plan(self, analysis: Dict, keyword: str,
                          target_whole_str: str, target_pieces_str: str) -> List[str]:
        """수정해야 할 작업 목록 생성 (Python이 정확히 계산)"""
        actions = []

        # 1. 글자수 체크
        chars = analysis['chars']
        if chars < 300:
            actions.append(f"글자수 {300 - chars}자 이상 늘리기 (현재 {chars}자 → 목표 300~900자)")
        elif chars > 900:
            actions.append(f"글자수 {chars - 900}자 줄이기 (현재 {chars}자 → 목표 300~900자)")

        # 2. 첫문단 통키워드 (정확히 2회)
        첫문단_count = analysis['첫문단_통키워드']
        if 첫문단_count < 2:
            diff = 2 - 첫문단_count
            actions.append(f"첫 문단에 [{keyword}] {diff}회 더 추가 (현재 {첫문단_count}회 → 목표 정확히 2회)")
        elif 첫문단_count > 2:
            diff = 첫문단_count - 2
            actions.append(f"첫 문단에서 [{keyword}] {diff}회 제거 (현재 {첫문단_count}회 → 목표 정확히 2회)")

        # 3. 문장 시작 (최소 2개 이상)
        문장시작_count = analysis['통키워드_문장시작']
        if 문장시작_count < 2:
            diff = 2 - 문장시작_count
            actions.append(f"[{keyword}]로 시작하는 문장 {diff}개 더 추가 (현재 {문장시작_count}개 → 목표 최소 2개 이상)")

        # 4. 첫문단 키워드 사이 문장 (최소 2개)
        키워드사이_count = analysis['첫문단_키워드사이_문장수']
        if 키워드사이_count < 2:
            diff = 2 - 키워드사이_count
            actions.append(f"첫 문단에서 첫 번째와 두 번째 [{keyword}] 사이에 문장 {diff}개 더 추가 (현재 {키워드사이_count}개 → 목표 최소 2개)")

        # 5. 나머지 통키워드 (최소 이상)
        for kw, data in analysis['나머지_통키워드'].items():
            if data['actual'] < data['target']:
                diff = data['target'] - data['actual']
                actions.append(f"첫 문단 이후에 [{kw}] 최소 {diff}회 더 추가 (현재 {data['actual']}회 → 목표 최소 {data['target']}회 이상, 많아도 OK)")

        # 6. 조각키워드 (최소 이상)
        for kw, data in analysis['나머지_조각키워드'].items():
            if data['actual'] < data['target']:
                diff = data['target'] - data['actual']
                actions.append(f"첫 문단 이후에 [{kw}] 최소 {diff}회 더 추가 (현재 {data['actual']}회 → 목표 최소 {data['target']}회 이상, 많아도 OK)")

        # 7. 서브키워드 (최소 이상)
        sub_diff = analysis['subkeywords']['target'] - analysis['subkeywords']['actual']
        if sub_diff > 0:
            actions.append(f"2회 이상 반복되는 단어를 최소 {sub_diff}개 더 추가 (현재 {analysis['subkeywords']['actual']}개 → 목표 최소 {analysis['subkeywords']['target']}개 이상)")

        return actions

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
        """Gemini용 수정 프롬프트 생성 (간소화 버전)"""

        # Python이 정확히 계산한 수정 작업 목록
        actions = self.create_action_plan(analysis, keyword, target_whole_str, target_pieces_str)

        # 금칙어 체크
        forbidden_found = self.check_forbidden_words(manuscript)

        prompt = f"""블로그 원고를 아래 지시사항대로 수정하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 최우선 작업: 금칙어 치환 (절대 필수!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # 금칙어 치환 (최우선)
        if forbidden_found:
            prompt += "\n⚠️ 아래 금칙어를 반드시 대체어로 치환하세요 (100% 필수!):\n"
            for item in forbidden_found[:10]:  # 최대 10개
                prompt += f"   - '{item['word']}' → '{item['alternative']}' 로 반드시 변경\n"
            prompt += "\n"
        else:
            prompt += "✅ 금칙어 없음\n\n"

        prompt += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 키워드 및 내용 수정 ({len(actions)}개)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # 수정 작업 목록 (필수 항목 강조)
        if actions:
            prompt += "\n✅ 아래 모든 항목 필수:\n"
            for i, action in enumerate(actions, 1):
                # "문장 시작"과 "첫 문단" 관련 항목은 강조
                if "문장" in action and "시작" in action:
                    prompt += f"   ⚠️ {i}. {action} 【필수】\n"
                elif "첫 문단" in action and "추가" in action:
                    prompt += f"   ⚠️ {i}. {action} 【필수】\n"
                else:
                    prompt += f"   {i}. {action}\n"
        else:
            prompt += "✅ 키워드 개수는 충족 (유지)\n"

        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 중요 규칙 (반드시 지킬 것!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 키워드 띄어쓰기 필수!
   ❌ {keyword}에, {keyword}를, {keyword}가
   ✅ {keyword} 관련해서 (띄어쓰기!), {keyword} 정보를 (띄어쓰기!)

2. "~때문에" 사용 규칙 (중요!):
   ⚠️ "~때문에" 뒤에는 **문제/원인/고민**이 와야 함
   ❌ 나쁜 예: "{keyword} 때문에 고민입니다" (키워드가 문제가 아님!)
   ✅ 좋은 예: "무릎이 아파서 고민입니다. {keyword} 관련해서 알아보고 있어요"
   ✅ 좋은 예: "관절 통증 때문에 힘듭니다. {keyword} 정보를 찾고 있습니다"

   → 키워드는 **해결책**이므로 "~때문에"와 함께 쓰면 안 됨!
   → 대신: "~관련해서", "~정보를", "~알아보는 중", "~찾고 있습니다" 사용

3. 문장 시작 규칙:
   - 줄 맨 앞에서 [{keyword}]로 시작하는 문장 최소 2개 이상 (많아도 OK)
   - 예시: "{keyword} 관련해서 알아보고 있어요." (줄 맨 앞에서 시작)
   - 예시: "{keyword} 정보를 찾고 있는데요." (줄 맨 앞에서 시작)

4. 첫 문단 구조:
   - 첫 번째 [{keyword}]와 두 번째 [{keyword}] 사이에 최소 2문장 배치 (온점, 쉼표로 구분)
   - 예시: "{keyword} 관련해서 알아보고 있어요. 이것저것 검색해봤는데, 정보가 너무 많아서 헷갈리네요. {keyword} 사용해보신 분 계시나요?"

5. 원본 글 흐름 최대한 유지
   - 키워드만 추가/제거/위치 조정
   - 처음부터 새로 쓰지 말 것

6. 도입부: 고민이나 불편함 표현 (키워드 없이 문제 먼저 언급)
7. 마무리: 댓글 유도 또는 정보 공유 요청

8. 글의 자연스러움:
   - 키워드가 억지로 끼워 넣어진 느낌이 들면 안 됨
   - 자연스럽고 대화체처럼 편안한 문장

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 원본 원고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{manuscript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 출력 전 필수 체크! (직접 확인하세요)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 출력 전에 반드시 확인:
0. 🚫 금칙어 100% 치환 완료? (가장 중요!)
1. 첫 문단에 [{keyword} ] (띄어쓰기) 정확히 2번?
2. 줄 맨 앞에서 [{keyword}]로 시작하는 문장 최소 2개 이상?
   → 예: "{keyword} 관련해서..." (줄 시작)
   → 예: "{keyword} 정보를..." (줄 시작)
3. 첫 문단에서 첫 번째 [{keyword}]와 두 번째 [{keyword}] 사이에 최소 2문장? (온점, 쉼표 기준)
   → 예: "{keyword} 관련해서 알아보고 있어요. 이것저것 검색해봤는데, 정보가 너무 많네요. {keyword} 사용해보신 분 계시나요?"
4. 글자수 300~900자?
5. "{keyword} 때문에" 같은 부자연스러운 표현 없음?

위 항목을 모두 확인하고 맞으면 수정된 원고만 출력하세요 (설명 없이).
"""
        return prompt

    def rewrite_manuscript(self, manuscript: str, keyword: str,
                          target_whole_str: str, target_pieces_str: str,
                          target_subkeywords: int) -> Dict:
        """원고 자동 수정 (한 번만 시도)"""

        # 1. 분석
        analysis = self.analyze_manuscript(manuscript, keyword, target_whole_str,
                                          target_pieces_str, target_subkeywords)

        print(f"\n{'=' * 100}")
        print(f"원고 분석 - 키워드: {keyword}")
        print(f"{'=' * 100}")
        print(f"글자수: {analysis['chars']}자 (목표: 300~900자)")
        print(f"첫문단 통키워드: {analysis['첫문단_통키워드']}회 (목표: 2회)")
        print(f"통키워드 문장 시작: {analysis['통키워드_문장시작']}개 (목표: 최소 2개 이상)")

        print(f"\n🤖 Gemini가 원고를 수정 중...")

        try:
            # 2. 프롬프트 생성
            prompt = self.create_rewrite_prompt(manuscript, keyword, analysis,
                                               target_whole_str, target_pieces_str)

            # 3. Gemini로 수정
            response = self.model.generate_content(prompt)
            rewritten = response.text.strip()

            # 4. 수정 후 재분석
            after_analysis = self.analyze_manuscript(rewritten, keyword, target_whole_str,
                                                    target_pieces_str, target_subkeywords)

            # 5. 검증 - ALL 7개 기준을 정확히 체크
            first_para_ok = after_analysis['첫문단_통키워드'] == 2
            sentence_start_ok = after_analysis['통키워드_문장시작'] >= 2  # 2개 이상이면 OK
            키워드사이_문장수_ok = after_analysis['첫문단_키워드사이_문장수'] >= 2
            chars_ok = after_analysis['chars_in_range']

            # 나머지 통키워드 검증 (최소 이상이어야 함 - 넘어가는 건 OK)
            나머지_통키워드_ok = True
            나머지_통키워드_errors = []
            for kw, data in after_analysis['나머지_통키워드'].items():
                if data['actual'] < data['target']:
                    나머지_통키워드_ok = False
                    나머지_통키워드_errors.append(f"{kw}: {data['actual']}회 (목표: {data['target']}회 이상)")

            # 조각키워드 검증 (목표 이상이어야 함 - 넘어가는 건 OK)
            조각키워드_ok = True
            조각키워드_errors = []
            for kw, data in after_analysis['나머지_조각키워드'].items():
                if data['actual'] < data['target']:
                    조각키워드_ok = False
                    조각키워드_errors.append(f"{kw}: {data['actual']}회 (목표: {data['target']}회 이상)")

            # 서브키워드 검증 (목표 이상이어야 함)
            서브키워드_ok = after_analysis['subkeywords']['actual'] >= after_analysis['subkeywords']['target']

            # 금칙어 검증
            forbidden_found = self.check_forbidden_words(rewritten)
            금칙어_ok = len(forbidden_found) == 0

            # ALL 8개 기준이 모두 충족되어야 성공
            all_criteria_met = (first_para_ok and sentence_start_ok and 키워드사이_문장수_ok and
                               chars_ok and 나머지_통키워드_ok and 조각키워드_ok and 서브키워드_ok and 금칙어_ok)

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
            elif after_analysis['나머지_통키워드']:
                for kw, data in after_analysis['나머지_통키워드'].items():
                    print(f"     - {kw}: {data['actual']}/{data['target']}회 ✅")

            # 조각키워드 출력
            print(f"  6. 조각키워드: {'✅' if 조각키워드_ok else '❌'}")
            if not 조각키워드_ok:
                for err in 조각키워드_errors:
                    print(f"     - {err}")
            elif after_analysis['나머지_조각키워드']:
                for kw, data in after_analysis['나머지_조각키워드'].items():
                    print(f"     - {kw}: {data['actual']}/{data['target']}회 ✅")

            # 서브키워드 출력
            print(f"  7. 서브키워드 목록: {after_analysis['subkeywords']['actual']}개 (목표: {after_analysis['subkeywords']['target']}개 이상) {'✅' if 서브키워드_ok else '❌'}")

            # 금칙어 출력
            print(f"  8. 금칙어: {'✅' if 금칙어_ok else '❌'}")
            if not 금칙어_ok:
                for item in forbidden_found[:3]:  # 최대 3개만 표시
                    print(f"     - '{item['word']}' 발견 (대체: {item['alternative']})")

            # ALL 기준 충족 여부 확인
            if all_criteria_met:
                print(f"\n✅ 성공! 모든 기준 충족 (8/8)")
                return {
                    'success': True,
                    'original': manuscript,
                    'rewritten': rewritten,
                    'before_analysis': analysis,
                    'after_analysis': after_analysis
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
                    not 서브키워드_ok,
                    not 금칙어_ok
                ])
                print(f"\n⚠️ 기준 미달 ({8-failed_count}/8 충족) - 그대로 저장")

                # 실패 이유 수집
                error_messages = []
                if not first_para_ok:
                    error_messages.append(f"첫문단 통키워드 {after_analysis['첫문단_통키워드']}회 (목표: 2회)")
                if not sentence_start_ok:
                    error_messages.append(f"문장 시작 {after_analysis['통키워드_문장시작']}개 (목표: 최소 2개 이상)")
                if not 키워드사이_문장수_ok:
                    error_messages.append(f"키워드 사이 문장 {after_analysis['첫문단_키워드사이_문장수']}개 (목표: 최소 2개)")
                if not chars_ok:
                    error_messages.append(f"글자수 {after_analysis['chars']}자 (목표: 300~900자)")
                if not 나머지_통키워드_ok:
                    error_messages.extend(나머지_통키워드_errors)
                if not 조각키워드_ok:
                    error_messages.extend(조각키워드_errors)
                if not 서브키워드_ok:
                    error_messages.append(f"서브키워드 {after_analysis['subkeywords']['actual']}개 (목표: {after_analysis['subkeywords']['target']}개 이상)")
                if not 금칙어_ok:
                    forbidden_list = ', '.join([f"'{item['word']}'" for item in forbidden_found[:3]])
                    error_messages.append(f"금칙어 발견: {forbidden_list}")

                return {
                    'success': False,
                    'error': ', '.join(error_messages),
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

    def create_retry_prompt(self, original: str, keyword: str, failed_text: str,
                           failed_analysis: Dict, target_whole_str: str,
                           target_pieces_str: str) -> str:
        """재시도용 프롬프트 (간소화 버전 - 실패 이유만 강조)"""

        # Python이 정확히 계산한 수정 작업 목록
        actions = self.create_action_plan(failed_analysis, keyword, target_whole_str, target_pieces_str)

        # 금칙어 체크
        forbidden_found = self.check_forbidden_words(failed_text)

        prompt = f"""⚠️ 이전 수정이 기준 미달입니다. 다시 수정하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 이전 시도에서 부족했던 부분
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # 금칙어
        if forbidden_found:
            prompt += "\n🚫 금칙어 치환:\n"
            for item in forbidden_found[:5]:
                prompt += f"   - '{item['word']}' → '{item['alternative']}'\n"

        # 부족한 부분 (필수 항목 강조)
        if actions:
            prompt += "\n✅ 아래 사항을 정확히 수정 (⚠️ 모든 항목 필수!):\n"
            for i, action in enumerate(actions, 1):
                # "문장 시작"과 "첫 문단" 관련 항목은 강조
                if "문장" in action and "시작" in action:
                    prompt += f"   ⚠️ {i}. {action} 【절대 필수】\n"
                elif "첫 문단" in action and "추가" in action:
                    prompt += f"   ⚠️ {i}. {action} 【절대 필수】\n"
                else:
                    prompt += f"   {i}. {action}\n"

        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 이전 시도 (기준 미달)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{failed_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 중요 규칙 (재확인)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 조사 붙으면 카운팅 안 됨!
   ❌ {keyword}에, {keyword}를, {keyword}가
   ✅ {keyword} 관련해서, {keyword} 때문에 (띄어쓰기!)

2. 원본 글 흐름 유지하면서 키워드만 조정

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 원본 원고 (참고)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{original}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 출력 전 필수 체크! (직접 확인하세요)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 출력 전에 반드시 확인:
0. 🚫 금칙어 100% 치환 완료? (가장 중요!)
1. 첫 문단에 [{keyword} ] (띄어쓰기) 정확히 2번?
2. 줄 맨 앞에서 [{keyword}]로 시작하는 문장 최소 2개 이상?
   → 예: "{keyword} 관련해서..." (줄 시작)
   → 예: "{keyword} 정보를..." (줄 시작)
3. 첫 문단에서 첫 번째 [{keyword}]와 두 번째 [{keyword}] 사이에 최소 2문장? (온점, 쉼표 기준)
   → 예: "{keyword} 관련해서 알아보고 있어요. 이것저것 검색해봤는데, 정보가 너무 많네요. {keyword} 사용해보신 분 계시나요?"
4. 글자수 300~900자?
5. "{keyword} 때문에" 같은 부자연스러운 표현 없음?

위 항목을 모두 확인하고 맞으면 수정된 원고만 출력하세요 (설명 없이).
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

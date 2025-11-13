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

        # 3. 문장 시작 (정확히 2개)
        문장시작_count = analysis['통키워드_문장시작']
        if 문장시작_count < 2:
            diff = 2 - 문장시작_count
            actions.append(f"[{keyword}]로 시작하는 문장 {diff}개 더 추가 (현재 {문장시작_count}개 → 목표 정확히 2개)")
        elif 문장시작_count > 2:
            diff = 문장시작_count - 2
            actions.append(f"[{keyword}]로 시작하는 문장 {diff}개 제거 (현재 {문장시작_count}개 → 목표 정확히 2개)")

        # 4. 첫문단 키워드 사이 문장 (최소 2개)
        키워드사이_count = analysis['첫문단_키워드사이_문장수']
        if 키워드사이_count < 2:
            diff = 2 - 키워드사이_count
            actions.append(f"첫 문단에서 첫 번째와 두 번째 [{keyword}] 사이에 문장 {diff}개 더 추가 (현재 {키워드사이_count}개 → 목표 최소 2개)")

        # 5. 나머지 통키워드 (정확히 일치)
        for kw, data in analysis['나머지_통키워드'].items():
            diff = data['target'] - data['actual']
            if diff > 0:
                actions.append(f"첫 문단 이후에 [{kw}] {diff}회 더 추가 (현재 {data['actual']}회 → 목표 정확히 {data['target']}회)")
            elif diff < 0:
                actions.append(f"첫 문단 이후에서 [{kw}] {abs(diff)}회 제거 (현재 {data['actual']}회 → 목표 정확히 {data['target']}회)")

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
📋 수정 지시사항 ({len(actions) + len(forbidden_found)}개)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # 금칙어 치환
        if forbidden_found:
            prompt += "\n🚫 금칙어 치환:\n"
            for item in forbidden_found[:5]:  # 상위 5개만
                prompt += f"   - '{item['word']}' → '{item['alternative']}'\n"

        # 수정 작업 목록
        if actions:
            prompt += "\n✅ 키워드 및 내용 수정:\n"
            for i, action in enumerate(actions, 1):
                prompt += f"   {i}. {action}\n"

        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 중요 규칙
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 조사 붙으면 카운팅 안 됨!
   ❌ {keyword}에, {keyword}를, {keyword}가
   ✅ {keyword} 관련해서, {keyword} 때문에 (띄어쓰기!)

2. 원본 글 내용과 흐름 최대한 유지
   - 키워드만 추가/제거/위치 조정
   - 처음부터 새로 쓰지 말 것

3. 도입부: 고민이나 불편함 표현
4. 마무리: 댓글 유도 또는 정보 공유 요청

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 원본 원고
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{manuscript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 출력
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

수정된 원고만 출력하세요 (설명 없이).
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

                # 조각키워드 검증 (목표 이상이어야 함 - 넘어가는 건 OK)
                조각키워드_ok = True
                조각키워드_errors = []
                for kw, data in after_analysis['나머지_조각키워드'].items():
                    if data['actual'] < data['target']:
                        조각키워드_ok = False
                        조각키워드_errors.append(f"{kw}: {data['actual']}회 (목표: {data['target']}회 이상)")

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

        # 부족한 부분
        if actions:
            prompt += "\n✅ 아래 사항을 정확히 수정:\n"
            for i, action in enumerate(actions, 1):
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
✅ 출력
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

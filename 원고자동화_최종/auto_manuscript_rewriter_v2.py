#!/usr/bin/env python3
"""
개선된 원고 자동 수정 시스템 v2
- 프롬프트 극단적 단순화
- 숫자 규칙 우선 적용
"""

import os
import re
import pandas as pd
from typing import Dict, List
from collections import Counter
import google.generativeai as genai


class AutoManuscriptRewriterV2:
    """개선된 원고 자동 검수 및 수정 시스템"""

    def __init__(self, forbidden_words_file='금칙어 리스트.xlsx', gemini_api_key=None, model_choice=1):
        """초기화"""
        self.forbidden_words_file = forbidden_words_file
        self.load_forbidden_words()

        # Gemini API 설정
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY 환경변수를 설정하거나 gemini_api_key 파라미터를 전달하세요.")

        genai.configure(api_key=api_key)

        if model_choice == 2:
            model_name = 'gemini-2.0-flash-exp'
            print("🚀 모델: gemini-2.0-flash-exp")
        else:
            model_name = 'gemini-2.5-pro'
            print("🎯 모델: gemini-2.5-pro")

        self.model = genai.GenerativeModel(model_name)

    def load_forbidden_words(self):
        """금칙어 리스트 로드"""
        try:
            df = pd.read_excel(self.forbidden_words_file)
            self.forbidden_words = {}

            for idx, row in df.iterrows():
                forbidden = row.iloc[1]
                if pd.notna(forbidden) and forbidden != '금칙어':
                    alternatives = []
                    for i in range(2, len(row)):
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
        """키워드로 시작하는 문장 개수"""
        if not keyword:
            return 0

        sentences = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
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

        count = 0
        for sentence in sentences:
            if sentence.startswith(keyword):
                count += 1

        return count

    def count_sentences_between_keywords(self, paragraph: str, keyword: str) -> int:
        """첫 문단에서 키워드 사이 문장 개수"""
        if not keyword or not paragraph:
            return 0

        text = '\n'.join([line for line in paragraph.split('\n') if not line.strip().startswith('#')])
        sentences = re.split(r'[.,]\s*', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        keyword_pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'

        keyword_indices = []
        for i, sentence in enumerate(sentences):
            if re.search(keyword_pattern, sentence):
                keyword_indices.append(i)

        if len(keyword_indices) >= 2:
            return keyword_indices[1] - keyword_indices[0] - 1

        return 0

    def count_subkeywords(self, text: str, exclude_keywords: List[str] = None) -> int:
        """서브키워드 목록 수 (한글 단어 + 특수문자 반복)"""
        if exclude_keywords is None:
            exclude_keywords = []

        words = re.findall(r'[가-힣]+', text)
        # 앞뒤 띄어쓰기가 있는 특수문자 2개 이상 반복 (^^, ;;, .., ..., 등)
        # 패턴 전체를 잡음: .. 와 ... 는 별개의 서브키워드
        special_patterns = re.findall(r'(?<=\s)(([^\w\s가-힣])\2+)(?=\s)', text)
        punct_patterns = [match[0] for match in special_patterns]

        word_counter = Counter(words)
        punct_counter = Counter(punct_patterns)

        subkeywords = set()
        for word, count in word_counter.items():
            if count >= 2 and len(word) >= 2 and word not in exclude_keywords:
                subkeywords.add(word)

        # 특수문자 패턴: 2회 이상 등장하면 서브키워드로 카운트
        # 예: '..' 2회, '...' 2회 → 서브키워드 2개 (별개!)
        for pattern, count in punct_counter.items():
            if count >= 2:
                subkeywords.add(pattern)

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

    def replace_forbidden_words(self, text: str, keyword: str = None, target_pieces_str: str = None) -> str:
        """금칙어 치환 (단, 통키워드/조각키워드 안의 금칙어는 보호)"""

        # 보호할 키워드 리스트
        protected_keywords = []
        if keyword:
            protected_keywords.append(keyword)
        if target_pieces_str:
            target_pieces = self.parse_target_value(target_pieces_str)
            protected_keywords.extend(target_pieces.keys())

        # 일반 금칙어 치환 (보호 대상 제외)
        for forbidden, alternatives in self.forbidden_words.items():
            if not alternatives:
                continue

            # 이 금칙어가 보호 대상 키워드에 포함되어 있는지 확인
            is_protected = any(forbidden in pk for pk in protected_keywords)

            if not is_protected:
                # 보호 대상이 아니면 치환
                text = text.replace(forbidden, alternatives[0])

        # 특수 금칙어 변환 (보호 대상이어도 항상 변환)
        text = text.replace("네요", "내요")
        text = text.replace("하더라", "하더 라")

        return text

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

        actual_chars = len(text_no_title.replace(' ', '').replace('\n', ''))
        첫문단_통키워드 = self.count_keyword(첫문단, keyword)
        전체_통키워드_문장시작 = self.count_sentences_starting_with(text_no_title, keyword)
        첫문단_키워드사이_문장수 = self.count_sentences_between_keywords(첫문단, keyword)

        나머지_통키워드 = {}
        for kw, target in target_whole.items():
            actual = self.count_keyword(나머지, kw)
            나머지_통키워드[kw] = {'target': target, 'actual': actual}

        나머지_조각키워드 = {}
        for kw, target in target_pieces.items():
            actual = self.count_keyword(나머지, kw)
            나머지_조각키워드[kw] = {'target': target, 'actual': actual}

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

    def create_simple_prompt(self, manuscript: str, keyword: str, analysis: Dict,
                            target_whole_str: str, target_pieces_str: str) -> str:
        """극단적으로 단순화된 프롬프트 (숫자 규칙만 강조)"""

        # 필요한 수정사항만 추출
        tasks = []

        # 1. 첫문단 통키워드 (정확히 2개)
        첫문단_count = analysis['첫문단_통키워드']
        if 첫문단_count != 2:
            if 첫문단_count < 2:
                tasks.append(f"첫 문단에 [{keyword}] 를 {2 - 첫문단_count}개 더 추가하세요. (현재 {첫문단_count}개 → 목표 정확히 2개)")
            else:
                tasks.append(f"첫 문단에 [{keyword}] 를 {첫문단_count - 2}개 제거하세요. (현재 {첫문단_count}개 → 목표 정확히 2개)")

        # 2. 문장 시작 (정확히 2개)
        문장시작_count = analysis['통키워드_문장시작']
        if 문장시작_count != 2:
            if 문장시작_count < 2:
                tasks.append(f"줄 맨 앞에서 [{keyword}]로 시작하는 문장을 {2 - 문장시작_count}개 더 만드세요. (현재 {문장시작_count}개 → 목표 정확히 2개)")
            else:
                tasks.append(f"줄 맨 앞에서 [{keyword}]로 시작하는 문장을 {문장시작_count - 2}개 줄이세요. (현재 {문장시작_count}개 → 목표 정확히 2개)")

        # 3. 첫문단 키워드 사이 문장 (최소 2개)
        키워드사이 = analysis['첫문단_키워드사이_문장수']
        if 키워드사이 < 2:
            tasks.append(f"첫 문단에서 첫 번째 [{keyword}]와 두 번째 [{keyword}] 사이에 문장을 {2 - 키워드사이}개 더 추가하세요. (현재 {키워드사이}개 → 목표 최소 2개)")

        # 4. 글자수
        chars = analysis['chars']
        if chars < 300:
            tasks.append(f"글자수를 {300 - chars}자 이상 늘리세요. (현재 {chars}자 → 목표 300~900자)")
        elif chars > 900:
            tasks.append(f"글자수를 {chars - 900}자 줄이세요. (현재 {chars}자 → 목표 300~900자)")

        # 5. 나머지 통키워드 (목표~목표+1개 허용, 그 이상 초과 금지)
        for kw, data in analysis['나머지_통키워드'].items():
            if data['actual'] < data['target']:
                diff = data['target'] - data['actual']
                tasks.append(f"첫 문단 이후에 [{kw}] 를 {diff}개 추가하세요. (현재 {data['actual']}개 → 목표 {data['target']}~{data['target']+1}개)")
            elif data['actual'] > data['target'] + 1:
                diff = data['actual'] - data['target'] - 1
                tasks.append(f"첫 문단 이후에 [{kw}] 를 {diff}개 제거하세요. (현재 {data['actual']}개 → 목표 {data['target']}~{data['target']+1}개, 초과 금지)")

        # 6. 조각키워드 (목표~목표+1개 허용, 그 이상 초과 금지)
        for kw, data in analysis['나머지_조각키워드'].items():
            if data['actual'] < data['target']:
                diff = data['target'] - data['actual']
                tasks.append(f"첫 문단 이후에 [{kw}] 를 {diff}개 추가하세요. (현재 {data['actual']}개 → 목표 {data['target']}~{data['target']+1}개)")
            elif data['actual'] > data['target'] + 1:
                diff = data['actual'] - data['target'] - 1
                tasks.append(f"첫 문단 이후에 [{kw}] 를 {diff}개 제거하세요. (현재 {data['actual']}개 → 목표 {data['target']}~{data['target']+1}개, 초과 금지)")

        # 7. 서브키워드 (목표~목표+1개 허용, 그 이상 초과 금지)
        sub_diff = analysis['subkeywords']['target'] - analysis['subkeywords']['actual']
        if sub_diff > 0:
            tasks.append(f"""서브키워드를 {sub_diff}개 더 추가하세요. (현재 {analysis['subkeywords']['actual']}개 → 목표 {analysis['subkeywords']['target']}~{analysis['subkeywords']['target']+1}개)
   방법 1: 2회 이상 반복되는 한글 단어 추가 (예: "정말", "많이" 등)
   방법 2: 특수문자 반복 추가 - 문장 끝에 자연스럽게 삽입
      예: "도움이 됐으면 좋겠어요 ^^" (띄어쓰기 필수!)
      예: "궁금한 점이 많네요 .." (띄어쓰기 필수!)
      예: "정말 좋아요 ..." (띄어쓰기 필수!)
   ⚠️ 중요: ".." 와 "..." 는 별개의 서브키워드! 각각 2회씩 사용해야 함
   ⚠️ 특수문자는 반드시 앞뒤로 띄어쓰기!""")
        elif analysis['subkeywords']['actual'] > analysis['subkeywords']['target'] + 1:
            sub_excess = analysis['subkeywords']['actual'] - analysis['subkeywords']['target'] - 1
            tasks.append(f"반복 단어를 {sub_excess}개 제거하세요. (현재 {analysis['subkeywords']['actual']}개 → 목표 {analysis['subkeywords']['target']}~{analysis['subkeywords']['target']+1}개, 초과 금지)")

        # 프롬프트 생성
        prompt = f"""블로그 원고를 수정하세요.

【최우선 규칙】
1. 키워드는 반드시 띄어쓰기로 분리: [{keyword} ] (공백 필수!)
   ❌ 나쁜 예: {keyword}를, {keyword}에
   ✅ 좋은 예: {keyword} 관련, {keyword} 정보

2. 아래 작업을 정확한 개수로 수행:

"""

        if tasks:
            for i, task in enumerate(tasks, 1):
                prompt += f"   {i}. {task}\n"
        else:
            prompt += "   ✅ 모든 규칙이 이미 충족되어 있습니다. 원고를 그대로 출력하세요.\n"

        prompt += f"""
【원본 원고】
{manuscript}

【출력 규칙】
- 수정된 원고만 출력 (설명 없이)
- 제목(# 시작)은 제거하지 말 것
- 위 작업을 모두 정확히 수행했는지 확인 후 출력
"""

        return prompt

    def rewrite_manuscript(self, manuscript: str, keyword: str,
                          target_whole_str: str, target_pieces_str: str,
                          target_subkeywords: int, max_retries: int = 3) -> Dict:
        """원고 자동 수정 (여러 번 재시도)"""

        for attempt in range(1, max_retries + 1):
            print(f"\n{'=' * 100}")
            print(f"{'🔄 재시도 ' + str(attempt) if attempt > 1 else '🤖 1차 시도'}")
            print(f"{'=' * 100}")

            # 분석
            analysis = self.analyze_manuscript(manuscript, keyword, target_whole_str,
                                              target_pieces_str, target_subkeywords)

            print(f"현재 상태:")
            print(f"  - 글자수: {analysis['chars']}자")
            print(f"  - 첫문단 통키워드: {analysis['첫문단_통키워드']}회 (목표: 2회)")
            print(f"  - 문장 시작: {analysis['통키워드_문장시작']}개 (목표: 2개)")
            print(f"  - 키워드 사이 문장: {analysis['첫문단_키워드사이_문장수']}개 (목표: 2개 이상)")

            # 프롬프트 생성
            prompt = self.create_simple_prompt(manuscript, keyword, analysis,
                                              target_whole_str, target_pieces_str)

            try:
                # Gemini로 수정
                response = self.model.generate_content(prompt)
                rewritten = response.text.strip()

                # 수정 후 재분석
                after_analysis = self.analyze_manuscript(rewritten, keyword, target_whole_str,
                                                        target_pieces_str, target_subkeywords)

                # 검증 (목표~목표+1 범위 허용, 초과 금지!)
                all_ok = (
                    after_analysis['첫문단_통키워드'] == 2 and
                    after_analysis['통키워드_문장시작'] == 2 and
                    after_analysis['첫문단_키워드사이_문장수'] >= 2 and
                    after_analysis['chars_in_range'] and
                    all(d['target'] <= d['actual'] <= d['target'] + 1 for d in after_analysis['나머지_통키워드'].values()) and
                    all(d['target'] <= d['actual'] <= d['target'] + 1 for d in after_analysis['나머지_조각키워드'].values()) and
                    after_analysis['subkeywords']['target'] <= after_analysis['subkeywords']['actual'] <= after_analysis['subkeywords']['target'] + 1
                )

                print(f"\n검증 결과:")
                print(f"  - 글자수: {after_analysis['chars']}자 {'✅' if after_analysis['chars_in_range'] else '❌'}")
                print(f"  - 첫문단 통키워드: {after_analysis['첫문단_통키워드']}회 {'✅' if after_analysis['첫문단_통키워드'] == 2 else '❌'}")
                print(f"  - 문장 시작: {after_analysis['통키워드_문장시작']}개 {'✅' if after_analysis['통키워드_문장시작'] == 2 else '❌'}")
                print(f"  - 키워드 사이 문장: {after_analysis['첫문단_키워드사이_문장수']}개 {'✅' if after_analysis['첫문단_키워드사이_문장수'] >= 2 else '❌'}")

                if all_ok:
                    print(f"\n✅ 성공! (시도 {attempt}회)")
                    # 마지막에 금칙어 치환 (통키워드/조각키워드는 보호)
                    final_output = self.replace_forbidden_words(rewritten, keyword, target_pieces_str)
                    return {
                        'success': True,
                        'original': manuscript,
                        'rewritten': final_output,
                        'before_analysis': analysis,
                        'after_analysis': after_analysis,
                        'attempts': attempt
                    }
                else:
                    print(f"\n⚠️ 기준 미달 (시도 {attempt}/{max_retries})")
                    manuscript = rewritten  # 다음 시도를 위해 현재 결과 사용

            except Exception as e:
                print(f"❌ 오류: {e}")
                continue

        # 최종 실패 - 그래도 금칙어는 치환 (통키워드/조각키워드는 보호)
        final_rewritten = rewritten if 'rewritten' in locals() else manuscript
        final_output = self.replace_forbidden_words(final_rewritten, keyword, target_pieces_str)
        return {
            'success': False,
            'error': f'{max_retries}회 시도 후에도 기준 미달',
            'original': manuscript,
            'rewritten': final_output,
            'before_analysis': analysis,
            'after_analysis': after_analysis if 'after_analysis' in locals() else analysis,
            'attempts': max_retries
        }

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

        # 2. 첫문단 통키워드 (2회 이상, 3회도 OK)
        첫문단_count = analysis['첫문단_통키워드']
        if 첫문단_count < 2:
            diff = 2 - 첫문단_count
            actions.append(f"첫 문단에 [{keyword}] {diff}회 더 추가 (현재 {첫문단_count}회 → 목표 2회 이상)")

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

        # 5. 나머지 통키워드 (목표~목표+1개 허용, 그 이상 초과 금지)
        for kw, data in analysis['나머지_통키워드'].items():
            if data['actual'] < data['target']:
                diff = data['target'] - data['actual']
                actions.append(f"첫 문단 이후에 [{kw}] {diff}회 더 추가 (현재 {data['actual']}회 → 목표 {data['target']}~{data['target']+1}회)")
            elif data['actual'] > data['target'] + 1:
                diff = data['actual'] - data['target'] - 1
                actions.append(f"첫 문단 이후에 [{kw}] {diff}회 제거 (현재 {data['actual']}회 → 목표 {data['target']}~{data['target']+1}회, 초과 금지)")

        # 6. 조각키워드 (목표~목표+1개 허용, 그 이상 초과 금지)
        for kw, data in analysis['나머지_조각키워드'].items():
            if data['actual'] < data['target']:
                diff = data['target'] - data['actual']
                actions.append(f"첫 문단 이후에 [{kw}] {diff}회 더 추가 (현재 {data['actual']}회 → 목표 {data['target']}~{data['target']+1}회)")
            elif data['actual'] > data['target'] + 1:
                diff = data['actual'] - data['target'] - 1
                actions.append(f"첫 문단 이후에 [{kw}] {diff}회 제거 (현재 {data['actual']}회 → 목표 {data['target']}~{data['target']+1}회, 초과 금지)")

        # 7. 서브키워드 (목표~목표+1개 허용, 그 이상 초과 금지)
        sub_diff = analysis['subkeywords']['target'] - analysis['subkeywords']['actual']
        if sub_diff > 0:
            actions.append(f"""서브키워드 {sub_diff}개 더 추가 (현재 {analysis['subkeywords']['actual']}개 → 목표 {analysis['subkeywords']['target']}~{analysis['subkeywords']['target']+1}개)
   방법 1: 2회 이상 반복되는 한글 단어 (예: "정말", "많이")
   방법 2: 특수문자 반복 - 문장 끝에 삽입
      예: "좋겠어요 ^^", "많네요 ..", "좋아요 ..."
   ⚠️ 중요: ".." 와 "..." 는 별개의 서브키워드! 각각 2회씩 사용
   ⚠️ 특수문자는 반드시 앞뒤로 띄어쓰기!""")
        elif analysis['subkeywords']['actual'] > analysis['subkeywords']['target'] + 1:
            sub_excess = analysis['subkeywords']['actual'] - analysis['subkeywords']['target'] - 1
            actions.append(f"반복 단어를 {sub_excess}개 제거 (현재 {analysis['subkeywords']['actual']}개 → 목표 {analysis['subkeywords']['target']}~{analysis['subkeywords']['target']+1}개, 초과 금지)")

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

        # 키워드 관련 작업과 기타 작업 분리
        keyword_actions = [a for a in actions if '[' in a and ']' in a]
        other_actions = [a for a in actions if '[' not in a and ']' not in a]


        prompt = f"""블로그 원고를 아래 지시사항대로 수정하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 최우선 목표: 키워드 개수 맞추기 (절대 필수!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        if keyword_actions:
            prompt += "\n⚠️ 아래 키워드 개수를 정확히 맞춰주세요. (하나라도 틀리면 안 됩니다!)\n"
            for action in keyword_actions:
                prompt += f"   - {action}\n"
            prompt += "\n"
        else:
            prompt += "✅ 키워드 개수는 이미 충족. 그대로 유지하세요.\n\n"


        prompt += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 다음 목표: 금칙어 치환 (필수!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # 금칙어 치환 (최우선)
        if forbidden_found:
            prompt += "\n⚠️ 아래 금칙어를 반드시 대체어로 치환하세요 (100% 필수! 문법이나 자연스러움보다 이 규칙이 우선입니다):\n"
            for item in forbidden_found[:10]:  # 최대 10개
                prompt += f"   - '{item['word']}' → '{item['alternative']}' 로 예외 없이 기계적으로 치환하세요.\n"
            prompt += "\n"
        else:
            prompt += "✅ 금칙어 없음\n\n"

        prompt += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 나머지 내용 수정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        if other_actions:
            prompt += "\n✅ 아래 항목을 수정하세요:\n"
            for i, action in enumerate(other_actions, 1):
                prompt += f"   {i}. {action}\n"
        else:
            prompt += "✅ 추가 내용 수정 없음\n"


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
   - 첫 번째 [{keyword}]와 두 번째 [{keyword}] 사이에 최소 2문장 이상 배치 (온점, 쉼표로 구분)
   - 예시: "{keyword} 관련해서 알아보고 있어요. 이것저것 검색해봤는데요. {keyword} 사용해보신 분 계시나요?"

5. 원본 글 흐름 최대한 유지
   - 키워드만 추가/제거/위치 조정
   - 처음부터 새로 쓰지 말 것

6. 글 구조 템플릿 (필수!):
   ⚠️ 아래 플로우를 반드시 따를 것:

   [도입부] 신체적 불편함/고민 표현 (키워드 없이!)
   → 예: "무릎이 아프기 시작한 게 벌써 몇 달째예요."
   → 예: "50대 중반 넘어가니까 관절이 점점 안 좋아지네요."

   [중간부] 키워드 언급하며 정보 찾는 중임을 표현
   → 예: "{keyword} 관련해서 알아보고 있는데요."
   → 예: "{keyword} 정보를 찾아봤는데 너무 많아서 헷갈리네요."

   [마무리] 정보 공유 요청 (필수! 제품 홍보는 댓글에서만!)
   → 예: "사용해보신 분들 계시면 정보 공유 부탁드려요."
   → 예: "경험 있으신 분들 댓글로 알려주시면 감사하겠습니다."
   → 예: "혹시 아시는 분 계시면 댓글 남겨주세요."

7. 글의 자연스러움 (매우 중요!):
   - 키워드가 억지로 끼워 넣어진 느낌이 들면 안 됨
   - 자연스럽고 대화체처럼 편안한 문장
   - 실제로 커뮤니티에 질문하는 것처럼 작성
   - 템플릿 느낌이 나더라도 자연스러워야 함

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
6. 글 구조 확인:
   → 도입부: 불편함/고민 먼저 언급?
   → 마무리: 정보 공유/댓글 요청 있음?

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
            first_para_ok = after_analysis['첫문단_통키워드'] >= 2  # 2회 이상이면 OK (3회도 괜찮음)
            sentence_start_ok = after_analysis['통키워드_문장시작'] >= 2  # 2개 이상이면 OK
            키워드사이_문장수_ok = after_analysis['첫문단_키워드사이_문장수'] >= 2  # 최소 2개 (1개는 ❌)
            chars_ok = after_analysis['chars_in_range']

            # 나머지 통키워드 검증 (목표~목표+1 허용, 초과 금지)
            나머지_통키워드_ok = True
            나머지_통키워드_errors = []
            for kw, data in after_analysis['나머지_통키워드'].items():
                if not (data['target'] <= data['actual'] <= data['target'] + 1):
                    나머지_통키워드_ok = False
                    나머지_통키워드_errors.append(f"{kw}: {data['actual']}회 (목표: {data['target']}~{data['target']+1}회)")

            # 조각키워드 검증 (목표~목표+1 허용, 초과 금지)
            조각키워드_ok = True
            조각키워드_errors = []
            for kw, data in after_analysis['나머지_조각키워드'].items():
                if not (data['target'] <= data['actual'] <= data['target'] + 1):
                    조각키워드_ok = False
                    조각키워드_errors.append(f"{kw}: {data['actual']}회 (목표: {data['target']}~{data['target']+1}회)")

            # 서브키워드 검증 (목표~목표+1 허용, 초과 금지)
            서브키워드_ok = after_analysis['subkeywords']['target'] <= after_analysis['subkeywords']['actual'] <= after_analysis['subkeywords']['target'] + 1

            # ALL 7개 기준이 모두 충족되어야 성공 (금칙어는 마지막에 자동 치환)
            all_criteria_met = (first_para_ok and sentence_start_ok and 키워드사이_문장수_ok and
                               chars_ok and 나머지_통키워드_ok and 조각키워드_ok and 서브키워드_ok)

            print(f"\n{'=' * 100}")
            print(f"1차 시도 검증 결과:")
            print(f"  1. 글자수: {after_analysis['chars']}자 {'✅' if chars_ok else '❌'}")
            print(f"  2. 첫문단 통키워드: {after_analysis['첫문단_통키워드']}회 (목표: 2회 이상) {'✅' if first_para_ok else '❌'}")
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

            # ALL 기준 충족 여부 확인
            if all_criteria_met:
                print(f"\n✅ 1차 시도 성공! 모든 기준 충족 (7/7)")
                # 마지막에 금칙어 치환 (통키워드/조각키워드는 보호)
                final_output = self.replace_forbidden_words(rewritten, keyword, target_pieces_str)
                return {
                    'success': True,
                    'original': manuscript,
                    'rewritten': final_output,
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
                    not 서브키워드_ok
                ])
                print(f"\n⚠️ 1차 시도 기준 미달 ({7-failed_count}/7 충족) - 2차 재시도 시작...")

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # 2차 재시도
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                print(f"\n{'=' * 100}")
                print(f"🔄 2차 재시도 중...")
                print(f"{'=' * 100}")

                # 재시도 프롬프트 생성
                retry_prompt = self.create_retry_prompt(
                    manuscript, keyword, rewritten, after_analysis,
                    target_whole_str, target_pieces_str
                )

                # 2차 시도
                retry_response = self.model.generate_content(retry_prompt)
                rewritten_retry = retry_response.text.strip()

                # 2차 수정 후 재분석
                after_analysis_retry = self.analyze_manuscript(
                    rewritten_retry, keyword, target_whole_str,
                    target_pieces_str, target_subkeywords
                )

                # 2차 검증
                first_para_ok_retry = after_analysis_retry['첫문단_통키워드'] >= 2
                sentence_start_ok_retry = after_analysis_retry['통키워드_문장시작'] >= 2
                키워드사이_문장수_ok_retry = after_analysis_retry['첫문단_키워드사이_문장수'] >= 2
                chars_ok_retry = after_analysis_retry['chars_in_range']

                나머지_통키워드_ok_retry = True
                나머지_통키워드_errors_retry = []
                for kw, data in after_analysis_retry['나머지_통키워드'].items():
                    if not (data['target'] <= data['actual'] <= data['target'] + 1):
                        나머지_통키워드_ok_retry = False
                        나머지_통키워드_errors_retry.append(f"{kw}: {data['actual']}회 (목표: {data['target']}~{data['target']+1}회)")

                조각키워드_ok_retry = True
                조각키워드_errors_retry = []
                for kw, data in after_analysis_retry['나머지_조각키워드'].items():
                    if not (data['target'] <= data['actual'] <= data['target'] + 1):
                        조각키워드_ok_retry = False
                        조각키워드_errors_retry.append(f"{kw}: {data['actual']}회 (목표: {data['target']}~{data['target']+1}회)")

                서브키워드_ok_retry = after_analysis_retry['subkeywords']['target'] <= after_analysis_retry['subkeywords']['actual'] <= after_analysis_retry['subkeywords']['target'] + 1

                all_criteria_met_retry = (
                    first_para_ok_retry and sentence_start_ok_retry and 키워드사이_문장수_ok_retry and
                    chars_ok_retry and 나머지_통키워드_ok_retry and 조각키워드_ok_retry and
                    서브키워드_ok_retry
                )

                # 2차 검증 결과 출력
                print(f"\n{'=' * 100}")
                print(f"2차 시도 검증 결과:")
                print(f"  1. 글자수: {after_analysis_retry['chars']}자 {'✅' if chars_ok_retry else '❌'}")
                print(f"  2. 첫문단 통키워드: {after_analysis_retry['첫문단_통키워드']}회 {'✅' if first_para_ok_retry else '❌'}")
                print(f"  3. 통키워드 문장 시작: {after_analysis_retry['통키워드_문장시작']}개 {'✅' if sentence_start_ok_retry else '❌'}")
                print(f"  4. 첫문단 키워드 사이 문장: {after_analysis_retry['첫문단_키워드사이_문장수']}개 (최소 2개) {'✅' if 키워드사이_문장수_ok_retry else '❌'}")
                print(f"  5. 나머지 통키워드: {'✅' if 나머지_통키워드_ok_retry else '❌'}")
                if not 나머지_통키워드_ok_retry:
                    for err in 나머지_통키워드_errors_retry:
                        print(f"     - {err}")
                print(f"  6. 조각키워드: {'✅' if 조각키워드_ok_retry else '❌'}")
                if not 조각키워드_ok_retry:
                    for err in 조각키워드_errors_retry:
                        print(f"     - {err}")
                print(f"  7. 서브키워드 목록: {after_analysis_retry['subkeywords']['actual']}개 (목표: {after_analysis_retry['subkeywords']['target']}개 이상) {'✅' if 서브키워드_ok_retry else '❌'}")

                if all_criteria_met_retry:
                    print(f"\n✅ 2차 시도 성공! 모든 기준 충족 (7/7)")
                    # 마지막에 금칙어 치환 (통키워드/조각키워드는 보호)
                    final_output_retry = self.replace_forbidden_words(rewritten_retry, keyword, target_pieces_str)
                    return {
                        'success': True,
                        'original': manuscript,
                        'rewritten': final_output_retry,
                        'before_analysis': analysis,
                        'after_analysis': after_analysis_retry
                    }
                else:
                    failed_count_retry = sum([
                        not chars_ok_retry,
                        not first_para_ok_retry,
                        not sentence_start_ok_retry,
                        not 키워드사이_문장수_ok_retry,
                        not 나머지_통키워드_ok_retry,
                        not 조각키워드_ok_retry,
                        not 서브키워드_ok_retry
                    ])
                    print(f"\n⚠️ 2차 시도도 기준 미달 ({7-failed_count_retry}/7 충족) - 그대로 저장")

                    # 2차 실패 이유 수집
                    error_messages_retry = []
                    if not first_para_ok_retry:
                        error_messages_retry.append(f"첫문단 통키워드 {after_analysis_retry['첫문단_통키워드']}회 (목표: 2회 이상)")
                    if not sentence_start_ok_retry:
                        error_messages_retry.append(f"문장 시작 {after_analysis_retry['통키워드_문장시작']}개 (목표: 최소 2개 이상)")
                    if not 키워드사이_문장수_ok_retry:
                        error_messages_retry.append(f"키워드 사이 문장 {after_analysis_retry['첫문단_키워드사이_문장수']}개 (목표: 최소 2개)")
                    if not chars_ok_retry:
                        error_messages_retry.append(f"글자수 {after_analysis_retry['chars']}자 (목표: 300~900자)")
                    if not 나머지_통키워드_ok_retry:
                        error_messages_retry.extend(나머지_통키워드_errors_retry)
                    if not 조각키워드_ok_retry:
                        error_messages_retry.extend(조각키워드_errors_retry)
                    if not 서브키워드_ok_retry:
                        error_messages_retry.append(f"서브키워드 {after_analysis_retry['subkeywords']['actual']}개 (목표: {after_analysis_retry['subkeywords']['target']}개 이상)")

                    # 실패해도 금칙어는 치환 (통키워드/조각키워드는 보호)
                    final_output_fail = self.replace_forbidden_words(rewritten_retry, keyword, target_pieces_str)
                    return {
                        'success': False,
                        'error': ', '.join(error_messages_retry),
                        'original': manuscript,
                        'rewritten': final_output_fail,
                        'before_analysis': analysis,
                        'after_analysis': after_analysis_retry
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
   ✅ {keyword} 관련해서 (띄어쓰기!), {keyword} 정보를 (띄어쓰기!)

2. "~때문에" 사용 금지!
   ❌ "{keyword} 때문에 고민" (키워드가 문제가 아님!)
   ✅ "무릎이 아파서 고민. {keyword} 관련해서 알아보는 중"

3. 글 구조 (필수!):
   [도입부] 불편함/고민 → [중간부] 키워드 언급 → [마무리] 정보 공유 요청

4. 원본 글 흐름 유지하면서 키워드만 조정

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
6. 글 구조 확인:
   → 도입부: 불편함/고민 먼저 언급?
   → 마무리: 정보 공유/댓글 요청 있음?

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

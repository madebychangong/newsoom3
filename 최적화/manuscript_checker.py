#!/usr/bin/env python3
"""
원고 검수 시스템
- 회사 기준에 맞춰 원고 검증
- 부족한 부분을 명확히 표시
"""

import pandas as pd
import re
from collections import Counter
from typing import Dict, List, Tuple


class ManuscriptChecker:
    """원고 검수 클래스"""

    def __init__(self, forbidden_words_file='금칙어 리스트.xlsx'):
        """초기화"""
        self.forbidden_words_file = forbidden_words_file
        # 금칙어 로드는 나중에 구현

    def get_first_paragraph(self, text: str) -> str:
        """첫 문단 추출 (빈 줄로 구분)"""
        if not text:
            return ""

        # 제목 제거
        lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
        text_no_title = '\n'.join(lines)

        # 첫 문단 (빈 줄 전까지)
        paragraphs = text_no_title.split('\n\n')
        if paragraphs:
            return paragraphs[0].strip()
        return text_no_title.strip()

    def get_rest_paragraphs(self, text: str) -> str:
        """첫 문단 제외한 나머지"""
        if not text:
            return ""

        lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
        text_no_title = '\n'.join(lines)

        paragraphs = text_no_title.split('\n\n')
        if len(paragraphs) > 1:
            return '\n\n'.join(paragraphs[1:]).strip()
        return ""

    def count_keyword(self, text: str, keyword: str) -> int:
        """
        키워드 카운팅 (띄어쓰기 기준)

        키워드 뒤에 조사가 바로 붙으면 카운팅 X
        키워드 뒤에 공백, 문장부호, 줄바꿈이 오면 카운팅 O

        예:
        - "강남 맛집 추천을" → 카운팅 X (조사 '을' 붙음)
        - "강남 맛집 추천 리스트" → 카운팅 O (공백)
        - "강남 맛집 추천." → 카운팅 O (문장부호)
        """
        if not keyword or pd.isna(keyword):
            return 0

        # 정규식: 키워드 뒤에 한글이 아닌 것
        # (공백, 문장부호, 줄바꿈, 문장 끝)
        pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
        matches = re.findall(pattern, text)
        return len(matches)

    def count_chars(self, text: str) -> int:
        """글자수 카운팅 (공백/줄바꿈 제외)"""
        return len(text.replace(' ', '').replace('\n', ''))

    def count_subkeywords(self, text: str, exclude_keywords: List[str] = None) -> int:
        """
        서브키워드 목록 수 계산
        - 2번 이상 등장하는 단어의 개수
        - 중복 문장부호도 카운팅 (??, ;;, ... 등)
        """
        if exclude_keywords is None:
            exclude_keywords = []

        # 한글 단어 추출
        words = re.findall(r'[가-힣]+', text)

        # 중복 문장부호 추출
        punctuations = re.findall(r'([^\w\s가-힣])\1+', text)

        # 단어 빈도 계산
        word_counter = Counter(words)
        punct_counter = Counter(punctuations)

        # 2번 이상 등장하는 단어
        subkeywords = set()
        for word, count in word_counter.items():
            if count >= 2 and len(word) >= 2 and word not in exclude_keywords:
                subkeywords.add(word)

        # 2번 이상 등장하는 문장부호
        for punct, count in punct_counter.items():
            if count >= 2:
                subkeywords.add(punct * 2)

        return len(subkeywords)

    def parse_target_value(self, value_str) -> Dict[str, int]:
        """
        D, E열의 목표값 파싱
        예: "팔꿈치 쿠션 보호대 : 0" → {"팔꿈치 쿠션 보호대": 0}
        """
        if pd.isna(value_str) or value_str == '-':
            return {}

        result = {}
        lines = str(value_str).split('\n')

        for line in lines:
            if ':' in line:
                parts = line.split(':')
                keyword = parts[0].strip()
                count = int(parts[1].strip())
                result[keyword] = count

        return result

    def check_manuscript(
        self,
        manuscript: str,
        keyword: str,
        target_chars: int,
        target_whole_str: str,
        target_pieces_str: str,
        target_subkeywords: int
    ) -> Dict:
        """
        원고 검수

        Args:
            manuscript: 검수할 원고
            keyword: 통 키워드
            target_chars: 목표 글자수
            target_whole_str: 통키워드 목표 (D열 값)
            target_pieces_str: 조각키워드 목표 (E열 값)
            target_subkeywords: 서브키워드 목표 (F열 값)

        Returns:
            검수 결과 딕셔너리
        """
        # 제목 제거
        text_no_title = '\n'.join([line for line in manuscript.split('\n')
                                   if not line.strip().startswith('#')])

        # 첫 문단과 나머지 분리
        첫문단 = self.get_first_paragraph(manuscript)
        나머지 = self.get_rest_paragraphs(manuscript)

        # 목표값 파싱
        target_whole = self.parse_target_value(target_whole_str)
        target_pieces = self.parse_target_value(target_pieces_str)

        result = {
            'errors': [],
            'warnings': [],
            'details': {}
        }

        # 1. 글자수 검사
        actual_chars = self.count_chars(text_no_title)
        char_diff = actual_chars - target_chars

        result['details']['글자수'] = {
            '목표': target_chars,
            '실제': actual_chars,
            '차이': char_diff
        }

        if char_diff != 0:
            result['errors'].append(f"글자수: {char_diff:+d}자 {'필요' if char_diff < 0 else '초과'}")

        # 2. 첫 문단 통키워드 검사 (무조건 2회)
        첫문단_통키워드 = self.count_keyword(첫문단, keyword)

        result['details']['첫문단_통키워드'] = {
            '목표': 2,
            '실제': 첫문단_통키워드,
            '차이': 첫문단_통키워드 - 2
        }

        if 첫문단_통키워드 != 2:
            result['errors'].append(
                f"첫 문단에 통키워드가 {첫문단_통키워드}개 입니다. "
                f"정확히 2개를 사용해야합니다."
            )

        # 3. 나머지 부분 통키워드 검사
        if target_whole:
            for kw, target_count in target_whole.items():
                actual_count = self.count_keyword(나머지, kw)
                diff = target_count - actual_count

                result['details'][f'통키워드_{kw}'] = {
                    '목표': target_count,
                    '실제': actual_count,
                    '차이': diff
                }

                if diff != 0:
                    result['errors'].append(
                        f"통키워드 '{kw}': {abs(diff):+d} {'필요' if diff > 0 else '제거'}"
                    )

        # 4. 나머지 부분 조각키워드 검사
        if target_pieces:
            조각키워드_errors = []
            for kw, target_count in target_pieces.items():
                actual_count = self.count_keyword(나머지, kw)
                diff = target_count - actual_count

                result['details'][f'조각키워드_{kw}'] = {
                    '목표': target_count,
                    '실제': actual_count,
                    '차이': diff
                }

                if diff != 0:
                    조각키워드_errors.append(
                        f"{kw} {abs(diff):+d} {'필요' if diff > 0 else '제거'}"
                    )

            if 조각키워드_errors:
                result['errors'].append(f"조각키워드: {', '.join(조각키워드_errors)}")

        # 5. 서브키워드 검사
        exclude_list = [keyword] if keyword else []
        if target_pieces:
            exclude_list.extend(target_pieces.keys())

        actual_subkeywords = self.count_subkeywords(text_no_title, exclude_list)
        subkeyword_diff = target_subkeywords - actual_subkeywords

        result['details']['서브키워드'] = {
            '목표': target_subkeywords,
            '실제': actual_subkeywords,
            '차이': subkeyword_diff
        }

        if subkeyword_diff != 0:
            result['warnings'].append(
                f"서브키워드: {abs(subkeyword_diff):+d}개 {'필요' if subkeyword_diff > 0 else '초과'}"
            )

        return result

    def print_result(self, result: Dict, keyword: str):
        """검수 결과 출력"""
        print(f"\n{'=' * 80}")
        print(f"원고 검수 결과 - 키워드: {keyword}")
        print(f"{'=' * 80}")

        if not result['errors'] and not result['warnings']:
            print("✅ 모든 기준 충족!")
            return

        if result['errors']:
            print("\n❌ 오류 (반드시 수정 필요):")
            for error in result['errors']:
                print(f"  - {error}")

        if result['warnings']:
            print("\n⚠️  경고:")
            for warning in result['warnings']:
                print(f"  - {warning}")

        print(f"\n{'=' * 80}")


def test_checker():
    """테스트"""
    checker = ManuscriptChecker()

    # 엑셀 읽기
    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    # 8행(관절에 좋은 차) 테스트
    row = after_df.iloc[6]  # 7번째 행 (0-indexed)

    keyword = row['키워드']
    manuscript = row['원고']
    target_chars = row['글자수']
    target_whole = row['통키워드 반복수']
    target_pieces = row['조각키워드 반복수']
    target_subkeywords = row['서브키워드 목록 수']

    result = checker.check_manuscript(
        manuscript,
        keyword,
        target_chars,
        target_whole,
        target_pieces,
        target_subkeywords
    )

    checker.print_result(result, keyword)

    # 상세 정보 출력
    print("\n상세 정보:")
    for key, value in result['details'].items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    test_checker()

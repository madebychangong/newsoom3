#!/usr/bin/env python3
"""
금칙어 리스트.xlsx 로더
- 조사 결합 형태 우선 처리
- 여러 대체어 중 랜덤 선택
- 긴 패턴부터 치환
"""

import pandas as pd
import random
from typing import Dict, List, Tuple


class ForbiddenWordsLoader:
    """금칙어 리스트 로더"""

    def __init__(self, excel_path: str = '금칙어 리스트.xlsx'):
        self.excel_path = excel_path
        self.forbidden_dict = {}
        self.load_forbidden_words()

    def load_forbidden_words(self):
        """금칙어 리스트.xlsx 읽기"""
        try:
            df = pd.read_excel(self.excel_path, engine='openpyxl')

            # 첫 번째 행은 헤더이므로 스킵
            for idx in range(1, len(df)):
                row = df.iloc[idx]

                # 금칙어 추출 (Unnamed: 1 컬럼)
                forbidden = row['Unnamed: 1']

                if pd.isna(forbidden) or forbidden == '':
                    continue

                # 대체어 추출 (Unnamed: 2부터)
                replacements = []
                for col in df.columns[2:]:
                    val = row[col]
                    if pd.notna(val) and val != '':
                        replacements.append(str(val).strip())

                # 금칙어와 대체어 저장
                if replacements:
                    self.forbidden_dict[str(forbidden).strip()] = replacements

            print(f"✅ 금칙어 {len(self.forbidden_dict)}개 로드됨")

        except Exception as e:
            print(f"❌ 금칙어 리스트 로드 실패: {e}")
            self.forbidden_dict = {}

    def get_sorted_forbidden_words(self) -> List[Tuple[str, List[str]]]:
        """
        금칙어를 길이 순으로 정렬 (긴 것부터)

        예: "광고가" (3글자) → "광고" (2글자)
        """
        items = list(self.forbidden_dict.items())
        # 금칙어 길이 기준 내림차순 정렬
        items.sort(key=lambda x: len(x[0]), reverse=True)
        return items

    def replace_forbidden_words(self, text: str) -> Tuple[str, List[str]]:
        """
        금칙어 치환

        Returns:
            (치환된 텍스트, 변경 내역 리스트)
        """
        if not text:
            return text, []

        modified_text = text
        changes = []

        # 긴 패턴부터 처리
        for forbidden, replacements in self.get_sorted_forbidden_words():
            if forbidden in modified_text:
                # 대체어 중 랜덤 선택
                replacement = random.choice(replacements)

                # 치환
                count = modified_text.count(forbidden)
                modified_text = modified_text.replace(forbidden, replacement)

                changes.append(f"{forbidden} → {replacement} ({count}회)")

        return modified_text, changes


def test_loader():
    """테스트"""
    print("=" * 80)
    print("금칙어 로더 테스트")
    print("=" * 80)

    loader = ForbiddenWordsLoader('/home/user/blogm/금칙어 리스트.xlsx')

    # 정렬된 금칙어 확인
    print("\n첫 20개 금칙어 (긴 것부터):")
    for forbidden, replacements in loader.get_sorted_forbidden_words()[:20]:
        print(f"  '{forbidden}' ({len(forbidden)}글자) → {replacements[:3]}")

    # 테스트 문장
    print("\n" + "=" * 80)
    print("테스트 치환")
    print("=" * 80)

    test_texts = [
        "정말 좋네요. 광고가 많아서 불편해요.",
        "병원에서 진단 받았어요. 효과가 좋더라구요.",
        "가격이 비싸네요. 구매하기 망설여져요.",
        "광고는 싫지만 이건 좋네요.",
    ]

    for text in test_texts:
        result, changes = loader.replace_forbidden_words(text)
        print(f"\n원본: {text}")
        print(f"결과: {result}")
        if changes:
            print(f"변경: {', '.join(changes)}")


if __name__ == '__main__':
    test_loader()

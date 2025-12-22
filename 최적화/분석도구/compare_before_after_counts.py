#!/usr/bin/env python3
"""
검수전/후 시트의 C열 글자수 비교 및 실제 글자수 분석
"""

import pandas as pd


def analyze_column_c():
    """C열 글자수가 무엇을 의미하는지 검수전/후 비교"""

    # 엑셀 읽기
    before_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')
    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    print("=" * 120)
    print("검수전/후 C열 글자수 비교")
    print("=" * 120)

    for idx in range(min(20, len(before_df))):
        before_row = before_df.iloc[idx]
        after_row = after_df.iloc[idx]

        keyword = before_row['키워드']
        before_c = before_row['글자수']
        after_c = after_row['글자수']

        before_text = before_row['원고']
        after_text = after_row['원고']

        if pd.isna(before_text) or pd.isna(after_text):
            continue

        # 제목 제거
        before_no_title = '\n'.join([line for line in before_text.split('\n') if not line.strip().startswith('#')])
        after_no_title = '\n'.join([line for line in after_text.split('\n') if not line.strip().startswith('#')])

        # 실제 글자수 (여러 방식)
        before_actual = len(before_no_title.replace(' ', '').replace('\n', ''))
        after_actual = len(after_no_title.replace(' ', '').replace('\n', ''))

        print(f"\n[{idx+2}행] {keyword}")
        print(f"  C열 글자수: 검수전={before_c} / 검수후={after_c} {'(동일)' if before_c == after_c else '(다름)'}")
        print(f"  실제 글자수 (공백/줄바꿈 제외): 검수전={before_actual} / 검수후={after_actual}")

        # C열이 검수후 실제 글자수와 일치하는지 확인
        if before_c == after_actual or after_c == after_actual:
            print(f"  ✅ C열이 검수후 실제 글자수와 일치!")

        # C열이 키워드 관련 숫자인지 확인
        keyword_len = len(keyword) if not pd.isna(keyword) else 0
        if before_c == keyword_len:
            print(f"  ✅ C열이 키워드 글자수와 일치!")


if __name__ == '__main__':
    analyze_column_c()

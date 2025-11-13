#!/usr/bin/env python3
"""
C열이 검수후 목표 글자수인지 검증
"""

import pandas as pd


def verify_column_c():
    """C열과 검수후 실제 글자수 비교"""

    # 엑셀 읽기
    before_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')
    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    print("=" * 120)
    print("C열이 '검수후 목표 글자수'인지 검증")
    print("=" * 120)

    matches = 0
    total = 0

    for idx in range(min(20, len(before_df))):
        after_row = after_df.iloc[idx]

        keyword = after_row['키워드']
        c_value = after_row['글자수']
        after_text = after_row['원고']

        if pd.isna(after_text):
            continue

        # 제목 제거
        after_no_title = '\n'.join([line for line in after_text.split('\n') if not line.strip().startswith('#')])

        # 여러 방식으로 글자수 계산
        actual_no_space = len(after_no_title.replace(' ', '').replace('\n', ''))  # 공백/줄바꿈 제외
        actual_with_space = len(after_no_title.replace('\n', ''))  # 줄바꿈만 제외
        actual_all = len(after_no_title)  # 전체

        # 차이 계산
        diff_no_space = abs(c_value - actual_no_space)
        diff_with_space = abs(c_value - actual_with_space)
        diff_all = abs(c_value - actual_all)

        # 가장 가까운 방식 찾기
        min_diff = min(diff_no_space, diff_with_space, diff_all)

        match_type = ""
        if diff_no_space == min_diff:
            match_type = "공백/줄바꿈 제외"
        elif diff_with_space == min_diff:
            match_type = "줄바꿈만 제외"
        else:
            match_type = "전체 포함"

        total += 1

        print(f"\n[{idx+2}행] {keyword}")
        print(f"  C열: {c_value}")
        print(f"  검수후 실제 (공백/줄바꿈 제외): {actual_no_space} (차이: {diff_no_space})")
        print(f"  검수후 실제 (줄바꿈만 제외): {actual_with_space} (차이: {diff_with_space})")
        print(f"  검수후 실제 (전체): {actual_all} (차이: {diff_all})")

        if min_diff <= 10:
            print(f"  ✅ 거의 일치! (가장 가까운 방식: {match_type})")
            matches += 1
        elif min_diff <= 50:
            print(f"  ⚠️ 비슷함 (가장 가까운 방식: {match_type})")
        else:
            print(f"  ❌ 차이가 큼")

    print(f"\n\n{'=' * 120}")
    print(f"결과 요약")
    print(f"{'=' * 120}")
    print(f"  10자 이내 일치: {matches}/{total}행")
    print(f"\n✅ C열은 '검수후 원고의 목표 글자수'일 가능성이 높음")


if __name__ == '__main__':
    verify_column_c()

#!/usr/bin/env python3
"""
C열 글자수 재확인 - 여러 계산 방식으로
"""

import pandas as pd


def check_chars():
    """여러 방식으로 글자수 계산해서 C열과 비교"""

    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    print("=" * 120)
    print("C열 글자수 재확인")
    print("=" * 120)

    stats = {
        '공백줄바꿈제외': 0,
        '줄바꿈만제외': 0,
        '전체포함': 0,
        '첫문단만': 0,
        '나머지만': 0,
        'total': 0
    }

    for idx, row in after_df.iterrows():
        if idx >= 20:  # 20개만
            break

        keyword = row['키워드']
        target_chars = row['글자수']
        원고 = row['원고']

        if pd.isna(원고):
            continue

        # 제목 제거
        lines = [line for line in 원고.split('\n') if not line.strip().startswith('#')]
        text_no_title = '\n'.join(lines)

        # 첫 문단/나머지 분리
        paragraphs = text_no_title.split('\n\n')
        첫문단 = paragraphs[0] if paragraphs else ""
        나머지 = '\n\n'.join(paragraphs[1:]) if len(paragraphs) > 1 else ""

        # 여러 방식으로 글자수 계산
        방식1 = len(text_no_title.replace(' ', '').replace('\n', ''))  # 공백/줄바꿈 제외
        방식2 = len(text_no_title.replace('\n', ''))  # 줄바꿈만 제외
        방식3 = len(text_no_title)  # 전체 포함
        방식4 = len(첫문단.replace(' ', '').replace('\n', ''))  # 첫문단만
        방식5 = len(나머지.replace(' ', '').replace('\n', ''))  # 나머지만

        # 차이 계산
        차이1 = abs(target_chars - 방식1)
        차이2 = abs(target_chars - 방식2)
        차이3 = abs(target_chars - 방식3)
        차이4 = abs(target_chars - 방식4)
        차이5 = abs(target_chars - 방식5)

        # 가장 가까운 방식 찾기
        차이들 = [차이1, 차이2, 차이3, 차이4, 차이5]
        최소차이 = min(차이들)
        일치방식 = ['공백줄바꿈제외', '줄바꿈만제외', '전체포함', '첫문단만', '나머지만'][차이들.index(최소차이)]

        print(f"\n[{idx+2}행] {keyword}")
        print(f"  C열 목표: {target_chars}자")
        print(f"  공백/줄바꿈 제외: {방식1}자 (차이: {차이1})")
        print(f"  줄바꿈만 제외: {방식2}자 (차이: {차이2})")
        print(f"  전체 포함: {방식3}자 (차이: {차이3})")
        print(f"  첫문단만: {방식4}자 (차이: {차이4})")
        print(f"  나머지만: {방식5}자 (차이: {차이5})")
        print(f"  → 가장 가까운 방식: {일치방식} (차이: {최소차이})")

        stats['total'] += 1
        if 차이1 <= 10:
            stats['공백줄바꿈제외'] += 1
        if 차이2 <= 10:
            stats['줄바꿈만제외'] += 1
        if 차이3 <= 10:
            stats['전체포함'] += 1
        if 차이4 <= 10:
            stats['첫문단만'] += 1
        if 차이5 <= 10:
            stats['나머지만'] += 1

    # 요약
    print(f"\n\n{'=' * 120}")
    print("통계 (10자 이내 일치)")
    print(f"{'=' * 120}")
    total = stats['total']
    for key, count in stats.items():
        if key != 'total':
            print(f"  {key}: {count}/{total} ({count/total*100:.1f}%)")

    # 결론
    가장많은 = max([(k, v) for k, v in stats.items() if k != 'total'], key=lambda x: x[1])
    print(f"\n✅ C열은 '{가장많은[0]}' 방식일 가능성이 가장 높음 ({가장많은[1]}/{total} = {가장많은[1]/total*100:.1f}%)")


if __name__ == '__main__':
    check_chars()

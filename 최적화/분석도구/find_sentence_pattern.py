#!/usr/bin/env python3
"""
패턴 찾기: 통키워드로 시작하는 문장 개수
"""

import pandas as pd
import re


def count_sentences_starting_with_keyword(text, keyword):
    """키워드로 시작하는 문장 개수 세기"""
    if not keyword:
        return 0, []

    # 문장 분리 (., !, ?, 줄바꿈으로 시작)
    # 각 문장의 시작 부분이 키워드인지 확인

    sentences_with_keyword = []
    count = 0

    # 줄바꿈으로 분리
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 이 줄이 키워드로 시작하는지 확인
        if line.startswith(keyword):
            sentences_with_keyword.append(line[:50] + '...' if len(line) > 50 else line)
            count += 1

    return count, sentences_with_keyword


def analyze_pattern():
    """검수 후 원고들의 패턴 분석"""

    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    print("=" * 120)
    print("패턴 분석: 통키워드로 시작하는 문장")
    print("=" * 120)

    results = []

    for idx, row in after_df.iterrows():
        if idx >= 15:  # 처음 15개만
            break

        keyword = row['키워드']
        원고 = row['원고']

        if pd.isna(원고):
            continue

        # 제목 제거
        lines = [line for line in 원고.split('\n') if not line.strip().startswith('#')]
        text_no_title = '\n'.join(lines)

        # 첫 문단과 나머지
        paragraphs = text_no_title.split('\n\n')
        첫문단 = paragraphs[0] if paragraphs else ""
        나머지 = '\n\n'.join(paragraphs[1:]) if len(paragraphs) > 1 else ""
        전체 = text_no_title

        # 키워드로 시작하는 문장 세기
        전체_count, 전체_sentences = count_sentences_starting_with_keyword(전체, keyword)
        첫문단_count, 첫문단_sentences = count_sentences_starting_with_keyword(첫문단, keyword)
        나머지_count, 나머지_sentences = count_sentences_starting_with_keyword(나머지, keyword)

        print(f"\n[{idx+2}행] 키워드: {keyword}")
        print(f"  전체 원고: 키워드로 시작하는 문장 {전체_count}개")
        print(f"  첫 문단: 키워드로 시작하는 문장 {첫문단_count}개")
        print(f"  나머지: 키워드로 시작하는 문장 {나머지_count}개")

        if 전체_sentences:
            print(f"  문장들:")
            for s in 전체_sentences[:5]:  # 처음 5개만
                print(f"    - {s}")

        results.append({
            'keyword': keyword,
            '전체': 전체_count,
            '첫문단': 첫문단_count,
            '나머지': 나머지_count
        })

    # 패턴 요약
    print(f"\n\n{'=' * 120}")
    print("패턴 요약")
    print(f"{'=' * 120}")

    # 가장 많은 패턴 찾기
    from collections import Counter
    전체_counts = Counter([r['전체'] for r in results])
    첫문단_counts = Counter([r['첫문단'] for r in results])

    print(f"\n전체 원고에서 키워드로 시작하는 문장 개수 분포:")
    for count, freq in sorted(전체_counts.items()):
        print(f"  {count}개: {freq}회")

    print(f"\n첫 문단에서 키워드로 시작하는 문장 개수 분포:")
    for count, freq in sorted(첫문단_counts.items()):
        print(f"  {count}개: {freq}회")

    # 가장 많은 패턴
    most_common_전체 = 전체_counts.most_common(1)[0] if 전체_counts else (0, 0)
    most_common_첫문단 = 첫문단_counts.most_common(1)[0] if 첫문단_counts else (0, 0)

    print(f"\n✅ 발견된 패턴:")
    print(f"  - 전체 원고: 통키워드로 시작하는 문장 약 {most_common_전체[0]}개")
    print(f"  - 첫 문단: 통키워드로 시작하는 문장 약 {most_common_첫문단[0]}개")


if __name__ == '__main__':
    analyze_pattern()

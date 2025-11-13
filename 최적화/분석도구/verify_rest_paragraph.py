#!/usr/bin/env python3
"""
새로운 가설 검증:
- 첫 문단: 통키워드 무조건 2회 (고정)
- D~F열: 첫 문단 제외한 나머지 부분에서의 목표 출현 횟수
"""

import pandas as pd
import re


def get_first_paragraph(text):
    """첫 문단 추출"""
    if not text:
        return ""

    lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
    text_no_title = '\n'.join(lines)

    paragraphs = text_no_title.split('\n\n')
    if paragraphs:
        return paragraphs[0].strip()
    return ""


def get_rest_paragraphs(text):
    """첫 문단 제외한 나머지 추출"""
    if not text:
        return ""

    lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
    text_no_title = '\n'.join(lines)

    paragraphs = text_no_title.split('\n\n')
    if len(paragraphs) > 1:
        return '\n\n'.join(paragraphs[1:]).strip()
    return ""


def count_keyword_simple(text, keyword):
    """단순 카운트"""
    if not keyword or pd.isna(keyword):
        return 0
    return text.count(keyword)


def parse_target_value(value_str):
    """목표값 파싱"""
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


def verify_rest_paragraph_hypothesis():
    """첫 문단 제외 나머지 부분 가설 검증"""

    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    print("=" * 120)
    print("가설 검증: 첫 문단=통키워드 2회(고정), D~F열=나머지 부분 목표")
    print("=" * 120)

    match_stats = {
        '첫문단_통키워드2회': 0,
        '나머지_통키워드일치': 0,
        '나머지_조각키워드일치': 0,
        'total': 0
    }

    for idx, row in after_df.iterrows():
        if idx >= 15:  # 처음 15개만
            break

        keyword = row['키워드']
        target_whole = parse_target_value(row['통키워드 반복수'])
        target_pieces = parse_target_value(row['조각키워드 반복수'])
        원고 = row['원고']

        if pd.isna(원고):
            continue

        첫문단 = get_first_paragraph(원고)
        나머지 = get_rest_paragraphs(원고)

        print(f"\n{'=' * 120}")
        print(f"[{idx+2}행] 키워드: {keyword}")
        print(f"{'=' * 120}")

        # 1. 첫 문단 통키워드 2회 확인
        첫문단_통키워드 = count_keyword_simple(첫문단, keyword)
        첫문단2회 = (첫문단_통키워드 == 2)

        print(f"\n첫 문단 통키워드: {첫문단_통키워드}회 {'✅ (2회 고정규칙 충족)' if 첫문단2회 else '❌'}")

        # 2. 나머지 부분 통키워드 확인
        whole_match = True
        if target_whole:
            print(f"\n나머지 부분 통키워드:")
            for kw, target_count in target_whole.items():
                나머지_count = count_keyword_simple(나머지, kw)
                match = (나머지_count == target_count)
                whole_match = whole_match and match

                print(f"  '{kw}': 목표={target_count}회, 실제={나머지_count}회 {'✅' if match else '❌'}")

        # 3. 나머지 부분 조각키워드 확인
        piece_match = True
        if target_pieces:
            print(f"\n나머지 부분 조각키워드:")
            for kw, target_count in target_pieces.items():
                첫문단_piece = count_keyword_simple(첫문단, kw)
                나머지_piece = count_keyword_simple(나머지, kw)
                match = (나머지_piece == target_count)
                piece_match = piece_match and match

                print(f"  '{kw}':")
                print(f"    첫문단: {첫문단_piece}회")
                print(f"    나머지: 목표={target_count}회, 실제={나머지_piece}회 {'✅' if match else '❌'}")

        # 통계
        match_stats['total'] += 1
        if 첫문단2회:
            match_stats['첫문단_통키워드2회'] += 1
        if whole_match:
            match_stats['나머지_통키워드일치'] += 1
        if piece_match:
            match_stats['나머지_조각키워드일치'] += 1

    # 요약
    print(f"\n\n{'=' * 120}")
    print("가설 검증 결과")
    print(f"{'=' * 120}")
    total = match_stats['total']
    print(f"총 {total}개 분석")
    print(f"  첫 문단 통키워드 2회: {match_stats['첫문단_통키워드2회']}/{total} ({match_stats['첫문단_통키워드2회']/total*100:.1f}%)")
    print(f"  나머지 부분 통키워드 일치: {match_stats['나머지_통키워드일치']}/{total} ({match_stats['나머지_통키워드일치']/total*100:.1f}%)")
    print(f"  나머지 부분 조각키워드 일치: {match_stats['나머지_조각키워드일치']}/{total} ({match_stats['나머지_조각키워드일치']/total*100:.1f}%)")

    if match_stats['첫문단_통키워드2회'] >= total * 0.9 and match_stats['나머지_통키워드일치'] >= total * 0.9:
        print(f"\n✅✅✅ 가설 성립!!!")
        print(f"  - 첫 문단: 통키워드 무조건 2회 (고정 규칙)")
        print(f"  - D~F열: 첫 문단 제외한 나머지 부분의 목표 출현 횟수")
    else:
        print(f"\n❌ 가설 불성립")


if __name__ == '__main__':
    verify_rest_paragraph_hypothesis()

#!/usr/bin/env python3
"""
첫 문단에서의 키워드 출현 분석
가설: D~F열은 첫 문단에서의 목표 출현 횟수?
"""

import pandas as pd
import re


def get_first_paragraph(text):
    """첫 문단 추출 (빈 줄로 구분)"""
    if not text:
        return ""

    # 제목 제거
    lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
    text_no_title = '\n'.join(lines)

    # 첫 문단 추출 (빈 줄 전까지)
    paragraphs = text_no_title.split('\n\n')
    if paragraphs:
        return paragraphs[0].strip()
    return text_no_title.strip()


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


def analyze_first_paragraph():
    """첫 문단에서의 키워드 출현 분석"""

    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    print("=" * 120)
    print("첫 문단 키워드 분석 - D~F열이 첫 문단 기준인가?")
    print("=" * 120)

    match_stats = {
        '통키워드_전체일치': 0,
        '조각키워드_전체일치': 0,
        'total': 0
    }

    for idx, row in after_df.iterrows():
        if idx >= 10:  # 처음 10개만
            break

        keyword = row['키워드']
        target_whole = parse_target_value(row['통키워드 반복수'])
        target_pieces = parse_target_value(row['조각키워드 반복수'])
        원고 = row['원고']

        if pd.isna(원고):
            continue

        # 전체 원고와 첫 문단 추출
        원고_전체 = '\n'.join([line for line in 원고.split('\n') if not line.strip().startswith('#')])
        첫문단 = get_first_paragraph(원고)

        print(f"\n{'=' * 120}")
        print(f"[{idx+2}행] 키워드: {keyword}")
        print(f"{'=' * 120}")
        print(f"\n첫 문단:\n{첫문단}")
        print(f"\n{'-' * 120}")

        # 통키워드 분석
        whole_match = True
        if target_whole:
            print(f"\n통키워드:")
            for kw, target_count in target_whole.items():
                전체_count = count_keyword_simple(원고_전체, kw)
                첫문단_count = count_keyword_simple(첫문단, kw)

                match_전체 = (전체_count == target_count)
                match_첫문단 = (첫문단_count == target_count)

                print(f"\n  '{kw}':")
                print(f"    목표: {target_count}회")
                print(f"    전체 원고: {전체_count}회 {'✅' if match_전체 else '❌'}")
                print(f"    첫 문단: {첫문단_count}회 {'✅' if match_첫문단 else '❌'}")

                whole_match = whole_match and match_첫문단

        # 조각키워드 분석
        piece_match = True
        if target_pieces:
            print(f"\n조각키워드:")
            for kw, target_count in target_pieces.items():
                전체_count = count_keyword_simple(원고_전체, kw)
                첫문단_count = count_keyword_simple(첫문단, kw)

                match_전체 = (전체_count == target_count)
                match_첫문단 = (첫문단_count == target_count)

                print(f"\n  '{kw}':")
                print(f"    목표: {target_count}회")
                print(f"    전체 원고: {전체_count}회 {'✅' if match_전체 else '❌'}")
                print(f"    첫 문단: {첫문단_count}회 {'✅' if match_첫문단 else '❌'}")

                piece_match = piece_match and match_첫문단

        match_stats['total'] += 1
        if whole_match:
            match_stats['통키워드_전체일치'] += 1
        if piece_match:
            match_stats['조각키워드_전체일치'] += 1

    # 요약
    print(f"\n\n{'=' * 120}")
    print("결과 요약 (첫 문단 기준)")
    print(f"{'=' * 120}")
    total = match_stats['total']
    print(f"총 {total}개 분석")
    print(f"  통키워드 일치: {match_stats['통키워드_전체일치']}/{total} ({match_stats['통키워드_전체일치']/total*100:.1f}%)")
    print(f"  조각키워드 일치: {match_stats['조각키워드_전체일치']}/{total} ({match_stats['조각키워드_전체일치']/total*100:.1f}%)")

    if match_stats['통키워드_전체일치'] >= total * 0.7:
        print(f"\n✅ D~F열은 '첫 문단에서의 목표 출현 횟수'일 가능성이 높습니다!")
    else:
        print(f"\n❌ 첫 문단 기준도 아닙니다. 다른 의미를 가집니다.")


if __name__ == '__main__':
    analyze_first_paragraph()

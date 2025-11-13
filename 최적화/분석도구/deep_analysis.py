#!/usr/bin/env python3
"""
정확한 이해를 바탕으로 다시 분석
- 검수후 원고(G열)가 기준(C~F열)을 충족하는지 확인
- 충족하지 못하면 카운팅 로직을 수정해야 함
"""

import pandas as pd
import re
from collections import Counter


def count_keyword_method1(text, keyword):
    """
    방법1: 키워드 뒤에 공백이나 문장부호
    예: "강남 맛집 추천" 뒤에 공백 or 문장부호
    """
    if not keyword or pd.isna(keyword):
        return 0
    pattern = rf'{re.escape(keyword)}(?=\s|$|[.!?,\n])'
    return len(re.findall(pattern, text))


def count_keyword_method2(text, keyword):
    """
    방법2: 단순 문자열 카운트 (text.count)
    """
    if not keyword or pd.isna(keyword):
        return 0
    return text.count(keyword)


def count_keyword_method3(text, keyword):
    """
    방법3: 키워드 뒤에 한글이 아닌 것 (조사 제외)
    예: "강남 맛집 추천" 뒤에 한글이 아니거나 공백
    """
    if not keyword or pd.isna(keyword):
        return 0
    # 키워드 뒤에 한글 자모가 없거나 공백/문장부호
    pattern = rf'{re.escape(keyword)}(?![가-힣]|[ㄱ-ㅎ]|[ㅏ-ㅣ])'
    return len(re.findall(pattern, text))


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


def deep_analysis():
    """검수후 원고가 기준을 충족하는지 여러 카운팅 방법으로 분석"""

    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    print("=" * 120)
    print("검수후 원고 vs 기준 - 여러 카운팅 방법 비교")
    print("=" * 120)

    # 처음 5개 행만 상세 분석
    for idx in range(min(5, len(after_df))):
        row = after_df.iloc[idx]

        keyword = row['키워드']
        target_whole = parse_target_value(row['통키워드 반복수'])
        target_pieces = parse_target_value(row['조각키워드 반복수'])
        원고 = row['원고']

        if pd.isna(원고):
            continue

        # 제목 제거
        원고_no_title = '\n'.join([line for line in 원고.split('\n') if not line.strip().startswith('#')])

        print(f"\n{'=' * 120}")
        print(f"[{idx+2}행] 키워드: {keyword}")
        print(f"{'=' * 120}")

        # 통키워드 분석
        if target_whole:
            print(f"\n통키워드 분석:")
            for kw, target_count in target_whole.items():
                m1 = count_keyword_method1(원고_no_title, kw)
                m2 = count_keyword_method2(원고_no_title, kw)
                m3 = count_keyword_method3(원고_no_title, kw)

                print(f"\n  키워드: '{kw}'")
                print(f"  목표: {target_count}회")
                print(f"  방법1 (공백/문장부호 뒤): {m1}회 {'✅' if m1 == target_count else '❌'}")
                print(f"  방법2 (단순 카운트): {m2}회 {'✅' if m2 == target_count else '❌'}")
                print(f"  방법3 (한글 제외): {m3}회 {'✅' if m3 == target_count else '❌'}")

                # 실제 위치 찾기
                positions = [m.start() for m in re.finditer(re.escape(kw), 원고_no_title)]
                print(f"\n  '{kw}' 출현 위치:")
                for pos in positions[:5]:  # 처음 5개만
                    context_start = max(0, pos - 10)
                    context_end = min(len(원고_no_title), pos + len(kw) + 10)
                    context = 원고_no_title[context_start:context_end]
                    # 특수문자 표시
                    context_display = context.replace('\n', '\\n').replace(' ', '·')
                    print(f"    위치 {pos}: ...{context_display}...")

        # 조각키워드 분석
        if target_pieces:
            print(f"\n조각키워드 분석:")
            for kw, target_count in target_pieces.items():
                m1 = count_keyword_method1(원고_no_title, kw)
                m2 = count_keyword_method2(원고_no_title, kw)
                m3 = count_keyword_method3(원고_no_title, kw)

                print(f"\n  키워드: '{kw}'")
                print(f"  목표: {target_count}회")
                print(f"  방법1 (공백/문장부호 뒤): {m1}회 {'✅' if m1 == target_count else '❌'}")
                print(f"  방법2 (단순 카운트): {m2}회 {'✅' if m2 == target_count else '❌'}")
                print(f"  방법3 (한글 제외): {m3}회 {'✅' if m3 == target_count else '❌'}")


if __name__ == '__main__':
    deep_analysis()

#!/usr/bin/env python3
"""
검수후 원고가 C~F열 기준을 얼마나 충족하는지 분석
"""

import pandas as pd
import re
from collections import Counter


def count_keyword_spacing_rule(text, keyword):
    """
    띄어쓰기 기준 키워드 카운팅
    키워드 뒤에 공백이나 문장부호가 있어야 카운팅
    (조사가 바로 붙으면 카운팅 X)
    """
    if not keyword or pd.isna(keyword):
        return 0

    # 키워드 뒤에 공백, 줄바꿈, 문장부호가 오는 경우만
    pattern = rf'{re.escape(keyword)}(?=\s|$|[^\w가-힣])'
    matches = re.findall(pattern, text)
    return len(matches)


def count_subkeywords(text, exclude_keywords=None):
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
            subkeywords.add(punct * 2)  # ??는 하나의 서브키워드

    return len(subkeywords), list(subkeywords)


def parse_target_value(value_str):
    """
    D, E열의 목표값 파싱
    예: "팔꿈치 쿠션 보호대 : 0" → {"팔꿈치 쿠션 보호대": 0}
    예: "팔꿈치 : 0\n쿠션 : 0\n보호대 : 1" → {"팔꿈치": 0, "쿠션": 0, "보호대": 1}
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


def analyze_compliance():
    """검수후 원고가 기준을 얼마나 충족하는지 분석"""

    # 엑셀 읽기
    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    print("=" * 120)
    print("검수 후 원고의 기준 충족도 분석")
    print("=" * 120)

    compliance_summary = {
        '글자수_일치': 0,
        '통키워드_일치': 0,
        '조각키워드_일치': 0,
        '서브키워드_일치': 0,
        '전체_일치': 0,
        'total': 0
    }

    for idx, row in after_df.iterrows():
        keyword = row['키워드']
        target_chars = row['글자수']
        target_whole = parse_target_value(row['통키워드 반복수'])
        target_pieces = parse_target_value(row['조각키워드 반복수'])
        target_subkeywords = row['서브키워드 목록 수']
        원고 = row['원고']

        if pd.isna(원고):
            continue

        # 제목 제거
        원고_no_title = '\n'.join([line for line in 원고.split('\n') if not line.strip().startswith('#')])

        print(f"\n{'=' * 120}")
        print(f"[{idx+2}행] 키워드: {keyword}")
        print(f"{'=' * 120}")

        # 1. 글자수 체크
        actual_chars = len(원고_no_title.replace(' ', '').replace('\n', ''))
        chars_match = abs(actual_chars - target_chars) <= 10  # 10자 이내 허용

        print(f"\n1. 글자수:")
        print(f"   목표: {target_chars}자")
        print(f"   실제: {actual_chars}자")
        print(f"   차이: {actual_chars - target_chars:+d}자")
        print(f"   {'✅ 일치' if chars_match else '❌ 불일치'}")

        # 2. 통키워드 체크
        whole_match = True
        if target_whole:
            print(f"\n2. 통키워드 반복수:")
            for kw, target_count in target_whole.items():
                actual_count = count_keyword_spacing_rule(원고_no_title, kw)
                match = (actual_count == target_count)
                whole_match = whole_match and match
                print(f"   '{kw}':")
                print(f"     목표: {target_count}회")
                print(f"     실제: {actual_count}회")
                print(f"     {'✅ 일치' if match else '❌ 불일치'}")

        # 3. 조각키워드 체크
        piece_match = True
        if target_pieces:
            print(f"\n3. 조각키워드 반복수:")
            for kw, target_count in target_pieces.items():
                actual_count = count_keyword_spacing_rule(원고_no_title, kw)
                match = (actual_count == target_count)
                piece_match = piece_match and match
                print(f"   '{kw}':")
                print(f"     목표: {target_count}회")
                print(f"     실제: {actual_count}회")
                print(f"     {'✅ 일치' if match else '❌ 불일치'}")

        # 4. 서브키워드 목록 수 체크
        exclude_list = [keyword] if keyword else []
        if target_pieces:
            exclude_list.extend(target_pieces.keys())

        actual_subkeywords_count, actual_subkeywords = count_subkeywords(원고_no_title, exclude_list)
        sub_match = (actual_subkeywords_count == target_subkeywords)

        print(f"\n4. 서브키워드 목록 수:")
        print(f"   목표: {target_subkeywords}개")
        print(f"   실제: {actual_subkeywords_count}개")
        print(f"   {'✅ 일치' if sub_match else '❌ 불일치'}")
        if actual_subkeywords and len(actual_subkeywords) <= 20:
            print(f"   실제 서브키워드: {', '.join(actual_subkeywords[:20])}")

        # 통계
        compliance_summary['total'] += 1
        if chars_match:
            compliance_summary['글자수_일치'] += 1
        if whole_match:
            compliance_summary['통키워드_일치'] += 1
        if piece_match:
            compliance_summary['조각키워드_일치'] += 1
        if sub_match:
            compliance_summary['서브키워드_일치'] += 1
        if chars_match and whole_match and piece_match and sub_match:
            compliance_summary['전체_일치'] += 1

    # 요약
    print(f"\n\n{'=' * 120}")
    print("기준 충족도 요약")
    print(f"{'=' * 120}")
    total = compliance_summary['total']
    print(f"총 {total}개 원고 분석")
    print(f"  글자수 일치: {compliance_summary['글자수_일치']}/{total} ({compliance_summary['글자수_일치']/total*100:.1f}%)")
    print(f"  통키워드 일치: {compliance_summary['통키워드_일치']}/{total} ({compliance_summary['통키워드_일치']/total*100:.1f}%)")
    print(f"  조각키워드 일치: {compliance_summary['조각키워드_일치']}/{total} ({compliance_summary['조각키워드_일치']/total*100:.1f}%)")
    print(f"  서브키워드 일치: {compliance_summary['서브키워드_일치']}/{total} ({compliance_summary['서브키워드_일치']/total*100:.1f}%)")
    print(f"  전체 기준 충족: {compliance_summary['전체_일치']}/{total} ({compliance_summary['전체_일치']/total*100:.1f}%)")


if __name__ == '__main__':
    analyze_compliance()

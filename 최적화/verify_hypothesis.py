#!/usr/bin/env python3
"""
가설 검증: C~F열이 검수전 원고의 현재 상태를 나타내는가?
"""

import pandas as pd
import re
from collections import Counter


def count_keyword_spacing_rule(text, keyword):
    """띄어쓰기 기준 키워드 카운팅"""
    if not keyword or pd.isna(keyword):
        return 0
    pattern = rf'{re.escape(keyword)}(?=\s|$|[^\w가-힣])'
    matches = re.findall(pattern, text)
    return len(matches)


def count_subkeywords(text, exclude_keywords=None):
    """서브키워드 목록 수 계산"""
    if exclude_keywords is None:
        exclude_keywords = []

    words = re.findall(r'[가-힣]+', text)
    punctuations = re.findall(r'([^\w\s가-힣])\1+', text)

    word_counter = Counter(words)
    punct_counter = Counter(punctuations)

    subkeywords = set()
    for word, count in word_counter.items():
        if count >= 2 and len(word) >= 2 and word not in exclude_keywords:
            subkeywords.add(word)

    for punct, count in punct_counter.items():
        if count >= 2:
            subkeywords.add(punct * 2)

    return len(subkeywords)


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


def verify_hypothesis():
    """가설 검증: C~F열이 검수전 원고 상태인가?"""

    before_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')

    print("=" * 120)
    print("가설 검증: C~F열이 '검수전 원고의 현재 상태'를 나타내는가?")
    print("=" * 120)

    match_count = {
        '글자수': 0,
        '통키워드': 0,
        '조각키워드': 0,
        '서브키워드': 0,
        'total': 0
    }

    for idx, row in before_df.iterrows():
        keyword = row['키워드']
        표시된_글자수 = row['글자수']
        표시된_통키워드 = parse_target_value(row['통키워드 반복수'])
        표시된_조각키워드 = parse_target_value(row['조각키워드 반복수'])
        표시된_서브키워드 = row['서브키워드 목록 수']
        원고 = row['원고']

        if pd.isna(원고):
            continue

        # 제목 제거
        원고_no_title = '\n'.join([line for line in 원고.split('\n') if not line.strip().startswith('#')])

        print(f"\n{'=' * 120}")
        print(f"[{idx+2}행] 키워드: {keyword}")
        print(f"{'=' * 120}")

        # 1. 글자수 비교
        실제_글자수 = len(원고_no_title.replace(' ', '').replace('\n', ''))
        글자수_일치 = abs(실제_글자수 - 표시된_글자수) <= 20

        print(f"\n1. 글자수:")
        print(f"   C열 표시: {표시된_글자수}자")
        print(f"   검수전 실제: {실제_글자수}자")
        print(f"   차이: {abs(실제_글자수 - 표시된_글자수)}자")
        print(f"   {'✅ 일치' if 글자수_일치 else '❌ 불일치'}")

        # 2. 통키워드 비교
        통키워드_일치 = True
        if 표시된_통키워드:
            print(f"\n2. 통키워드:")
            for kw, 표시된_횟수 in 표시된_통키워드.items():
                실제_횟수 = count_keyword_spacing_rule(원고_no_title, kw)
                일치 = (실제_횟수 == 표시된_횟수)
                통키워드_일치 = 통키워드_일치 and 일치
                print(f"   '{kw}':")
                print(f"     D열 표시: {표시된_횟수}회")
                print(f"     검수전 실제: {실제_횟수}회")
                print(f"     {'✅ 일치' if 일치 else '❌ 불일치'}")

        # 3. 조각키워드 비교
        조각키워드_일치 = True
        if 표시된_조각키워드:
            print(f"\n3. 조각키워드:")
            for kw, 표시된_횟수 in 표시된_조각키워드.items():
                실제_횟수 = count_keyword_spacing_rule(원고_no_title, kw)
                일치 = (실제_횟수 == 표시된_횟수)
                조각키워드_일치 = 조각키워드_일치 and 일치
                print(f"   '{kw}':")
                print(f"     E열 표시: {표시된_횟수}회")
                print(f"     검수전 실제: {실제_횟수}회")
                print(f"     {'✅ 일치' if 일치 else '❌ 불일치'}")

        # 4. 서브키워드 비교
        exclude_list = [keyword] if keyword else []
        if 표시된_조각키워드:
            exclude_list.extend(표시된_조각키워드.keys())

        실제_서브키워드 = count_subkeywords(원고_no_title, exclude_list)
        서브키워드_일치 = (실제_서브키워드 == 표시된_서브키워드)

        print(f"\n4. 서브키워드 목록 수:")
        print(f"   F열 표시: {표시된_서브키워드}개")
        print(f"   검수전 실제: {실제_서브키워드}개")
        print(f"   {'✅ 일치' if 서브키워드_일치 else '❌ 불일치'}")

        # 통계
        match_count['total'] += 1
        if 글자수_일치:
            match_count['글자수'] += 1
        if 통키워드_일치:
            match_count['통키워드'] += 1
        if 조각키워드_일치:
            match_count['조각키워드'] += 1
        if 서브키워드_일치:
            match_count['서브키워드'] += 1

    # 요약
    print(f"\n\n{'=' * 120}")
    print("가설 검증 결과")
    print(f"{'=' * 120}")
    total = match_count['total']
    print(f"총 {total}개 원고 분석")
    print(f"  글자수 일치: {match_count['글자수']}/{total} ({match_count['글자수']/total*100:.1f}%)")
    print(f"  통키워드 일치: {match_count['통키워드']}/{total} ({match_count['통키워드']/total*100:.1f}%)")
    print(f"  조각키워드 일치: {match_count['조각키워드']}/{total} ({match_count['조각키워드']/total*100:.1f}%)")
    print(f"  서브키워드 일치: {match_count['서브키워드']}/{total} ({match_count['서브키워드']/total*100:.1f}%)")

    # 결론
    print(f"\n{'=' * 120}")
    if match_count['통키워드'] >= total * 0.8 and match_count['조각키워드'] >= total * 0.8:
        print("✅ 가설 성립! C~F열은 '검수전 원고의 현재 상태'를 나타냅니다.")
    else:
        print("❌ 가설 불성립. C~F열은 다른 의미를 가집니다.")


if __name__ == '__main__':
    verify_hypothesis()

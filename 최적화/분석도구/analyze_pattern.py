#!/usr/bin/env python3
"""
검수전 시트 패턴 분석 - 글자수가 무엇을 의미하는지 찾기
"""

import pandas as pd
import re


def count_keyword_exact(text, keyword):
    """띄어쓰기 기준 키워드 카운팅 (뒤에 공백이나 문장부호)"""
    if not keyword or pd.isna(keyword):
        return 0
    # 키워드 뒤에 공백, 줄바꿈, 문장부호가 오는 경우만
    pattern = rf'{re.escape(keyword)}(?=\s|$|[^\w가-힣])'
    return len(re.findall(pattern, text))


def count_subkeywords(text):
    """2번 이상 등장하는 단어 개수 세기 (서브키워드 목록 수)"""
    # 문장부호 제거하고 단어 분리
    words = re.findall(r'[가-힣]+|\S+', text)

    # 단어 빈도 계산
    word_count = {}
    for word in words:
        if len(word) >= 2:  # 2글자 이상만
            word_count[word] = word_count.get(word, 0) + 1

    # 2번 이상 등장하는 단어 개수
    subkeywords = [word for word, count in word_count.items() if count >= 2]
    return len(subkeywords), subkeywords


def analyze_all_rows():
    """검수전 시트의 모든 행 분석"""

    # 엑셀 읽기
    df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')

    print("=" * 120)
    print("검수전 시트 전체 분석 (2~21행)")
    print("=" * 120)

    results = []

    for idx, row in df.iterrows():
        keyword = row['키워드']
        글자수 = row['글자수']
        통키워드_반복수_str = row['통키워드 반복수']
        조각키워드_반복수_str = row['조각키워드 반복수']
        서브키워드_목록수 = row['서브키워드 목록 수']
        원고 = row['원고']

        if pd.isna(원고):
            continue

        # 제목 제거
        원고_no_title = '\n'.join([line for line in 원고.split('\n') if not line.strip().startswith('#')])

        # 실제 글자수 계산
        실제_글자수 = len(원고_no_title.replace(' ', '').replace('\n', ''))  # 공백/줄바꿈 제외
        실제_글자수_공백포함 = len(원고_no_title)
        실제_글자수_줄바꿈제외 = len(원고_no_title.replace('\n', ''))

        # 통 키워드 카운팅
        통키워드_실제 = count_keyword_exact(원고_no_title, keyword)

        # 조각 키워드 카운팅
        pieces = keyword.split() if keyword and not pd.isna(keyword) else []
        조각키워드_실제 = {}
        for piece in pieces:
            조각키워드_실제[piece] = count_keyword_exact(원고_no_title, piece)

        # 서브키워드 카운팅
        서브키워드_실제, 서브키워드_리스트 = count_subkeywords(원고_no_title)

        print(f"\n[{idx+2}행] 키워드: {keyword}")
        print(f"-" * 120)

        print(f"C열 글자수: {글자수}")
        print(f"  실제 글자수 (공백/줄바꿈 제외): {실제_글자수}")
        print(f"  실제 글자수 (공백 포함, 줄바꿈 제외): {실제_글자수_줄바꿈제외}")
        print(f"  실제 글자수 (공백/줄바꿈 포함): {실제_글자수_공백포함}")

        # 글자수 매칭 확인
        if 글자수 == 실제_글자수:
            print(f"  ✅ C열 = 공백/줄바꿈 제외 글자수")
        elif 글자수 == 실제_글자수_줄바꿈제외:
            print(f"  ✅ C열 = 공백 포함, 줄바꿈 제외 글자수")
        elif 글자수 == 실제_글자수_공백포함:
            print(f"  ✅ C열 = 공백/줄바꿈 포함 글자수")
        else:
            print(f"  ❓ C열 글자수가 어떤 계산법인지 불명확")

        print(f"\nD열 통키워드 반복수: {통키워드_반복수_str}")
        print(f"  실제 통키워드 출현: {통키워드_실제}회")

        if not pd.isna(조각키워드_반복수_str) and 조각키워드_반복수_str != '-':
            print(f"\nE열 조각키워드 반복수: {조각키워드_반복수_str}")
            print(f"  실제 조각키워드 출현:")
            for piece, count in 조각키워드_실제.items():
                print(f"    {piece}: {count}회")

        print(f"\nF열 서브키워드 목록 수: {서브키워드_목록수}")
        print(f"  실제 서브키워드 목록 수: {서브키워드_실제}개")

        results.append({
            'row': idx+2,
            'keyword': keyword,
            'C열_글자수': 글자수,
            '실제_공백줄바꿈제외': 실제_글자수,
            '실제_줄바꿈제외': 실제_글자수_줄바꿈제외,
            '실제_전체': 실제_글자수_공백포함,
            '차이_공백줄바꿈제외': 글자수 - 실제_글자수 if not pd.isna(글자수) else None,
            '차이_줄바꿈제외': 글자수 - 실제_글자수_줄바꿈제외 if not pd.isna(글자수) else None,
            '차이_전체': 글자수 - 실제_글자수_공백포함 if not pd.isna(글자수) else None,
        })

    # 패턴 요약
    print(f"\n\n{'=' * 120}")
    print("패턴 분석 요약")
    print(f"{'=' * 120}")

    # DataFrame으로 변환
    results_df = pd.DataFrame(results)

    print("\n글자수 계산 방식 추론:")

    # 각 계산 방식별로 일치하는 행 개수
    match_공백줄바꿈제외 = (results_df['차이_공백줄바꿈제외'] == 0).sum()
    match_줄바꿈제외 = (results_df['차이_줄바꿈제외'] == 0).sum()
    match_전체 = (results_df['차이_전체'] == 0).sum()

    total = len(results_df)

    print(f"  공백/줄바꿈 제외: {match_공백줄바꿈제외}/{total}행 일치")
    print(f"  줄바꿈만 제외 (공백 포함): {match_줄바꿈제외}/{total}행 일치")
    print(f"  공백/줄바꿈 포함: {match_전체}/{total}행 일치")

    # 가장 많이 일치하는 방식
    if match_공백줄바꿈제외 >= match_줄바꿈제외 and match_공백줄바꿈제외 >= match_전체:
        print(f"\n✅ 결론: C열 '글자수'는 공백/줄바꿈을 제외한 순수 글자 개수일 가능성이 높음")
    elif match_줄바꿈제외 >= match_공백줄바꿈제외 and match_줄바꿈제외 >= match_전체:
        print(f"\n✅ 결론: C열 '글자수'는 줄바꿈만 제외하고 공백은 포함한 글자 개수일 가능성이 높음")
    else:
        print(f"\n✅ 결론: C열 '글자수'는 공백/줄바꿈 모두 포함한 글자 개수일 가능성이 높음")

    # 차이 분포 확인
    print(f"\n차이 통계:")
    print(f"  공백/줄바꿈 제외 방식: 평균 차이 = {results_df['차이_공백줄바꿈제외'].abs().mean():.1f}")
    print(f"  줄바꿈만 제외 방식: 평균 차이 = {results_df['차이_줄바꿈제외'].abs().mean():.1f}")
    print(f"  전체 포함 방식: 평균 차이 = {results_df['차이_전체'].abs().mean():.1f}")


if __name__ == '__main__':
    analyze_all_rows()

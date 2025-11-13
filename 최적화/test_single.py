#!/usr/bin/env python3
"""단일 원고 테스트"""

import pandas as pd
from auto_manuscript_rewriter import AutoManuscriptRewriter

# API 키
api_key = "AIzaSyCGjirKto6fE3p80uD0O4CnlJeW4Bbc588"

# Rewriter 초기화
print("🤖 Gemini API 초기화 중...")
rewriter = AutoManuscriptRewriter(gemini_api_key=api_key)

# 엑셀 파일 읽기
df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')

# 첫 번째 원고
row = df.iloc[0]
keyword = row['키워드']
원고 = row['원고']
target_whole = row['통키워드 반복수']
target_pieces = row['조각키워드 반복수']
target_subkeywords = row['서브키워드 목록 수']

print(f"\n{'='*100}")
print(f"원고 수정 테스트 - 키워드: {keyword}")
print(f"{'='*100}\n")

# 원고 수정
result = rewriter.rewrite_manuscript(
    manuscript=원고,
    keyword=keyword,
    target_whole_str=target_whole,
    target_pieces_str=target_pieces,
    target_subkeywords=target_subkeywords
)

if result['success']:
    print("\n✅ 수정 완료!\n")
    print(f"{'='*100}")
    print("수정된 원고:")
    print(f"{'='*100}")
    print(result['rewritten'])
    print(f"\n{'='*100}")

    # 분석 결과
    after = result['after_analysis']
    print(f"\n📊 수정 후 분석:")
    print(f"  글자수: {after['chars']}자 (목표: 300~900자)")
    print(f"  첫문단 통키워드: {after['첫문단_통키워드']}회 (목표: 2회)")
    print(f"  통키워드 문장 시작: {after['통키워드_문장시작']}개 (목표: 2개)")

    # 조사 붙은 것 체크
    print(f"\n🔍 조사 체크:")
    text = result['rewritten']

    bad_patterns = [
        (f"{keyword}를", "를"),
        (f"{keyword}을", "을"),
        (f"{keyword}가", "가"),
        (f"{keyword}이", "이"),
        (f"{keyword}에", "에"),
        (f"{keyword}도", "도"),
        (f"{keyword}의", "의"),
    ]

    found_issues = []
    for pattern, particle in bad_patterns:
        if pattern in text:
            found_issues.append(f"  ❌ '{particle}' 조사 발견: {pattern}")

    if found_issues:
        print("  조사 붙은 키워드 발견:")
        for issue in found_issues:
            print(issue)
    else:
        print("  ✅ 조사 없이 깔끔!")

else:
    print(f"\n❌ 실패: {result.get('error', 'Unknown')}")

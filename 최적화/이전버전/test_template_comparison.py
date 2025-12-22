#!/usr/bin/env python3
"""템플릿 원고 비교 테스트"""

import pandas as pd
from search_optimizer import SearchOptimizer

# 옵티마이저 초기화
optimizer = SearchOptimizer()

# 템플릿 파일 읽기
df_before = pd.read_excel('/home/user/blogm/블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전', engine='openpyxl')
df_after = pd.read_excel('/home/user/blogm/블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후', engine='openpyxl')

print("=" * 80)
print("템플릿 원고 최적화 테스트")
print("=" * 80)

# 첫 번째 원고 테스트
idx = 0
keyword = df_before.iloc[idx]['키워드']
text_before = df_before.iloc[idx]['원고']
text_after_expected = df_after.iloc[idx]['원고']

print(f"\n키워드: {keyword}")
print(f"\n검수전 키워드 출현: {text_before.count(keyword)}회")
print(f"검수 후 키워드 출현 (기대값): {text_after_expected.count(keyword)}회")

# 우리 최적화 실행
result = optimizer.optimize_for_search(text_before, keyword, '')

print(f"우리 최적화 키워드 출현: {result['keyword_count']}회")

print("\n" + "=" * 80)
print("변경 사항")
print("=" * 80)
for change in result['changes']:
    print(f"  {change}")

print("\n" + "=" * 80)
print("금칙어 '네요' 확인")
print("=" * 80)
print(f"검수전 '네요' 개수: {text_before.count('네요')}개")
print(f"검수 후 '네요' 개수 (기대값): {text_after_expected.count('네요')}개")
print(f"우리 최적화 '네요' 개수: {result['optimized_text'].count('네요')}개")

if result['optimized_text'].count('네요') == 0:
    print("✅ '네요' 모두 치환됨!")
else:
    print("❌ '네요' 일부 남아있음")

print("\n" + "=" * 80)
print("금칙어 '더라구요' 확인")
print("=" * 80)
print(f"검수전 '더라구요' 개수: {text_before.count('더라구요')}개")
print(f"검수 후 '더라구요' 개수 (기대값): {text_after_expected.count('더라구요')}개")
print(f"우리 최적화 '더라구요' 개수: {result['optimized_text'].count('더라구요')}개")

if result['optimized_text'].count('더라구요') == text_after_expected.count('더라구요'):
    print("✅ '더라구요' 유지됨 (금칙어 아님)")
else:
    print("❌ '더라구요' 처리 불일치")

print("\n" + "=" * 80)
print("키워드 출현 횟수 비교")
print("=" * 80)
expected_count = text_after_expected.count(keyword)
actual_count = result['keyword_count']

if actual_count == expected_count:
    print(f"✅ 키워드 출현 일치: {actual_count}회")
elif actual_count == 2:
    print(f"✅ 키워드 출현 목표 달성: {actual_count}회 (기대값: {expected_count}회)")
else:
    print(f"⚠️ 키워드 출현 차이: {actual_count}회 vs {expected_count}회")

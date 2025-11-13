#!/usr/bin/env python3
"""
빠른 테스트 - 엑셀 파일 하나만 최적화해서 확인
"""

import sys
sys.path.append('/home/user/blogm')
from search_optimizer import SearchOptimizer
import pandas as pd

# 초기화
optimizer = SearchOptimizer()

# 엑셀 파일 경로
input_file = '/home/user/blogm/작업 의뢰용 데이터.xlsx'

print("=" * 80)
print("📋 엑셀 파일 첫 번째 원고만 최적화해서 미리보기")
print("=" * 80)
print()

# 엑셀 읽기
df = pd.read_excel(input_file)
first_row = df.iloc[0]

keyword = first_row['키워드']
brand = first_row.get('브랜드', '')
original = first_row['원고']

print(f"키워드: {keyword}")
print(f"브랜드: {brand}")
print(f"원본 길이: {len(original)}자")
print()

# 최적화
result = optimizer.optimize_for_search(original, keyword, brand)

print("=" * 80)
print("📊 결과")
print("=" * 80)
print(f"최적화 길이: {result['optimized_length']}자 ({result['length_diff']:+d}자)")
print(f"키워드 출현: {result['keyword_count']}회")
print()

print("변경사항:")
for change in result['changes']:
    print(f"  {change}")
print()

# 키워드+조사 확인
optimized = result['optimized_text']
print("키워드+조사 검증:")
patterns = [f'{keyword}를', f'{keyword}을', f'{keyword}가', f'{keyword}이', f'{keyword}에']
for p in patterns:
    count = optimized.count(p)
    print(f"  {'✅' if count == 0 else '❌'} '{p}': {'제거 완료' if count == 0 else f'{count}회 남음'}")
print()

print("=" * 80)
print("최적화된 원고:")
print("=" * 80)
print(optimized)
print()

print("🏷️ 해시태그:")
print(' '.join(['#' + tag for tag in result['hashtags'][:10]]))

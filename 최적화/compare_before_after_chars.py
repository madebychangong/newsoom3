#!/usr/bin/env python3
"""
검수전/후 C열 글자수 비교
"""

import pandas as pd

before_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')
after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

print("=" * 100)
print("검수전 vs 검수후 C열 글자수 비교 (처음 10개)")
print("=" * 100)

for idx in range(min(10, len(before_df))):
    before_row = before_df.iloc[idx]
    after_row = after_df.iloc[idx]
    
    keyword = before_row['키워드']
    before_c = before_row['글자수']
    after_c = after_row['글자수']
    
    before_text = before_row['원고']
    after_text = after_row['원고']
    
    if pd.isna(before_text) or pd.isna(after_text):
        continue
    
    # 제목 제거
    before_no_title = '\n'.join([line for line in before_text.split('\n') if not line.strip().startswith('#')])
    after_no_title = '\n'.join([line for line in after_text.split('\n') if not line.strip().startswith('#')])
    
    # 글자수 (공백/줄바꿈 제외)
    before_actual = len(before_no_title.replace(' ', '').replace('\n', ''))
    after_actual = len(after_no_title.replace(' ', '').replace('\n', ''))
    
    print(f"\n[{idx+2}행] {keyword}")
    print(f"  C열: {before_c}자 (검수전/후 동일)")
    print(f"  검수전 실제: {before_actual}자 (차이: {abs(before_c - before_actual)})")
    print(f"  검수후 실제: {after_actual}자 (차이: {abs(after_c - after_actual)})")
    print(f"  검수전→후 변화: {before_actual}자 → {after_actual}자 ({after_actual - before_actual:+d})")
    
    # C열이 어떤 의미일까?
    if abs(before_c - before_actual) < abs(after_c - after_actual):
        print(f"  → C열은 '검수전 글자수'에 가까움")
    elif abs(after_c - after_actual) < abs(before_c - before_actual):
        print(f"  → C열은 '검수후 글자수'에 가까움")
    else:
        print(f"  → C열은 둘 다 안 맞음")


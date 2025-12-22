#!/usr/bin/env python3
import pandas as pd

after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

print("=" * 100)
print("검수 후 원고 글자수 통계")
print("=" * 100)

글자수들 = []

for idx, row in after_df.iterrows():
    if idx >= 20:
        break
    
    keyword = row['키워드']
    text = row['원고']
    
    if pd.isna(text):
        continue
    
    # 제목 제거
    text_no_title = '\n'.join([line for line in text.split('\n') if not line.strip().startswith('#')])
    
    # 공백/줄바꿈 제외
    chars = len(text_no_title.replace(' ', '').replace('\n', ''))
    
    글자수들.append({
        'row': idx + 2,
        'keyword': keyword,
        'chars': chars
    })
    
    print(f"[{idx+2}행] {keyword:20s} {chars:6d}자")

# 통계
평균 = sum(r['chars'] for r in 글자수들) / len(글자수들)
최소 = min(r['chars'] for r in 글자수들)
최대 = max(r['chars'] for r in 글자수들)

print(f"\n{'=' * 100}")
print(f"통계 (20개 원고):")
print(f"  평균: {평균:.0f}자")
print(f"  최소: {최소}자")
print(f"  최대: {최대}자")
print(f"  중간값: {sorted([r['chars'] for r in 글자수들])[len(글자수들)//2]}자")

# 범위별 분포
print(f"\n글자수 범위별 분포:")
ranges = [(0, 200), (200, 300), (300, 400), (400, 500), (500, 600), (600, 1000), (1000, 2000)]
for start, end in ranges:
    count = sum(1 for r in 글자수들 if start <= r['chars'] < end)
    if count > 0:
        print(f"  {start:4d}~{end:4d}자: {count}개")


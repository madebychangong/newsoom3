#!/usr/bin/env python3
import pandas as pd

after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

print("C열 = 검수후 글자수 + ? 패턴 확인")
print("=" * 100)

for idx, row in after_df.iterrows():
    if idx >= 20:
        break
    
    keyword = row['키워드']
    c_value = row['글자수']
    text = row['원고']
    
    if pd.isna(text):
        continue
    
    # 제목 제거
    text_no_title = '\n'.join([line for line in text.split('\n') if not line.strip().startswith('#')])
    actual = len(text_no_title.replace(' ', '').replace('\n', ''))
    
    diff = c_value - actual
    
    print(f"[{idx+2}행] {keyword[:20]:20s} C={c_value:6d} 실제={actual:6d} 차이={diff:+6d}")


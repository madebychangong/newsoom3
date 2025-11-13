#!/usr/bin/env python3
"""전체 금칙어 리스트 확인"""
import pandas as pd

df = pd.read_excel('금칙어 리스트.xlsx', engine='openpyxl')

print('전체 금칙어 리스트:')
print('=' * 80)

all_words = []
for idx in range(len(df)):
    forbidden = df.iloc[idx]['Unnamed: 1']
    if pd.notna(forbidden) and str(forbidden).strip() != '' and forbidden != '금칙어':
        word = str(forbidden).strip()
        all_words.append(word)

        # 대체어도 출력
        replacements = []
        for col in df.columns[2:]:
            val = df.iloc[idx][col]
            if pd.notna(val) and val != '':
                replacements.append(str(val).strip())

        print(f'{len(all_words)}. "{word}" → {replacements}')

print(f'\n총 {len(all_words)}개 금칙어')

# 사용자가 필요한 금칙어 확인
print('\n' + '=' * 80)
print('사용자 원고에 필요한 금칙어 확인:')
print('=' * 80)
needed = ['산부인과', '부작용', '비용', '의구심', '홍보성', '병원', '진단', '의사', '환자', '재발', '대출', '의문', '의심']
for word in needed:
    if word in all_words:
        print(f'✅ "{word}" - 있음')
    else:
        print(f'❌ "{word}" - 없음!')

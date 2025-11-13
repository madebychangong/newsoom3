#!/usr/bin/env python3
"""
키워드가 원고 어디에서 카운팅되는지 확인
"""

import pandas as pd
import re


def find_keyword_positions(text, keyword):
    """키워드 위치와 컨텍스트 찾기"""
    # 띄어쓰기 기준 패턴
    pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'

    positions = []
    for match in re.finditer(pattern, text):
        pos = match.start()
        # 앞뒤 20자씩 컨텍스트
        start = max(0, pos - 20)
        end = min(len(text), pos + len(keyword) + 20)
        context = text[start:end]
        # 줄바꿈 표시
        context_display = context.replace('\n', '↵')
        positions.append({
            'pos': pos,
            'context': context_display,
            'keyword': keyword
        })

    return positions


# 엑셀 읽기
df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

# 8행 (관절에 좋은 차)
row = df.iloc[6]

keyword = row['키워드']
원고 = row['원고']

# 제목 제거
lines = [line for line in 원고.split('\n') if not line.strip().startswith('#')]
text_no_title = '\n'.join(lines)

# 첫 문단과 나머지
paragraphs = text_no_title.split('\n\n')
첫문단 = paragraphs[0] if paragraphs else ""
나머지 = '\n\n'.join(paragraphs[1:]) if len(paragraphs) > 1 else ""

print("=" * 100)
print(f"키워드: {keyword}")
print("=" * 100)

# 통 키워드 위치
print(f"\n통 키워드 '{keyword}' 위치:")
print("\n[첫 문단]")
positions = find_keyword_positions(첫문단, keyword)
for i, p in enumerate(positions, 1):
    print(f"  {i}. 위치 {p['pos']}: ...{p['context']}...")
print(f"  총 {len(positions)}개")

print("\n[나머지 부분]")
positions = find_keyword_positions(나머지, keyword)
for i, p in enumerate(positions, 1):
    print(f"  {i}. 위치 {p['pos']}: ...{p['context']}...")
print(f"  총 {len(positions)}개")

# 조각 키워드
조각키워드 = keyword.split()
for piece in 조각키워드:
    print(f"\n\n조각 키워드 '{piece}' 위치:")

    print("\n[첫 문단]")
    positions = find_keyword_positions(첫문단, piece)
    for i, p in enumerate(positions, 1):
        print(f"  {i}. 위치 {p['pos']}: ...{p['context']}...")
    print(f"  총 {len(positions)}개")

    print("\n[나머지 부분]")
    positions = find_keyword_positions(나머지, piece)
    for i, p in enumerate(positions, 1):
        print(f"  {i}. 위치 {p['pos']}: ...{p['context']}...")
    print(f"  총 {len(positions)}개")

print("\n\n" + "=" * 100)
print("원고 전체:")
print("=" * 100)
print(text_no_title)

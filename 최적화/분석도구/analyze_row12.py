#!/usr/bin/env python3
"""
12행 (수원여성병원) 심층 분석
C열 = 2505로 극단적으로 큼
"""

import pandas as pd

# 엑셀 읽기
before_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')
after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

# 12행 수원여성병원 (0-indexed: 10)
idx = 10

before_row = before_df.iloc[idx]
after_row = after_df.iloc[idx]

print("=" * 120)
print(f"12행 특이케이스 분석 - C열: {before_row['글자수']}")
print("=" * 120)

print(f"\n키워드: {before_row['키워드']}")
print(f"날짜: {before_row['날짜']}")
print(f"C열 글자수: {before_row['글자수']}")
print(f"D열 통키워드: {before_row['통키워드 반복수']}")
print(f"E열 조각키워드: {before_row['조각키워드 반복수']}")
print(f"F열 서브키워드: {before_row['서브키워드 목록 수']}")

# 원고 분석
before_text = before_row['원고']
after_text = after_row['원고']

# 제목 제거
before_no_title = '\n'.join([line for line in before_text.split('\n') if not line.strip().startswith('#')])
after_no_title = '\n'.join([line for line in after_text.split('\n') if not line.strip().startswith('#')])

print(f"\n원고 분석:")
before_chars1 = len(before_no_title.replace(' ', '').replace('\n', ''))
after_chars1 = len(after_no_title.replace(' ', '').replace('\n', ''))
before_chars2 = len(before_no_title.replace('\n', ''))
after_chars2 = len(after_no_title.replace('\n', ''))
print(f"  검수전 원고 길이 (공백/줄바꿈 제외): {before_chars1}")
print(f"  검수후 원고 길이 (공백/줄바꿈 제외): {after_chars1}")
print(f"  검수전 원고 길이 (공백 포함, 줄바꿈 제외): {before_chars2}")
print(f"  검수후 원고 길이 (공백 포함, 줄바꿈 제외): {after_chars2}")
print(f"  검수전 원고 길이 (전체): {len(before_no_title)}")
print(f"  검수후 원고 길이 (전체): {len(after_no_title)}")

# 문장 개수
before_sentences = len([s for s in before_no_title.split('.') if s.strip()])
after_sentences = len([s for s in after_no_title.split('.') if s.strip()])
print(f"\n  검수전 문장 개수 (.기준): {before_sentences}")
print(f"  검수후 문장 개수 (.기준): {after_sentences}")

# 줄 개수
before_lines = len([l for l in before_no_title.split('\n') if l.strip()])
after_lines = len([l for l in after_no_title.split('\n') if l.strip()])
print(f"\n  검수전 줄 개수: {before_lines}")
print(f"  검수후 줄 개수: {after_lines}")

# 단어 개수
before_words = len(before_no_title.split())
after_words = len(after_no_title.split())
print(f"\n  검수전 단어 개수 (공백 기준): {before_words}")
print(f"  검수후 단어 개수 (공백 기준): {after_words}")

# 2505와 관련있을만한 값들
print(f"\n\n2505와의 관계 찾기:")
print(f"  키워드 길이: {len(before_row['키워드'])}")
print(f"  키워드 길이 * 100: {len(before_row['키워드']) * 100}")
print(f"  검수전 글자수 * 3: {before_chars1 * 3}")
print(f"  검수후 글자수 * 2: {after_chars1 * 2}")
print(f"  검수후 글자수 + 1500: {after_chars1 + 1500}")

# 모든 다른 값들도 확인
print(f"\n\n다른 행들의 C열 분포:")
for i, row in before_df.iterrows():
    if i >= 20:
        break
    c = row['글자수']
    kw = row['키워드']
    print(f"  [{i+2}행] {kw[:20]:20s} C={c:6d}")

# 혹시 입력 오류?
print(f"\n\n혹시 입력 오류일까?")
print(f"  2505 / 10 = {2505 / 10}")
print(f"  2505 - 2000 = {2505 - 2000}")
print(f"  2505가 다른 의미의 숫자일 수도?")

# 원고 출력
print(f"\n\n{'=' * 120}")
print("검수후 원고 전체:")
print(f"{'=' * 120}")
print(after_no_title)

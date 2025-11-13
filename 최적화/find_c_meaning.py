#!/usr/bin/env python3
"""
C열 글자수의 의미를 찾기 위한 체계적 분석
모든 가능한 계산 방식 시도
"""

import pandas as pd

# 엑셀 읽기
before_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')
after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

print("=" * 120)
print("C열 의미 찾기 - 모든 가능한 계산 방식 시도")
print("=" * 120)

results = []

for idx in range(min(20, len(after_df))):
    row = after_df.iloc[idx]

    keyword = row['키워드']
    c_value = row['글자수']
    text = row['원고']

    if pd.isna(text):
        continue

    # 제목 제거
    lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
    text_no_title = '\n'.join(lines)

    # 첫 문단/나머지 분리
    paragraphs = text_no_title.split('\n\n')
    첫문단 = paragraphs[0] if paragraphs else ""
    나머지 = '\n\n'.join(paragraphs[1:]) if len(paragraphs) > 1 else ""

    # 다양한 계산
    계산값들 = {
        '전체_공백줄바꿈제외': len(text_no_title.replace(' ', '').replace('\n', '')),
        '전체_줄바꿈만제외': len(text_no_title.replace('\n', '')),
        '전체_포함': len(text_no_title),
        '첫문단_공백줄바꿈제외': len(첫문단.replace(' ', '').replace('\n', '')),
        '첫문단_줄바꿈만제외': len(첫문단.replace('\n', '')),
        '첫문단_포함': len(첫문단),
        '나머지_공백줄바꿈제외': len(나머지.replace(' ', '').replace('\n', '')),
        '나머지_줄바꿈만제외': len(나머지.replace('\n', '')),
        '나머지_포함': len(나머지),
        '문장수': len([s for s in text_no_title.split('.') if s.strip()]),
        '줄수': len([l for l in text_no_title.split('\n') if l.strip()]),
        '문단수': len(paragraphs),
        '단어수': len(text_no_title.split()),
        '키워드길이': len(keyword) if keyword else 0,
    }

    # 추가 조합 계산
    계산값들['문장수x10'] = 계산값들['문장수'] * 10
    계산값들['문장수x20'] = 계산값들['문장수'] * 20
    계산값들['문장수x30'] = 계산값들['문장수'] * 30
    계산값들['줄수x10'] = 계산값들['줄수'] * 10
    계산값들['줄수x20'] = 계산값들['줄수'] * 20
    계산값들['줄수x30'] = 계산값들['줄수'] * 30
    계산값들['문단수x100'] = 계산값들['문단수'] * 100
    계산값들['단어수x2'] = 계산값들['단어수'] * 2
    계산값들['단어수x3'] = 계산값들['단어수'] * 3

    # C열과 가장 가까운 값 찾기
    차이들 = {name: abs(c_value - value) for name, value in 계산값들.items()}
    최소차이_이름 = min(차이들, key=차이들.get)
    최소차이_값 = 차이들[최소차이_이름]

    results.append({
        'row': idx + 2,
        'keyword': keyword,
        'c_value': c_value,
        '가장가까운': 최소차이_이름,
        '계산값': 계산값들[최소차이_이름],
        '차이': 최소차이_값,
        **계산값들
    })

# DataFrame으로 변환
df_results = pd.DataFrame(results)

# 가장 자주 일치하는 계산 방식 찾기
print("\n각 계산 방식별 일치도 (차이 10 이내):")
print("-" * 120)

계산방식들 = [k for k in results[0].keys() if k not in ['row', 'keyword', 'c_value', '가장가까운', '계산값', '차이']]

for 방식 in 계산방식들:
    일치개수 = sum(1 for r in results if abs(r['c_value'] - r[방식]) <= 10)
    평균차이 = sum(abs(r['c_value'] - r[방식]) for r in results) / len(results)
    print(f"  {방식:25s}: {일치개수}/20 일치 (평균차이: {평균차이:6.1f})")

# 가장 많이 일치하는 방식
최고_방식 = max(계산방식들, key=lambda x: sum(1 for r in results if abs(r['c_value'] - r[x]) <= 10))
최고_일치개수 = sum(1 for r in results if abs(r['c_value'] - r[최고_방식]) <= 10)

print(f"\n{'=' * 120}")
print(f"✅ 가장 일치율 높은 방식: {최고_방식} ({최고_일치개수}/20 = {최고_일치개수/20*100:.1f}%)")
print(f"{'=' * 120}")

# 상세 결과 (일치하지 않는 것들만)
print(f"\n일치하지 않는 행들 ({최고_방식} 기준):")
print("-" * 120)
for r in results:
    차이 = abs(r['c_value'] - r[최고_방식])
    if 차이 > 10:
        print(f"[{r['row']}행] {r['keyword']:20s} C={r['c_value']:6d} {최고_방식}={r[최고_방식]:6d} 차이={차이:6.0f}")

# 혹시 C열이 검수전 원고의 어떤 값일까?
print(f"\n\n{'=' * 120}")
print("검수전 원고도 확인:")
print(f"{'=' * 120}")

검수전_results = []
for idx in range(min(20, len(before_df))):
    row = before_df.iloc[idx]

    keyword = row['키워드']
    c_value = row['글자수']
    text = row['원고']

    if pd.isna(text):
        continue

    # 제목 제거
    lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
    text_no_title = '\n'.join(lines)

    검수전_전체 = len(text_no_title.replace(' ', '').replace('\n', ''))

    검수전_results.append({
        'row': idx + 2,
        'c_value': c_value,
        '검수전_전체': 검수전_전체,
        '차이': abs(c_value - 검수전_전체)
    })

검수전_일치 = sum(1 for r in 검수전_results if r['차이'] <= 10)
print(f"검수전 전체 글자수와 일치: {검수전_일치}/20")

# 불일치하는 것들
if 검수전_일치 < 20:
    print(f"\n검수전과도 일치하지 않는 행들:")
    for r in 검수전_results:
        if r['차이'] > 10:
            print(f"  [{r['row']}행] C={r['c_value']:6d} 검수전={r['검수전_전체']:6d} 차이={r['차이']:6.0f}")

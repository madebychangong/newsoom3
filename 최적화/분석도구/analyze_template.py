#!/usr/bin/env python3
"""템플릿 파일 상세 분석 - 검수전/검수후 비교"""

import pandas as pd
import re

# 파일 읽기
df_before = pd.read_excel('/home/user/blogm/블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')
df_after = pd.read_excel('/home/user/blogm/블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

print("=" * 80)
print("템플릿 분석: 검수전 → 검수 후")
print("=" * 80)

# 각 원고 비교
for idx in range(min(3, len(df_before))):  # 처음 3개만
    keyword = df_before.iloc[idx]['키워드']
    text_before = df_before.iloc[idx]['원고']
    text_after = df_after.iloc[idx]['원고']

    print(f"\n{'=' * 80}")
    print(f"[{idx+1}번] 키워드: {keyword}")
    print('=' * 80)

    # 1. # 제목 확인
    if text_before.strip().startswith('#'):
        print("✅ # 제목 삭제됨")
        print(f"   원본: {text_before.split(chr(10))[0][:50]}...")

    # 2. 키워드 출현 횟수
    count_before = text_before.count(keyword)
    count_after = text_after.count(keyword)
    print(f"\n📊 키워드 출현:")
    print(f"   검수전: {count_before}회")
    print(f"   검수 후: {count_after}회")
    if count_before != count_after:
        print(f"   → {count_before - count_after}회 감소 ✅")

    # 3. "네요" 패턴 확인
    neyo_before = text_before.count('네요')
    neyo_after = text_after.count('네요')
    if neyo_before > 0 or neyo_after > 0:
        print(f"\n💬 '네요' 패턴:")
        print(f"   검수전: {neyo_before}개")
        print(f"   검수 후: {neyo_after}개")
        if neyo_before > neyo_after:
            print(f"   → {neyo_before - neyo_after}개 치환됨 ✅")

    # 4. "더라구요" 패턴 확인
    deola_before = text_before.count('더라구요')
    deola_after = text_after.count('더라구요')
    if deola_before > 0 or deola_after > 0:
        print(f"\n💬 '더라구요' 패턴:")
        print(f"   검수전: {deola_before}개")
        print(f"   검수 후: {deola_after}개")
        if deola_before == deola_after:
            print(f"   → 유지됨 (금칙어 아님)")

    # 5. 키워드+조사 패턴 찾기
    particles = ['를', '을', '가', '이', '에', '의', '는', '은']
    print(f"\n🔧 키워드+조사 변화:")
    for p in particles:
        pattern = f'{keyword}{p}'
        if pattern in text_before:
            if pattern not in text_after:
                print(f"   '{keyword}{p}' → 제거 또는 수정됨 ✅")

    # 6. 금칙어 치환 찾기
    print(f"\n🚫 금칙어 치환:")

    # 효과 → 약효
    if '효과' in text_before and '약효' in text_after and text_after.count('약효') > text_before.count('약효'):
        print(f"   '효과' → '약효'")

    # 병원 관련
    if '병원' in text_before:
        if '병원' not in text_after or text_after.count('병원') < text_before.count('병원'):
            print(f"   '병원' → 치환됨")

    # 광고 관련
    if '광고' in text_before:
        if '광고' not in text_after or text_after.count('광고') < text_before.count('광고'):
            print(f"   '광고' → 치환됨")

    # 진단 관련
    if '진단' in text_before:
        if '진단' not in text_after or text_after.count('진단') < text_before.count('진단'):
            print(f"   '진단' → 치환됨")

print("\n" + "=" * 80)
print("분석 완료")
print("=" * 80)

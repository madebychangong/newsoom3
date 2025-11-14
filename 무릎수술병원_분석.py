#!/usr/bin/env python3
"""
무릎 수술 병원 원고 분석
"""

import re
from collections import Counter

manuscript = """# 무릎 수술 병원에 대해 고민 중인데, 경험 있으신 분 계신가요?

무릎 수술 병원을 알아보게 된 건 정말 우연이었어요.
무릎 수술 병원이라는 말을 친구들 모임에서 처음 들었는데, 저처럼 무릎 통증으로 고생하는 사람들이 많더라고요.
사실 저는 50대 중반인데 벌써 계단 오르내리는 게 고문같이 느껴져요.

의자에서 일어날 때마다 ""아이고, 아이고"" 소리가 절로 나오고,
예전에는 즐기던 산책이나 등산은 이제 꿈도 못 꿔요.
가족들과 여행 가서도 다들 구경하러 다닐 때 저만 벤치에 앉아 쉬어야 하니 미안하고 속상하죠.
나이 들수록 더 심해질까봐 정말 두려워요.

동네 정형외과에서 연골 주사도 맞아봤는데 일시적으로만 좋아지고 금방 다시 아프더라고요.
글루코사민, MSM, 보스웰리아 같은 관절 영양제들도 이것저것 먹어봤지만 별 차이를 못 느꼈어요.
물리치료도 받아봤는데 매번 가기가 너무 번거로워서 중단했죠.

그러다 친구가 어머니 때문에 서울 대학병원에서 수술 받으셨다는 얘기를 해줬어요.
72세 어머니가 말기 퇴행성 무릎관절증으로 인공관절 수술을 받으셨대요.
관절 전문 병원들이 많이 있는데, 서울 소재 대학병원이 선호된다고 하더라고요.

근데 막상 저도 알아보려니 어디서부터 시작해야 할지 모르겠어요.
수술까지 가기엔 아직 이른 것 같기도 하고,
재활 과정도 만만치 않다는데 걱정이 앞서네요.

혹시 무릎 수술 병원에서 치료받아보신 분 계신가요?
수술 말고도 다른 치료 옵션이 있는지도 궁금해요.
정말 효과 보신 치료법이나 관리 방법 있으면 꼭 알려주세요."""

keyword = "무릎 수술 병원"

# 제목 제거
lines = [line for line in manuscript.split('\n') if not line.strip().startswith('#')]
text_no_title = '\n'.join(lines)

# 첫 문단 추출
paragraphs = text_no_title.split('\n\n')
첫문단 = paragraphs[0].strip()
나머지 = '\n\n'.join(paragraphs[1:]).strip()

print("=" * 100)
print("📊 원고 분석 - 무릎 수술 병원")
print("=" * 100)

# 1. 글자수
chars = len(text_no_title.replace(' ', '').replace('\n', ''))
r1 = 300 <= chars <= 900
print(f"\n1️⃣ 글자수: {chars}자 {'✅' if r1 else '❌'} (목표: 300~900)")

# 2. 첫문단 통키워드
pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
첫문단_count = len(re.findall(pattern, 첫문단))
r2 = 첫문단_count == 2
print(f"2️⃣ 첫문단 통키워드: {첫문단_count}회 {'✅' if r2 else '❌'} (목표: 정확히 2)")

if 첫문단_count > 0:
    print(f"   발견된 위치:")
    matches = list(re.finditer(pattern, 첫문단))
    for i, match in enumerate(matches, 1):
        start = max(0, match.start()-20)
        end = min(len(첫문단), match.end()+20)
        context = 첫문단[start:end]
        print(f"   {i}번째: ...{context}...")

# 3. 키워드로 시작하는 문장
sentences = []
for line in text_no_title.split('\n'):
    line = line.strip()
    if line:
        parts = re.split(r'([.!?])\s*', line)
        current = ""
        for i, part in enumerate(parts):
            if part in '.!?':
                current += part
                if current.strip():
                    sentences.append(current.strip())
                current = ""
            else:
                current += part
        if current.strip():
            sentences.append(current.strip())

문장시작_count = sum(1 for s in sentences if s.startswith(keyword))
r3 = 문장시작_count == 2
print(f"\n3️⃣ 키워드로 시작하는 문장: {문장시작_count}개 {'✅' if r3 else '❌'} (목표: 정확히 2)")
if 문장시작_count > 0:
    print(f"   발견된 문장:")
    for s in sentences:
        if s.startswith(keyword):
            print(f"   - {s[:70]}...")

# 4. 첫문단 키워드 사이 문장수
첫문단_sentences = re.split(r'[.,]\s*', 첫문단)
첫문단_sentences = [s.strip() for s in 첫문단_sentences if s.strip()]

keyword_indices = []
for i, sentence in enumerate(첫문단_sentences):
    if re.search(pattern, sentence):
        keyword_indices.append(i)

if len(keyword_indices) >= 2:
    사이문장수 = keyword_indices[1] - keyword_indices[0] - 1
else:
    사이문장수 = 0

r4 = 사이문장수 >= 2
print(f"\n4️⃣ 첫문단 키워드 사이 문장: {사이문장수}개 {'✅' if r4 else '❌'} (목표: 최소 2)")

# 5. 나머지 통키워드
나머지_통 = len(re.findall(pattern, 나머지))
r5 = 나머지_통 >= 0  # 목표: 0 이상
print(f"\n5️⃣ 나머지 통키워드: {나머지_통}회 {'✅' if r5 else '❌'} (목표: 0 이상)")

# 6. 조각키워드
조각_무릎 = len(re.findall(r'무릎(?=\s|[^\w가-힣]|$)', 나머지))
조각_수술 = len(re.findall(r'수술(?=\s|[^\w가-힣]|$)', 나머지))
조각_병원 = len(re.findall(r'병원(?=\s|[^\w가-힣]|$)', 나머지))

r6 = 조각_무릎 >= 0 and 조각_수술 >= 2 and 조각_병원 >= 1
print(f"\n6️⃣ 조각키워드:")
print(f"   - 무릎: {조각_무릎}회 (목표: 0 이상) {'✅' if 조각_무릎 >= 0 else '❌'}")
print(f"   - 수술: {조각_수술}회 (목표: 2 이상) {'✅' if 조각_수술 >= 2 else '❌'}")
print(f"   - 병원: {조각_병원}회 (목표: 1 이상) {'✅' if 조각_병원 >= 1 else '❌'}")

# 7. 서브키워드
words = re.findall(r'[가-힣]+', text_no_title)
word_counter = Counter(words)
exclude = ['무릎', '수술', '병원']
subkeywords = set()
for word, count in word_counter.items():
    if count >= 2 and len(word) >= 2 and word not in exclude:
        subkeywords.add(word)

r7 = len(subkeywords) >= 5
print(f"\n7️⃣ 서브키워드: {len(subkeywords)}개 {'✅' if r7 else '❌'} (목표: 5 이상)")
if len(subkeywords) > 0:
    print(f"   발견된 서브키워드 (2회 이상): {sorted(list(subkeywords)[:15])}")

# 최종 결과
all_ok = all([r1, r2, r3, r4, r5, r6, r7])

print(f"\n{'=' * 100}")
print(f"📋 검수 결과 요약")
print(f"{'=' * 100}")

if all_ok:
    print(f"\n🎉 모든 규칙 충족! (7/7)")
else:
    passed = sum([r1, r2, r3, r4, r5, r6, r7])
    print(f"\n⚠️ {passed}/7 규칙 충족")

    issues = []
    if not r1:
        if chars < 300:
            issues.append(f"글자수 부족: {300-chars}자 더 필요 (현재 {chars}자)")
        else:
            issues.append(f"글자수 초과: {chars-900}자 줄여야 함 (현재 {chars}자)")
    if not r2:
        issues.append(f"첫문단 통키워드: {2-첫문단_count}개 {'더 필요' if 첫문단_count < 2 else '줄여야 함'} (현재 {첫문단_count}회)")
    if not r3:
        issues.append(f"키워드로 시작하는 문장: {2-문장시작_count}개 {'더 필요' if 문장시작_count < 2 else '줄여야 함'} (현재 {문장시작_count}개)")
    if not r4:
        issues.append(f"첫문단 키워드 사이 문장: {2-사이문장수}개 더 필요 (현재 {사이문장수}개)")
    if not r5:
        issues.append(f"나머지 통키워드 문제")
    if not r6:
        if 조각_무릎 < 0:
            issues.append(f"나머지 '무릎': {0-조각_무릎}개 더 필요")
        if 조각_수술 < 2:
            issues.append(f"나머지 '수술': {2-조각_수술}개 더 필요")
        if 조각_병원 < 1:
            issues.append(f"나머지 '병원': {1-조각_병원}개 더 필요")
    if not r7:
        issues.append(f"서브키워드: {5-len(subkeywords)}개 더 필요 (현재 {len(subkeywords)}개)")

    print(f"\n🔧 수정 필요 사항:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")

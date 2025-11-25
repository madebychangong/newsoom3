#!/usr/bin/env python3

import re
from collections import Counter

manuscript = """# 팔꿈치 쿠션 보호대 관련해서 사용해보신 분 계신가요?

무릎이 아프기 시작한 게 벌써 몇 달째예요. 의자에서 일어날 때마다 힘들고 계단도 오르기 어렵습니다. 팔꿈치 쿠션 보호대 알아보는 중인데요. 주변에서 추천받았거든요. 근데 검색하니까 종류도 많고 가격도 천차만별이더라구요. 팔꿈치 쿠션 보호대 써보신 분들 계시면 후기 알려주세요.

연골 주사도 맞아봤고 물리치료도 받아봤는데 일시적이었어요. 영양제는 꾸준히 먹는 중입니다.

지인이 보호대 하나 써보라고 하더라구요. 부담 없이 시작할 수 있다고 해서 관심 생겼습니다.

어떤 제품 쓰시는지 알려주시면 감사하겠습니다."""

keyword = "팔꿈치 쿠션 보호대"

lines = [line for line in manuscript.split('\n') if not line.strip().startswith('#')]
text_no_title = '\n'.join(lines)
paragraphs = text_no_title.split('\n\n')
첫문단 = paragraphs[0].strip()
나머지 = '\n\n'.join(paragraphs[1:]).strip()

print("=" * 100)
print("🎯 최종 검증")
print("=" * 100)

# 1. 글자수
chars = len(text_no_title.replace(' ', '').replace('\n', ''))
r1 = 300 <= chars <= 900
print(f"\n1️⃣ 글자수: {chars}자 {'✅' if r1 else '❌'} (목표: 300~900)")

# 2. 첫 문단 통키워드
pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
첫문단_count = len(re.findall(pattern, 첫문단))
r2 = 첫문단_count == 2
print(f"2️⃣ 첫 문단 통키워드: {첫문단_count}회 {'✅' if r2 else '❌'} (목표: 정확히 2)")

# 3. 문장 시작
sentences = []
for line in text_no_title.split('\n'):
    line = line.strip()
    if line:
        parts = re.split(r'([.!?])\s*', line)
        current = ""
        for part in parts:
            if part in '.!?':
                current += part
                if current.strip():
                    sentences.append(current.strip())
                current = ""
            else:
                current += part
        if current.strip():
            sentences.append(current.strip())

문장시작 = sum(1 for s in sentences if s.startswith(keyword))
r3 = 문장시작 == 2
print(f"3️⃣ 키워드로 시작 문장: {문장시작}개 {'✅' if r3 else '❌'} (목표: 정확히 2)")

# 4. 키워드 사이 문장
첫문단_sentences = re.split(r'[.,]\s*', 첫문단)
첫문단_sentences = [s.strip() for s in 첫문단_sentences if s.strip()]
keyword_indices = [i for i, s in enumerate(첫문단_sentences) if re.search(pattern, s)]
사이문장 = keyword_indices[1] - keyword_indices[0] - 1 if len(keyword_indices) >= 2 else 0
r4 = 사이문장 >= 2
print(f"4️⃣ 키워드 사이 문장: {사이문장}개 {'✅' if r4 else '❌'} (목표: 최소 2)")

# 5. 나머지 통키워드
나머지_통 = len(re.findall(pattern, 나머지))
r5 = 나머지_통 == 0
print(f"5️⃣ 나머지 통키워드: {나머지_통}회 {'✅' if r5 else '❌'} (목표: 0)")

# 6. 조각키워드
조각_팔꿈치 = len(re.findall(r'팔꿈치(?=\s|[^\w가-힣]|$)', 나머지))
조각_쿠션 = len(re.findall(r'쿠션(?=\s|[^\w가-힣]|$)', 나머지))
조각_보호대 = len(re.findall(r'보호대(?=\s|[^\w가-힣]|$)', 나머지))
r6 = 조각_팔꿈치 == 0 and 조각_쿠션 == 0 and 조각_보호대 == 1
print(f"6️⃣ 조각키워드: 팔꿈치 {조각_팔꿈치}, 쿠션 {조각_쿠션}, 보호대 {조각_보호대} {'✅' if r6 else '❌'} (목표: 0,0,1)")

# 7. 서브키워드
words = re.findall(r'[가-힣]+', text_no_title)
word_counter = Counter(words)
exclude = ['팔꿈치', '쿠션', '보호대']
subkeywords = {w for w, c in word_counter.items() if c >= 2 and len(w) >= 2 and w not in exclude}
r7 = len(subkeywords) == 0
print(f"7️⃣ 서브키워드: {len(subkeywords)}개 {'✅' if r7 else '❌'} (목표: 0)")
if subkeywords:
    print(f"   발견: {sorted(list(subkeywords)[:10])}")

all_ok = all([r1, r2, r3, r4, r5, r6, r7])

print(f"\n{'=' * 100}")
if all_ok:
    print("🎉 완벽! 모든 규칙 충족 (7/7)")
else:
    failed = sum([not r1, not r2, not r3, not r4, not r5, not r6, not r7])
    print(f"⚠️ {7-failed}/7 규칙 충족 (미달 {failed}개)")

print(f"{'=' * 100}\n")
print(manuscript)

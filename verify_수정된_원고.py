#!/usr/bin/env python3
"""
수정된 원고 검증
"""

import re
from collections import Counter

manuscript = """# 팔꿈치 쿠션 보호대 관련해서 사용해보신 분 계신가요?

무릎 통증으로 고생하고 있는 50대입니다. 의자에서 일어날 때마다 "아이고" 소리가 절로 나올 정도로 힘들어요. 팔꿈치 쿠션 보호대 관련해서 최근에 알게 되었는데요. 이것저것 검색해봤는데 정보가 너무 많아서 헷갈리네요. 팔꿈치 쿠션 보호대 사용해보신 분 계시면 경험담 좀 들려주실 수 있을까요?

계단 오르내릴 때는 정말 고문 같습니다. 예전에는 산책이나 등산도 즐겼는데 이제는 엄두도 못 내겠어요. 나이가 들수록 더 심해질까봐 불안합니다.

유명하다는 정형외과에서 비싼 연골 주사도 맞아봤는데 효과가 일시적이라 실망이 컸어요. 영양제도 꾸준히 먹어봤지만 솔직히 큰 차이를 못 느끼겠더라구요. 물리치료도 받아봤는데 매번 다니기가 너무 번거로워서 중단했습니다.

이런 상황에서 지인들과 대화하다가 보호대 얘기가 나왔어요. 단순한 영양제랑 뭐가 다른지도 궁금하고 정말 효과가 있는 건지 의심스럽기도 해요.

솔직한 경험담 좀 들려주실 수 있을까요? 효과를 보신 제품이 있다면 추천도 부탁드립니다. 정말 예전처럼 편하게 걷고 싶은 마음이 간절합니다."""

keyword = "팔꿈치 쿠션 보호대"

# 제목 제거
lines = [line for line in manuscript.split('\n') if not line.strip().startswith('#')]
text_no_title = '\n'.join(lines)

# 첫 문단 추출
paragraphs = text_no_title.split('\n\n')
첫문단 = paragraphs[0].strip()
나머지 = '\n\n'.join(paragraphs[1:]).strip()

print("=" * 100)
print("✅ 수정된 원고 검증")
print("=" * 100)

# 글자수
chars = len(text_no_title.replace(' ', '').replace('\n', ''))
print(f"\n1️⃣ 글자수: {chars}자 (목표: 300~900자) {'✅' if 300 <= chars <= 900 else '❌'}")

# 첫 문단에서 통키워드 카운팅
pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
첫문단_count = len(re.findall(pattern, 첫문단))
print(f"\n2️⃣ 첫 문단 통키워드: {첫문단_count}회 (목표: 정확히 2회) {'✅' if 첫문단_count == 2 else '❌'}")

# 첫 문단에서 발견된 키워드 위치
matches = list(re.finditer(pattern, 첫문단))
if matches:
    print(f"   발견된 키워드:")
    for i, match in enumerate(matches, 1):
        start = max(0, match.start()-15)
        end = min(len(첫문단), match.end()+15)
        context = 첫문단[start:end]
        print(f"   {i}번째: ...{context}...")

# 문장 시작하는 개수
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
print(f"\n3️⃣ 키워드로 시작하는 문장: {문장시작_count}개 (목표: 정확히 2개) {'✅' if 문장시작_count == 2 else '❌'}")
if 문장시작_count > 0:
    print(f"   발견된 문장:")
    for s in sentences:
        if s.startswith(keyword):
            print(f"   - {s[:60]}...")

# 첫 문단 키워드 사이 문장수
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

print(f"\n4️⃣ 첫 문단 키워드 사이 문장수: {사이문장수}개 (목표: 최소 2개) {'✅' if 사이문장수 >= 2 else '❌'}")
if len(keyword_indices) >= 2:
    print(f"   첫 번째 키워드: 문장 {keyword_indices[0]+1}")
    print(f"   두 번째 키워드: 문장 {keyword_indices[1]+1}")
    print(f"   사이 문장: {사이문장수}개")

# 나머지 부분 통키워드
나머지_통키워드_count = len(re.findall(pattern, 나머지))
print(f"\n5️⃣ 나머지 부분 통키워드: {나머지_통키워드_count}회 (목표: 0회) {'✅' if 나머지_통키워드_count == 0 else '❌'}")

# 나머지 부분 조각키워드
조각_팔꿈치 = len(re.findall(r'팔꿈치(?=\s|[^\w가-힣]|$)', 나머지))
조각_쿠션 = len(re.findall(r'쿠션(?=\s|[^\w가-힣]|$)', 나머지))
조각_보호대 = len(re.findall(r'보호대(?=\s|[^\w가-힣]|$)', 나머지))

print(f"\n6️⃣ 나머지 부분 조각키워드:")
print(f"   - 팔꿈치: {조각_팔꿈치}회 (목표: 0회) {'✅' if 조각_팔꿈치 == 0 else '❌'}")
print(f"   - 쿠션: {조각_쿠션}회 (목표: 0회) {'✅' if 조각_쿠션 == 0 else '❌'}")
print(f"   - 보호대: {조각_보호대}회 (목표: 1회) {'✅' if 조각_보호대 == 1 else '❌'}")

# 서브키워드
words = re.findall(r'[가-힣]+', text_no_title)
word_counter = Counter(words)
subkeywords = set()
exclude = ['팔꿈치', '쿠션', '보호대']
for word, count in word_counter.items():
    if count >= 2 and len(word) >= 2 and word not in exclude:
        subkeywords.add(word)

print(f"\n7️⃣ 서브키워드 목록: {len(subkeywords)}개 (목표: 0개) {'✅' if len(subkeywords) == 0 else '❌'}")
if len(subkeywords) > 0:
    print(f"   발견된 서브키워드 (2회 이상): {sorted(list(subkeywords)[:15])}")

# 최종 검수
all_ok = (
    300 <= chars <= 900 and
    첫문단_count == 2 and
    문장시작_count == 2 and
    사이문장수 >= 2 and
    나머지_통키워드_count == 0 and
    조각_팔꿈치 == 0 and
    조각_쿠션 == 0 and
    조각_보호대 == 1 and
    len(subkeywords) == 0
)

print(f"\n" + "=" * 100)
print(f"📋 최종 검수 결과")
print(f"=" * 100)

if all_ok:
    print(f"\n🎉 모든 규칙 충족! (7/7)")
    print(f"   ✅ 글자수 OK")
    print(f"   ✅ 첫문단 통키워드 2회 OK")
    print(f"   ✅ 문장 시작 2개 OK")
    print(f"   ✅ 키워드 사이 문장 OK")
    print(f"   ✅ 나머지 통키워드 0회 OK")
    print(f"   ✅ 조각키워드 OK")
    print(f"   ✅ 서브키워드 0개 OK")
else:
    issues = []
    if not (300 <= chars <= 900):
        issues.append(f"글자수 {chars}자")
    if 첫문단_count != 2:
        issues.append(f"첫문단 통키워드 {첫문단_count}회")
    if 문장시작_count != 2:
        issues.append(f"문장 시작 {문장시작_count}개")
    if 사이문장수 < 2:
        issues.append(f"키워드 사이 문장 {사이문장수}개")
    if 나머지_통키워드_count != 0:
        issues.append(f"나머지 통키워드 {나머지_통키워드_count}회")
    if 조각_팔꿈치 != 0:
        issues.append(f"나머지 '팔꿈치' {조각_팔꿈치}회")
    if 조각_쿠션 != 0:
        issues.append(f"나머지 '쿠션' {조각_쿠션}회")
    if 조각_보호대 != 1:
        issues.append(f"나머지 '보호대' {조각_보호대}회")
    if len(subkeywords) != 0:
        issues.append(f"서브키워드 {len(subkeywords)}개")

    print(f"\n⚠️ 일부 규칙 미충족 ({len(issues)}개):")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")

print(f"\n" + "=" * 100)
print(f"📝 수정된 원고 전문")
print(f"=" * 100)
print(manuscript)

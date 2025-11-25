#!/usr/bin/env python3

import re
from collections import Counter

manuscript = """# 무릎 수술 병원에 대해 고민 중인데, 경험 있으신 분 계신가요?

50대 중반인데 무릎이 너무 아파서 힘듭니다. 계단 오르내리는 게 고문같이 느껴지고 의자에서 일어날 때마다 아이고 소리가 절로 나와요. 무릎 수술 병원 알아보는 중인데요. 주변에서 관절 전문의 얘기를 많이 들었거든요. 검색해보니까 서울에 있는 곳들이 많더라구요. 무릎 수술 병원 다녀보신 분들 계시면 경험담 좀 들려주세요.

동네 정형외과에서 연골 주사도 맞아봤는데 일시적으로만 좋아지고 금방 다시 아프더라고요. 글루코사민 같은 영양제들도 먹어봤지만 별 차이를 못 느꼈어요. 물리치료도 받아봤는데 매번 가기가 번거로워서 중단했죠. 무릎 통증이 계속되니 일상생활이 힘들더라구요.

친구 어머니가 72세인데 말기 퇴행성 관절염으로 인공관절 수술 받으셨대요. 적합한 무릎 수술 병원 찾는 과정이 쉽지 않았다고 하더라구요. 서울에 있는 전문 센터에서 치료 받으셨는데 지금은 많이 좋아지셨답니다. 전문 센터 선택이 정말 중요하다고 강조하시더군요.

근데 막상 알아보려니 어디서부터 시작해야 할지 모르겠어요. 수술까지 가기엔 아직 이른 것 같기도 하고 재활 과정도 만만치 않다는데 걱정이 앞서네요. 과정 자체가 처음이라 더 막막합니다.

혹시 치료받아보신 분 계신가요? 실제로 경험해보신 분들의 이야기가 듣고 싶어요. 수술 말고도 다른 치료 옵션이 있는지도 궁금해요. 정말 효과 보신 치료법이나 관리 방법 있으면 꼭 알려주세요. 경험담 부탁드립니다."""

keyword = "무릎 수술 병원"

lines = [line for line in manuscript.split('\n') if not line.strip().startswith('#')]
text_no_title = '\n'.join(lines)
paragraphs = text_no_title.split('\n\n')
첫문단 = paragraphs[0].strip()
나머지 = '\n\n'.join(paragraphs[1:]).strip()

print("=" * 100)
print("🎯 무릎 수술 병원 - 최종 검증")
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

# 5. 나머지 통키워드 (목표: 1 이상)
나머지_통 = len(re.findall(pattern, 나머지))
target_나머지_통 = 1
r5 = 나머지_통 >= target_나머지_통
print(f"5️⃣ 나머지 통키워드: {나머지_통}회 {'✅' if r5 else '❌'} (목표: {target_나머지_통} 이상)")

# 6. 조각키워드 (목표: 무릎 1+, 수술 3+, 병원 1+)
조각_무릎 = len(re.findall(r'무릎(?=\s|[^\w가-힣]|$)', 나머지))
조각_수술 = len(re.findall(r'수술(?=\s|[^\w가-힣]|$)', 나머지))
조각_병원 = len(re.findall(r'병원(?=\s|[^\w가-힣]|$)', 나머지))
r6 = 조각_무릎 >= 1 and 조각_수술 >= 3 and 조각_병원 >= 1
print(f"6️⃣ 조각키워드: 무릎 {조각_무릎} (목표 1+), 수술 {조각_수술} (목표 3+), 병원 {조각_병원} (목표 1+) {'✅' if r6 else '❌'}")

# 7. 서브키워드 (목표: 5개 이상)
words = re.findall(r'[가-힣]+', text_no_title)
word_counter = Counter(words)
exclude = ['무릎', '수술', '병원']
subkeywords = {w for w, c in word_counter.items() if c >= 2 and len(w) >= 2 and w not in exclude}
target_서브 = 5
r7 = len(subkeywords) >= target_서브
print(f"7️⃣ 서브키워드: {len(subkeywords)}개 {'✅' if r7 else '❌'} (목표: {target_서브} 이상)")
if subkeywords:
    print(f"   발견: {sorted(list(subkeywords)[:15])}")

all_ok = all([r1, r2, r3, r4, r5, r6, r7])

print(f"\n{'=' * 100}")
if all_ok:
    print("🎉 완벽! 모든 규칙 충족 (7/7)")
else:
    passed = sum([r1, r2, r3, r4, r5, r6, r7])
    print(f"⚠️ {passed}/7 규칙 충족 (미달 {7-passed}개)")

print(f"{'=' * 100}\n")

#!/usr/bin/env python3
"""카운팅 로직 테스트"""

import re

def count_keyword(text: str, keyword: str) -> int:
    """키워드 카운팅 (띄어쓰기 기준)"""
    if not keyword:
        return 0
    pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
    matches = re.findall(pattern, text)
    return len(matches)

def get_first_paragraph(text: str) -> str:
    """첫 문단 추출"""
    lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
    text_no_title = '\n'.join(lines)
    paragraphs = text_no_title.split('\n\n')
    return paragraphs[0].strip() if paragraphs else ""

def count_sentences_starting_with(text: str, keyword: str) -> int:
    """키워드로 시작하는 문장(줄) 개수"""
    if not keyword:
        return 0
    count = 0
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith(keyword):
            count += 1
    return count

# 테스트 원고 (사용자가 보여준 것)
manuscript = """잠실유방외과에 대해 궁금한 점이 있어 글을 올립니다. 저는 최근 갱년기 증상으로 힘든 시간을 보내고 있는데, 잠실유방외과에서 이와 관련된 상담을 진행한다고 들었습니다. 50대 초반 주부인 저는 작년부터 갑작스러운 열감과 감정 기복으로 일상생활에 어려움을 겪고 있습니다.

잠실유방외과 관련해서 알아보다가, 실제로 갱년기 증상 완화에 도움을 받으신 분들의 경험담을 듣고 싶어 이렇게 글을 남깁니다. 처음에는 단순한 노화 현상으로 생각했지만, 밤에 잠을 제대로 이루지 못하고 사소한 일에도 쉽게 짜증이 나는 등 증상이 심해지면서 가족들에게 미안한 마음이 듭니다. 산부인과에서 호르몬 치료 상담을 받았지만, 부작용에 대한 우려 때문에 쉽게 결정을 내리지 못하고 있습니다. 칡즙이나 석류즙 같은 건강식품도 꾸준히 섭취했지만, 뚜렷한 효과를 보지 못했습니다.

그러던 중 친구가 잠실유방외과 이야기를 해주었는데, 솔직히 건강기능식품에 대한 의구심이 드는 것도 사실입니다. 잠실유방외과 후기를 찾아보면 너무 많은 정보가 쏟아져 나와 어떤 것을 믿어야 할지 혼란스럽습니다. 혹시 잠실유방외과에서 갱년기 관련 상담이나 치료를 받아보신 분이 있다면, 솔직한 경험담을 공유해주시면 감사하겠습니다. 어떤 점이 좋았는지, 실제로 효과를 보셨는지 알고 싶습니다.
잠실유방외과 관련해서 다른 갱년기 증상 완화에 도움이 될 만한 방법이나 제품이 있다면 추천 부탁드립니다."""

keyword = "잠실유방외과"

# 첫 문단 추출
first_para = get_first_paragraph(manuscript)
rest_para = manuscript.replace(first_para, '', 1).strip()

print("=" * 80)
print("첫 문단:")
print("=" * 80)
print(first_para)
print()

print("=" * 80)
print("나머지:")
print("=" * 80)
print(rest_para)
print()

# 카운팅
first_para_count = count_keyword(first_para, keyword)
sentence_start_count = count_sentences_starting_with(manuscript, keyword)

print("=" * 80)
print("검증 결과:")
print("=" * 80)
print(f"첫문단 '{keyword}' 카운팅: {first_para_count}회 (목표: 2회)")
print(f"'{keyword}'로 시작하는 문장: {sentence_start_count}개 (목표: 2개)")
print()

# 상세 분석 - 모든 "잠실유방외과" 등장 위치 찾기
print("=" * 80)
print("상세 분석 - 모든 등장 위치:")
print("=" * 80)

lines = manuscript.split('\n')
for i, line in enumerate(lines, 1):
    if keyword in line:
        # 키워드 주변 텍스트 추출
        idx = 0
        while True:
            idx = line.find(keyword, idx)
            if idx == -1:
                break

            # 앞뒤 10글자씩
            start = max(0, idx - 10)
            end = min(len(line), idx + len(keyword) + 10)
            context = line[start:end]

            # 키워드 바로 뒤 문자 확인
            after_keyword = line[idx + len(keyword):idx + len(keyword) + 3] if idx + len(keyword) < len(line) else ""

            # 카운팅 여부 확인
            pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
            if re.search(pattern, line[idx:]):
                counted = "✅ 카운팅됨"
            else:
                counted = "❌ 카운팅 안됨"

            print(f"줄 {i}: ...{context}...")
            print(f"  → 키워드 뒤: '{after_keyword}' → {counted}")
            print()

            idx += len(keyword)

print("=" * 80)
print("결론:")
print("=" * 80)
if first_para_count == 2:
    print("✅ 첫문단 기준 충족")
else:
    print(f"❌ 첫문단 기준 미달: {first_para_count}/2")

if sentence_start_count == 2:
    print("✅ 문장시작 기준 충족")
else:
    print(f"❌ 문장시작 기준 미달: {sentence_start_count}/2")

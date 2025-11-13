#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/user/newsoom3/최적화')
from auto_manuscript_rewriter import AutoManuscriptRewriter

class MockRewriter(AutoManuscriptRewriter):
    def __init__(self):
        self.forbidden_words_file = '/home/user/newsoom3/최적화/금칙어 리스트.xlsx'
        self.load_forbidden_words()

rewriter = MockRewriter()

# 사용자 제공 원고
manuscript = """뉴트리원 콘드로이친 때문에 요즘 고민이 많습니다. 저도 나이가 들어가니 무릎이 점점 말을 안 들어요. 사실 작년부터 무릎 통증이 심해져서 일상생활이 너무 힘들어요!! 의자에서 일어날 때마다 "아이고, 아이고" 소리가 절로 나오고, 특히 계단 오르내릴 때는 정말 고문 같아요. 뉴트리원 콘드로이친 제품이 괜찮다고 해서 알아보는 중인데, 정말 효과가 있는지 궁금합니다.

혹시 직접 드셔보신 분들 계시면 솔직한 후기 좀 들려주세요. 얼마나 드셔야 효과를 볼 수 있는지도 궁금하고, 혹시 뉴트리원 제품 말고 다른 더 좋은 관절 관리법이 있다면 추천 부탁드려요. 뉴트리원 제품 중에서 어떤 게 제일 나은지도 궁금해요. 제가 알아본 건 뉴트리원 콘드로이친 이거 하나뿐이라서요. 마지막으로 뉴트리원 브랜드 자체에 대한 이야기도 괜찮습니다.

나이 들수록 더 심해질까 봐 정말 걱정이에요. 가족들한테 짐이 되고 싶지도 않고... 아직 할 일도 많은데 무릎 때문에 포기하고 싶지 않고... 다양한 정보 공유 부탁드려요!"""

keyword = "뉴트리원 콘드로이친"
target_whole_str = "뉴트리원 콘드로이친 : 1"
target_pieces_str = """뉴트리원 : 3
콘드로이친 : 0"""
target_subkeywords = 5

print("=" * 100)
print("사용자 제공 원고 검증")
print("=" * 100)

# 분석
analysis = rewriter.analyze_manuscript(
    manuscript=manuscript,
    keyword=keyword,
    target_whole_str=target_whole_str,
    target_pieces_str=target_pieces_str,
    target_subkeywords=target_subkeywords
)

# 첫 문단과 나머지 분리
첫문단 = rewriter.get_first_paragraph(manuscript)
나머지 = rewriter.get_rest_paragraphs(manuscript)

print("\n[첫 문단]")
print("-" * 100)
print(첫문단)
print("-" * 100)
print(f"✓ 통키워드: {analysis['첫문단_통키워드']}회 (목표: 2회) {'✅' if analysis['첫문단_통키워드'] == 2 else '❌'}")

print("\n[나머지 문단]")
print("-" * 100)
print(나머지)
print("-" * 100)

print("\n검증 결과:")
print(f"  1. 글자수: {analysis['chars']}자 (목표: 300~900자) {'✅' if analysis['chars_in_range'] else '❌'}")
print(f"  2. 첫문단 통키워드: {analysis['첫문단_통키워드']}회 (목표: 2회) {'✅' if analysis['첫문단_통키워드'] == 2 else '❌'}")
print(f"  3. 통키워드 문장시작: {analysis['통키워드_문장시작']}개 (목표: 2개) {'✅' if analysis['통키워드_문장시작'] == 2 else '❌'}")
print(f"  4. 첫문단 키워드 사이 문장: {analysis['첫문단_키워드사이_문장수']}개 (목표: 2개 이상) {'✅' if analysis['첫문단_키워드사이_문장수'] >= 2 else '❌'}")

print(f"\n  5. 나머지 통키워드:")
for kw, data in analysis['나머지_통키워드'].items():
    icon = '✅' if data['actual'] == data['target'] else '❌'
    print(f"     - {kw}: {data['actual']}회 (목표: {data['target']}회) {icon}")

print(f"\n  6. 조각키워드:")
for kw, data in analysis['나머지_조각키워드'].items():
    icon = '✅' if data['actual'] == data['target'] else '❌'
    print(f"     - {kw}: {data['actual']}회 (목표: {data['target']}회) {icon}")

print(f"\n  7. 서브키워드: {analysis['subkeywords']['actual']}개 (목표: {analysis['subkeywords']['target']}개 이상) {'✅' if analysis['subkeywords']['actual'] >= analysis['subkeywords']['target'] else '❌'}")

# 수동 카운팅 (중복 확인)
print("\n\n" + "=" * 100)
print("🔍 상세 분석: 중복 카운팅 확인")
print("=" * 100)

print("\n나머지 문단 수동 카운팅:")
print(나머지)
print()

# 통키워드 위치 찾기
import re
통키워드_pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
통키워드_matches = list(re.finditer(통키워드_pattern, 나머지))
print(f"통키워드 [{keyword}] 발견:")
for i, match in enumerate(통키워드_matches, 1):
    start = match.start()
    end = match.end()
    context_start = max(0, start - 10)
    context_end = min(len(나머지), end + 20)
    print(f"  {i}. 위치 {start}: ...{나머지[context_start:context_end]}...")

# 조각키워드 위치 찾기
print(f"\n조각키워드 [뉴트리원] 발견:")
뉴트리원_pattern = rf'뉴트리원(?=\s|[^\w가-힣]|$)'
뉴트리원_matches = list(re.finditer(뉴트리원_pattern, 나머지))
for i, match in enumerate(뉴트리원_matches, 1):
    start = match.start()
    end = match.end()
    context_start = max(0, start - 5)
    context_end = min(len(나머지), end + 15)
    context = 나머지[context_start:context_end]

    # 통키워드 일부인지 확인
    is_part_of_whole = False
    for whole_match in 통키워드_matches:
        if whole_match.start() <= start < whole_match.end():
            is_part_of_whole = True
            break

    marker = "🔴 통키워드 일부" if is_part_of_whole else "🟢 단독 사용"
    print(f"  {i}. 위치 {start}: ...{context}... {marker}")

print(f"\n조각키워드 [콘드로이친] 발견:")
콘드로이친_pattern = rf'콘드로이친(?=\s|[^\w가-힣]|$)'
콘드로이친_matches = list(re.finditer(콘드로이친_pattern, 나머지))
for i, match in enumerate(콘드로이친_matches, 1):
    start = match.start()
    end = match.end()
    context_start = max(0, start - 10)
    context_end = min(len(나머지), end + 15)
    context = 나머지[context_start:context_end]

    # 통키워드 일부인지 확인
    is_part_of_whole = False
    for whole_match in 통키워드_matches:
        if whole_match.start() <= start < whole_match.end():
            is_part_of_whole = True
            break

    marker = "🔴 통키워드 일부" if is_part_of_whole else "🟢 단독 사용"
    print(f"  {i}. 위치 {start}: ...{context}... {marker}")

print("\n\n" + "=" * 100)
print("문제점 분석")
print("=" * 100)

뉴트리원_단독 = sum(1 for match in 뉴트리원_matches
                 if not any(whole_match.start() <= match.start() < whole_match.end()
                          for whole_match in 통키워드_matches))

콘드로이친_단독 = sum(1 for match in 콘드로이친_matches
                   if not any(whole_match.start() <= match.start() < whole_match.end()
                            for whole_match in 통키워드_matches))

print(f"\n현재 카운팅 방식 (중복 포함):")
print(f"  - 통키워드 [뉴트리원 콘드로이친]: {len(통키워드_matches)}회")
print(f"  - 조각키워드 [뉴트리원]: {len(뉴트리원_matches)}회 (통키워드 일부 포함)")
print(f"  - 조각키워드 [콘드로이친]: {len(콘드로이친_matches)}회 (통키워드 일부 포함)")

print(f"\n단독 카운팅 방식 (중복 제외):")
print(f"  - 통키워드 [뉴트리원 콘드로이친]: {len(통키워드_matches)}회")
print(f"  - 조각키워드 [뉴트리원]: {뉴트리원_단독}회 (단독 사용만)")
print(f"  - 조각키워드 [콘드로이친]: {콘드로이친_단독}회 (단독 사용만)")

print(f"\n목표:")
print(f"  - 통키워드 [뉴트리원 콘드로이친]: 1회")
print(f"  - 조각키워드 [뉴트리원]: 3회")
print(f"  - 조각키워드 [콘드로이친]: 0회")

print(f"\n⚠️ 중복 카운팅 문제:")
print(f"  현재 방식: 조각키워드 [뉴트리원] {len(뉴트리원_matches)}회 {'❌' if len(뉴트리원_matches) != 3 else '✅'}")
print(f"  단독 방식: 조각키워드 [뉴트리원] {뉴트리원_단독}회 {'❌' if 뉴트리원_단독 != 3 else '✅'}")
print(f"  현재 방식: 조각키워드 [콘드로이친] {len(콘드로이친_matches)}회 {'❌' if len(콘드로이친_matches) != 0 else '✅'}")
print(f"  단독 방식: 조각키워드 [콘드로이친] {콘드로이친_단독}회 {'❌' if 콘드로이친_단독 != 0 else '✅'}")

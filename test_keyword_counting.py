#!/usr/bin/env python3
"""
통키워드와 조각키워드 카운팅 중복 체크
"""
import sys
sys.path.insert(0, '/home/user/newsoom3/최적화')
from auto_manuscript_rewriter import AutoManuscriptRewriter

class MockRewriter(AutoManuscriptRewriter):
    def __init__(self):
        self.forbidden_words_file = '/home/user/newsoom3/최적화/금칙어 리스트.xlsx'
        self.load_forbidden_words()

rewriter = MockRewriter()

print("=" * 100)
print("통키워드 vs 조각키워드 카운팅 중복 테스트")
print("=" * 100)

# 테스트 케이스 1: 통키워드만 사용
text1 = """
뉴트리원 콘드로이친 먹어보신 분들 계신가요?
뉴트리원 콘드로이친 효과가 좋다고 들었어요.
"""

print("\n[테스트 1] 통키워드만 2회 사용")
print("-" * 100)
print(text1.strip())
print("-" * 100)

통키워드_count = rewriter.count_keyword(text1, "뉴트리원 콘드로이친")
조각1_count = rewriter.count_keyword(text1, "뉴트리원")
조각2_count = rewriter.count_keyword(text1, "콘드로이친")

print(f"통키워드 [뉴트리원 콘드로이친]: {통키워드_count}회")
print(f"조각키워드 [뉴트리원]: {조각1_count}회")
print(f"조각키워드 [콘드로이친]: {조각2_count}회")
print()
print("🔍 분석:")
if 조각1_count == 통키워드_count and 조각2_count == 통키워드_count:
    print("⚠️ 중복 카운팅 발생! 통키워드를 사용하면 조각키워드도 함께 카운팅됩니다.")
else:
    print("✅ 중복 카운팅 없음")

# 테스트 케이스 2: 조각키워드만 사용
text2 = """
뉴트리원 제품 중에서 좋은 게 뭐가 있을까요?
콘드로이친 성분이 중요하다고 들었어요.
뉴트리원 영양제 추천해주세요.
"""

print("\n\n[테스트 2] 조각키워드만 따로 사용 (뉴트리원 2회, 콘드로이친 1회)")
print("-" * 100)
print(text2.strip())
print("-" * 100)

통키워드_count = rewriter.count_keyword(text2, "뉴트리원 콘드로이친")
조각1_count = rewriter.count_keyword(text2, "뉴트리원")
조각2_count = rewriter.count_keyword(text2, "콘드로이친")

print(f"통키워드 [뉴트리원 콘드로이친]: {통키워드_count}회")
print(f"조각키워드 [뉴트리원]: {조각1_count}회")
print(f"조각키워드 [콘드로이친]: {조각2_count}회")

# 테스트 케이스 3: 혼합 사용
text3 = """
뉴트리원 콘드로이친 먹어보신 분들 계신가요?
뉴트리원 제품 중에서 좋은 게 뭐가 있을까요?
뉴트리원 영양제 추천해주세요.
"""

print("\n\n[테스트 3] 혼합 사용 (통키워드 1회 + 조각키워드 뉴트리원 2회 추가)")
print("-" * 100)
print(text3.strip())
print("-" * 100)

통키워드_count = rewriter.count_keyword(text3, "뉴트리원 콘드로이친")
조각1_count = rewriter.count_keyword(text3, "뉴트리원")
조각2_count = rewriter.count_keyword(text3, "콘드로이친")

print(f"통키워드 [뉴트리원 콘드로이친]: {통키워드_count}회")
print(f"조각키워드 [뉴트리원]: {조각1_count}회")
print(f"조각키워드 [콘드로이친]: {조각2_count}회")
print()
print("🔍 분석:")
print(f"   - 통키워드에 포함된 '뉴트리원': {통키워드_count}회")
print(f"   - 단독 사용된 '뉴트리원': {조각1_count - 통키워드_count}회")
print(f"   - 총 '뉴트리원' 카운팅: {조각1_count}회")
print()
if 조각1_count > 통키워드_count:
    print("⚠️ 문제: 통키워드 사용 시 조각키워드도 함께 카운팅됩니다!")
    print("   예) '뉴트리원 콘드로이친' 1회 사용 → '뉴트리원' 카운팅에도 1회 포함")
    print("   이게 의도한 동작인가요?")

# 테스트 케이스 4: 실제 엑셀 목표 시뮬레이션
print("\n\n" + "=" * 100)
print("실제 엑셀 목표 시뮬레이션")
print("=" * 100)
print("\n엑셀 설정:")
print("  - 통키워드 반복수: 뉴트리원 콘드로이친 1회")
print("  - 조각키워드 반복수: 뉴트리원 3회, 콘드로이친 0회")

text4 = """
첫 문단입니다.
뉴트리원 콘드로이친 먹어보신 분들 계신가요?
뉴트리원 콘드로이친 효과가 좋다고 들었어요.

나머지 문단입니다.
뉴트리원 콘드로이친 정보를 찾고 있어요.
뉴트리원 제품 중에서 좋은 게 뭐가 있을까요?
뉴트리원 영양제 추천해주세요.
"""

# 첫 문단과 나머지 분리
lines = text4.strip().split('\n')
첫문단_end = lines.index('')  # 빈 줄 찾기
첫문단 = '\n'.join(lines[:첫문단_end])
나머지 = '\n'.join(lines[첫문단_end+1:])

print("\n원고:")
print("-" * 100)
print(text4.strip())
print("-" * 100)

print("\n[첫 문단]")
print(첫문단)
첫문단_통키워드 = rewriter.count_keyword(첫문단, "뉴트리원 콘드로이친")
print(f"  통키워드 [뉴트리원 콘드로이친]: {첫문단_통키워드}회 (목표: 2회) {'✅' if 첫문단_통키워드 == 2 else '❌'}")

print("\n[나머지 문단]")
print(나머지)
나머지_통키워드 = rewriter.count_keyword(나머지, "뉴트리원 콘드로이친")
나머지_뉴트리원 = rewriter.count_keyword(나머지, "뉴트리원")
나머지_콘드로이친 = rewriter.count_keyword(나머지, "콘드로이친")

print(f"  통키워드 [뉴트리원 콘드로이친]: {나머지_통키워드}회 (목표: 1회) {'✅' if 나머지_통키워드 == 1 else '❌'}")
print(f"  조각키워드 [뉴트리원]: {나머지_뉴트리원}회 (목표: 3회) {'✅' if 나머지_뉴트리원 == 3 else '❌'}")
print(f"  조각키워드 [콘드로이친]: {나머지_콘드로이친}회 (목표: 0회) {'✅' if 나머지_콘드로이친 == 0 else '❌'}")

print("\n🔍 문제점:")
print(f"   - 나머지 문단에 '뉴트리원 콘드로이친' 1회 사용")
print(f"   - 이것이 '뉴트리원' 조각키워드에도 카운팅됨")
print(f"   - 실제 '뉴트리원' 단독 사용: 2회")
print(f"   - 총 '뉴트리원' 카운팅: {나머지_뉴트리원}회")
print(f"   - 목표는 3회인데, 통키워드 1회 + 단독 2회 = 3회로 달성되었지만...")
print(f"   - 사용자의 의도: 조각키워드는 단독 사용만 카운팅? 아니면 통키워드 포함?")

print("\n\n" + "=" * 100)
print("결론")
print("=" * 100)
print("""
현재 구현:
  - 통키워드와 조각키워드가 독립적으로 카운팅됨
  - "뉴트리원 콘드로이친"을 사용하면:
    → 통키워드 1회
    → 조각키워드 "뉴트리원" 1회
    → 조각키워드 "콘드로이친" 1회
  - 즉, 중복 카운팅이 발생함

사용자 의도 확인 필요:
  1. 현재처럼 중복 카운팅이 맞나요?
  2. 아니면 조각키워드는 통키워드 없이 단독 사용만 카운팅해야 하나요?

예시:
  - "뉴트리원 콘드로이친" → 통키워드로만 카운팅
  - "뉴트리원" 단독 → 조각키워드로 카운팅
""")

#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/user/newsoom3/최적화')
from auto_manuscript_rewriter import AutoManuscriptRewriter

# Rewriter 초기화 (API 키 없이 분석만)
class MockRewriter(AutoManuscriptRewriter):
    def __init__(self):
        self.forbidden_words_file = '/home/user/newsoom3/최적화/금칙어 리스트.xlsx'
        self.load_forbidden_words()

rewriter = MockRewriter()

# 테스트 데이터
keyword = "뉴트리원 콘드로이친"
target_whole_str = "뉴트리원 콘드로이친 : 1"
target_pieces_str = """뉴트리원 : 3
콘드로이친 : 0"""
target_subkeywords = 5

manuscript = """뉴트리원 콘드로이친 먹어보신 분들 계신가요?
저도 나이가 들어가니 무릎이 점점 말을 안 들어요.
사실 작년부터 무릎 통증이 심해져서 일상생활이 너무 힘들어요.
의자에서 일어날 때마다 "아이고, 아이고" 소리가 절로 나오고,
특히 계단 오르내릴 때는 정말 고문 같아요.
예전엔 산책도 좋아하고 등산도 자주 갔는데 이제는 엄두도 못 내겠더라고요.
뉴트리원 콘드로이친 괜찮다고 해서 알아보는 중인데, 정말 효과가 있는지 궁금합니다.

혹시 직접 드셔보신 분들 계시면 솔직한 후기 좀 들려주세요.
얼마나 드셔야 효과를 볼 수 있는지도 궁금하고,
뉴트리원 말고 다른 더 좋은 관절 관리법이나 제품이 있다면 추천 부탁드려요.

나이 들수록 더 심해질까 봐 정말 걱정이에요.
가족들한테 짐이 되고 싶지도 않고...
아직 할 일도 많은데 무릎 때문에 포기하고 싶지 않고..
조언 주시면 정말 감사하겠습니다.

# 뉴트리원 콘드로이친 # 뉴트리원 영양제 # 뉴트리원 건강기능식품
"""

print("=" * 100)
print("원고 분석")
print("=" * 100)

# 분석
analysis = rewriter.analyze_manuscript(
    manuscript=manuscript,
    keyword=keyword,
    target_whole_str=target_whole_str,
    target_pieces_str=target_pieces_str,
    target_subkeywords=target_subkeywords
)

print(f"\n키워드: {keyword}")
print(f"\n현재 상태:")
print(f"  - 글자수: {analysis['chars']}자 (목표: 300~900자) {'✅' if analysis['chars_in_range'] else '❌'}")
print(f"  - 첫문단 통키워드: {analysis['첫문단_통키워드']}회 (목표: 2회) {'✅' if analysis['첫문단_통키워드'] == 2 else '❌'}")
print(f"  - 통키워드 문장시작: {analysis['통키워드_문장시작']}개 (목표: 2개) {'✅' if analysis['통키워드_문장시작'] == 2 else '❌'}")
print(f"  - 첫문단 키워드 사이 문장: {analysis['첫문단_키워드사이_문장수']}개 (목표: 최소 2개) {'✅' if analysis['첫문단_키워드사이_문장수'] >= 2 else '❌'}")

print(f"\n나머지 통키워드:")
for kw, data in analysis['나머지_통키워드'].items():
    icon = '✅' if data['actual'] == data['target'] else '❌'
    print(f"  - {kw}: {data['actual']}회 (목표: {data['target']}회) {icon}")

print(f"\n나머지 조각키워드:")
for kw, data in analysis['나머지_조각키워드'].items():
    icon = '✅' if data['actual'] == data['target'] else '❌'
    print(f"  - {kw}: {data['actual']}회 (목표: {data['target']}회) {icon}")

print(f"\n서브키워드:")
print(f"  - {analysis['subkeywords']['actual']}개 (목표: {analysis['subkeywords']['target']}개 이상) {'✅' if analysis['subkeywords']['actual'] >= analysis['subkeywords']['target'] else '❌'}")

# 프롬프트 생성
print("\n" + "=" * 100)
print("Gemini에게 전달될 프롬프트")
print("=" * 100)

prompt = rewriter.create_rewrite_prompt(
    manuscript=manuscript,
    keyword=keyword,
    analysis=analysis,
    target_whole_str=target_whole_str,
    target_pieces_str=target_pieces_str
)

print(prompt)

# 검증 결과
print("\n" + "=" * 100)
print("검증 결과 요약")
print("=" * 100)

필요한_수정사항 = []

if analysis['첫문단_통키워드'] != 2:
    필요한_수정사항.append(f"첫문단 통키워드를 2회로 수정 (현재: {analysis['첫문단_통키워드']}회)")

if analysis['통키워드_문장시작'] != 2:
    필요한_수정사항.append(f"키워드로 시작하는 문장을 2개로 추가 (현재: {analysis['통키워드_문장시작']}개)")

if analysis['첫문단_키워드사이_문장수'] < 2:
    필요한_수정사항.append(f"첫문단 키워드 사이에 문장 추가 (현재: {analysis['첫문단_키워드사이_문장수']}개)")

for kw, data in analysis['나머지_통키워드'].items():
    if data['actual'] != data['target']:
        필요한_수정사항.append(f"나머지 부분에 [{kw}] {data['target']}회 사용 (현재: {data['actual']}회, 부족: {data['diff']}회)")

for kw, data in analysis['나머지_조각키워드'].items():
    if data['actual'] != data['target']:
        필요한_수정사항.append(f"나머지 부분에 [{kw}] {data['target']}회 사용 (현재: {data['actual']}회, 부족: {data['diff']}회)")

if analysis['subkeywords']['actual'] < analysis['subkeywords']['target']:
    필요한_수정사항.append(f"서브키워드 {analysis['subkeywords']['target']}개 이상 사용 (현재: {analysis['subkeywords']['actual']}개)")

if not analysis['chars_in_range']:
    필요한_수정사항.append(f"글자수를 300~900자로 조정 (현재: {analysis['chars']}자)")

if 필요한_수정사항:
    print("\n필요한 수정사항:")
    for i, item in enumerate(필요한_수정사항, 1):
        print(f"  {i}. {item}")
else:
    print("\n✅ 모든 기준 충족! 수정 필요 없음")

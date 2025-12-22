#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/home/user/newsoom3/최적화')
from auto_manuscript_rewriter import AutoManuscriptRewriter

# API 키 설정 (환경변수에서)
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("❌ GEMINI_API_KEY 환경변수를 설정해주세요.")
    sys.exit(1)

# Rewriter 초기화
rewriter = AutoManuscriptRewriter(
    forbidden_words_file='/home/user/newsoom3/최적화/금칙어 리스트.xlsx',
    gemini_api_key=api_key
)

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
print("원고 수정 테스트 시작")
print("=" * 100)

# 원고 수정
result = rewriter.rewrite_manuscript(
    manuscript=manuscript,
    keyword=keyword,
    target_whole_str=target_whole_str,
    target_pieces_str=target_pieces_str,
    target_subkeywords=target_subkeywords,
    max_retries=1
)

print("\n" + "=" * 100)
print("최종 결과")
print("=" * 100)

if result['success']:
    print("\n✅ 성공!")
    print("\n수정된 원고:")
    print("-" * 100)
    print(result['rewritten'])
    print("-" * 100)
else:
    print(f"\n❌ 실패: {result.get('error', 'Unknown')}")
    if 'rewritten' in result and result['rewritten']:
        print("\n수정된 원고 (기준 미달):")
        print("-" * 100)
        print(result['rewritten'])
        print("-" * 100)

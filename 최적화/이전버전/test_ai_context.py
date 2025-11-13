#!/usr/bin/env python3
"""
AI 문맥 재구성 테스트
- 단순 치환 vs AI 재구성 비교
"""

import os
from search_optimizer import SearchOptimizer

# 사용자 원고 (금칙어 포함)
text = """갱년기홍조 때문에 진짜 일상생활이 힘들어서 글 올려봅니다.
이거 증.상이 시작된 지 벌써 6개월이 넘었는데,
처음엔 그냥 피로 때문이라고 생각했어요.
이거인 줄 알게 된 건 최근 친구를 통해서였어요.

요즘은 갑자기 얼굴이 화끈거리고 온몸에 열이 오르면서,
사소한 일에도 감정 기복이 많이 심해졌어요.
밤에 잠도 못 자는 날이 많아져서 만성피로에 시달리고 있고,
'나도 이제 늙었구나' 하는 우울한 생각까지 들더라고요.

산부인과에서 호르몬 치료 문의도 받아봤는데,
암 위험 같은 부작용이 무서워서 선뜻 시작을 못하겠어요.
석류즙이나 칡즙이 갱년기에 좋다고 해서 꾸준히 먹어봤지만,
딱히 큰 약효는 못 봤어요.
비싼 한약도 먹어봤는데 비용이 부담돼서 중단했고요.

이러다 정말 답답한 마음에 친구한테 하소연하다가,
우연히 이거 라는 걸 알게 됐어요.
건강기능식품이 정말 약효가 있을지 의구심도 들고,
인터넷엔 홍보성 후기들이 많아서 뭘 믿어야 할지 모르겠더라고요.

그래서 실제로 경험해보신 분들의 솔직한 조언을 듣고 싶어서,
이렇게 용기내서 글을 올립니다.
혹시 이거 관리에 도움되는 방법 있으시면 알려주세요.
약효 보신 제품이나 생활습관 개선법 있으면 공유 부탁드려요.

갱년기홍조 말고도 갱년기 증.상 완화에 좋은 다른 방법이나,
제가 모르는 더 나은 제품들이 있다면 추천해주시면 감사하겠습니다."""

keyword = "갱년기홍조"

print("=" * 80)
print("AI 문맥 재구성 테스트")
print("=" * 80)

# 1. 기본 최적화 (AI 없음)
print("\n1️⃣ 기본 최적화 (단순 치환)")
print("=" * 80)
optimizer_basic = SearchOptimizer(use_ai=False)
result_basic = optimizer_basic.optimize_for_search(text, keyword)

print(result_basic['optimized_text'])

# 어색한 부분 체크
print("\n⚠️ 어색한 표현 체크:")
awkward_patterns = [
    ("경비이", "조사 오류"),
    ("궁금하다도", "조사 오류"),
    ("그런 모습이 시작된", "문맥 부자연"),
    ("그런 모습 완화에", "문맥 부자연"),
]

for pattern, issue in awkward_patterns:
    if pattern in result_basic['optimized_text']:
        print(f"  ❌ '{pattern}' 발견 - {issue}")

# 2. AI 재구성 (Gemini)
api_key = os.getenv('GEMINI_API_KEY')

if api_key:
    print("\n\n2️⃣ AI 재구성 (문맥에 맞게)")
    print("=" * 80)

    optimizer_ai = SearchOptimizer(use_ai=True, gemini_api_key=api_key)
    result_ai = optimizer_ai.optimize_for_search(text, keyword)

    print(result_ai['optimized_text'])

    # 개선 확인
    print("\n✅ 개선 체크:")
    improved = True
    for pattern, issue in awkward_patterns:
        if pattern in result_ai['optimized_text']:
            print(f"  ❌ '{pattern}' 여전히 있음")
            improved = False

    if improved:
        print("  ✅ 모든 어색한 표현 수정됨!")

    # 비교
    print("\n\n" + "=" * 80)
    print("🔍 개선 전/후 비교")
    print("=" * 80)

    comparisons = [
        ("이거 증.상이", "이거 그런 모습이"),
        ("비용이", "경비이"),
        ("의구심도", "궁금하다도"),
    ]

    for original, basic_result in comparisons:
        basic_snippet = ""
        ai_snippet = ""

        # 기본 최적화 결과에서 찾기
        for line in result_basic['optimized_text'].split('\n'):
            if basic_result in line or original in line:
                basic_snippet = line.strip()
                break

        # AI 재구성 결과에서 비슷한 부분 찾기
        for line in result_ai['optimized_text'].split('\n'):
            if any(word in line for word in original.split()):
                ai_snippet = line.strip()
                break

        if basic_snippet:
            print(f"\n원본: {original}")
            print(f"기본: {basic_snippet[:60]}...")
            if ai_snippet:
                print(f"AI:   {ai_snippet[:60]}...")

else:
    print("\n\n⚠️ Gemini API 키가 없어서 AI 재구성 테스트를 건너뜁니다.")
    print("export GEMINI_API_KEY='your-key' 로 설정하면 AI 재구성을 테스트할 수 있습니다.")

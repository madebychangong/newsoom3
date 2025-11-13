#!/usr/bin/env python3
"""
실제 Gemini API로 테스트
"""

import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyCGjirKto6fE3p80uD0O4CnlJeW4Bbc588'

from auto_manuscript_rewriter import AutoManuscriptRewriter

# 테스트 원고 (사용자가 보여준 것)
test_manuscript = """갱년기홍조 때문에 정말 고민이 많습니다.
저는 50대 중반인데 요즘 너무 힘들어요.
갱년기홍조가 시작된 지 6개월이 넘었는데 증상이 심해요.
얼굴이 화끈거리고 열이 올라요.
병원에서 치료도 받아봤는데 부작용이 걱정되더라고요.
효과가 있는 방법 좀 알려주세요."""

keyword = "갱년기홍조"
target_whole = "갱년기홍조 : 0"
target_pieces = "-"
target_subkeywords = 5

print("=" * 100)
print("실제 Gemini API 테스트 시작")
print("=" * 100)
print(f"키워드: {keyword}")
print(f"원본 원고:\n{test_manuscript}")
print("=" * 100)

try:
    rewriter = AutoManuscriptRewriter(gemini_api_key='AIzaSyCGjirKto6fE3p80uD0O4CnlJeW4Bbc588')

    result = rewriter.rewrite_manuscript(
        manuscript=test_manuscript,
        keyword=keyword,
        target_whole_str=target_whole,
        target_pieces_str=target_pieces,
        target_subkeywords=target_subkeywords,
        max_retries=3
    )

    if result['success']:
        print("\n" + "=" * 100)
        print("✅ 성공!")
        print("=" * 100)
        print(f"시도 횟수: {result.get('attempts', 'N/A')}")
        print(f"\n수정된 원고:")
        print("-" * 100)
        print(result['rewritten'])
        print("-" * 100)

        print(f"\n검증 결과:")
        print(f"  첫문단 통키워드: {result['after_analysis']['첫문단_통키워드']}회 (목표: 2회)")
        print(f"  문장시작: {result['after_analysis']['통키워드_문장시작']}개 (목표: 2개)")
        print(f"  글자수: {result['after_analysis']['chars']}자")
    else:
        print("\n" + "=" * 100)
        print("❌ 실패")
        print("=" * 100)
        print(f"에러: {result.get('error', 'Unknown')}")
        if 'rewritten' in result:
            print(f"\n마지막 시도 원고:")
            print("-" * 100)
            print(result['rewritten'])
            print("-" * 100)

except Exception as e:
    print(f"\n❌ 테스트 실패: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""
AI 재구성 기능 데모
- AI 사용 전/후 비교
- Gemini API 키 설정 방법 안내
"""

import os
from search_optimizer import SearchOptimizer

def demo_with_and_without_ai():
    """AI 사용 전/후 비교 데모"""

    # 테스트 원고
    test_keyword = "팔꿈치 쿠션 보호대"
    test_text = """# 팔꿈치 쿠션 보호대 후기
팔꿈치 쿠션 보호대를 최근에 알게 되어서 진짜 고민이네요.
사실 저는 무릎 통증으로 불편함을 느끼는 50대인데요,
의자에서 일어날 때마다 "아이고" 소리가 절로 나올 정도로 힘들어요.
팔꿈치 쿠션 보호대가 관절 통증에 효과가 있다는 이야기를 들었는데,
정말 가격 대비 효과가 있을지 의심이 들어서 궁금해요.
병원에서 진단을 받아야 할지 고민이네요."""

    print("=" * 80)
    print("AI 재구성 기능 데모")
    print("=" * 80)

    print(f"\n📝 원본 원고:")
    print(test_text)
    print(f"\n키워드: {test_keyword}")
    print(f"원본 키워드 출현: {test_text.count(test_keyword)}회")

    # 1. AI 없이 기본 최적화
    print("\n" + "=" * 80)
    print("1️⃣ 기본 최적화 (AI 없음)")
    print("=" * 80)

    optimizer_basic = SearchOptimizer(use_ai=False)
    result_basic = optimizer_basic.optimize_for_search(test_text, test_keyword)

    print(f"\n✅ 최적화 완료:")
    print(result_basic['optimized_text'])
    print(f"\n📊 변경사항:")
    for change in result_basic['changes']:
        print(f"  {change}")
    print(f"\n키워드 출현: {result_basic['keyword_count']}회")

    # 2. AI 재구성 (API 키가 있으면)
    api_key = os.getenv('GEMINI_API_KEY')

    if api_key:
        print("\n" + "=" * 80)
        print("2️⃣ AI 재구성 포함 (Gemini API)")
        print("=" * 80)

        try:
            optimizer_ai = SearchOptimizer(use_ai=True, gemini_api_key=api_key)
            result_ai = optimizer_ai.optimize_for_search(test_text, test_keyword)

            print(f"\n✅ AI 재구성 완료:")
            print(result_ai['optimized_text'])
            print(f"\n📊 변경사항:")
            for change in result_ai['changes']:
                print(f"  {change}")
            print(f"\n키워드 출현: {result_ai['keyword_count']}회")

            # 비교
            print("\n" + "=" * 80)
            print("🔍 AI 재구성 전/후 비교")
            print("=" * 80)
            print("\n기본 최적화:")
            print(result_basic['optimized_text'][:200] + "...")
            print("\nAI 재구성:")
            print(result_ai['optimized_text'][:200] + "...")

        except Exception as e:
            print(f"\n⚠️ AI 재구성 오류: {e}")
    else:
        print("\n" + "=" * 80)
        print("⚠️ Gemini API 키가 설정되지 않았습니다")
        print("=" * 80)
        print("\nAI 재구성을 사용하려면 다음 중 하나를 수행하세요:")
        print("\n1. 환경변수 설정:")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        print("\n2. GUI에서 API 키 입력:")
        print("   python3 blog_optimizer_gui.py")
        print("   → '🤖 AI 자연스러운 재구성 사용' 체크")
        print("   → Gemini API 키 입력")
        print("\n💡 Gemini API 키 발급:")
        print("   https://aistudio.google.com/app/apikey")

if __name__ == '__main__':
    demo_with_and_without_ai()

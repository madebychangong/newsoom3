#!/usr/bin/env python3
"""
실제 원고 테스트 - 팔꿈치 쿠션 보호대
"""

import os
import sys

# 원고자동화_최종 폴더의 모듈을 import하기 위해 경로 추가
sys.path.insert(0, '/home/user/newsoom3/원고자동화_최종')

from auto_manuscript_rewriter import AutoManuscriptRewriter

# 테스트 데이터
keyword = "팔꿈치 쿠션 보호대"
target_whole = """팔꿈치 쿠션 보호대 : 0"""
target_pieces = """팔꿈치 : 0
쿠션 : 0
보호대 : 1"""
target_subkeywords = 0

manuscript = """# 팔꿈치 쿠션 보호대 관련해서 사용해보신 분 계신가요?

팔꿈치 쿠션 보호대를 최근에 알게 되어서 정말 고민이 많습니다.
사실 저는 무릎 통증으로 고생하고 있는 50대인데요,
의자에서 일어날 때마다 "아이고" 소리가 절로 나올 정도로 힘들어요.
팔꿈치 쿠션 보호대가 관절 통증에 도움이 된다는 이야기를 우연히 듣게 되었는데,
정말 효과가 있을지 의구심이 들어서 이렇게 글을 올려봅니다.

특히 계단 오르내릴 때는 정말 고문 같아요.
예전에는 산책이나 등산도 즐겼는데 이제는 엄두도 못 내겠더라구요.
나이가 들수록 더 심해질까봐 불안하고,
가족들한테 짐이 될까봐 걱정도 됩니다.

유명하다는 정형외과에서 비싼 연골 주사도 맞아봤는데,
효과가 일시적이라 실망이 컸어요.
글루코사민이나 MSM, 보스웰리아 같은 관절 영양제도 꾸준히 먹어봤지만,
솔직히 큰 차이를 못 느끼겠더라구요.
물리치료도 받아봤는데 매번 다니기가 너무 번거로워서 중단했습니다.

이런 상황에서 지인들과 대화하다가 팔꿈치 쿠션 보호대 얘기가 나왔어요.
단순한 영양제랑 뭐가 다른지도 궁금하고,
정말 효과가 있는 건지 의심스럽기도 해요.
그래도 뭔가 붙이거나 보호대를 하려고 알아보고 있는데,
아직 확신이 서지 않네요.

혹시 팔꿈치 쿠션 보호대를 직접 사용해보신 분 계시면,
솔직한 경험담 좀 들려주실 수 있을까요?
효과를 보신 제품이 있다면 추천도 부탁드립니다.

이런 보호대 말고도 관절 통증 완화에 도움되는,
다른 좋은 방법이나 제품이 있을까요?

정말 예전처럼 편하게 걷고 싶은 마음이 간절합니다.
여러분들의 조언 꼭 부탁드려요.
"""

def main():
    # API 키 확인
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수를 설정해주세요.")
        print("예: export GEMINI_API_KEY='your-api-key'")
        return

    print("=" * 100)
    print("🔍 원본 원고 분석")
    print("=" * 100)

    # Rewriter 초기화
    rewriter = AutoManuscriptRewriter(
        forbidden_words_file='/home/user/newsoom3/원고자동화_최종/금칙어 리스트.xlsx',
        gemini_api_key=api_key,
        model_choice=1  # gemini-2.5-pro
    )

    # 원본 분석
    print("\n📊 원본 원고 통계:")
    analysis = rewriter.analyze_manuscript(
        manuscript, keyword, target_whole, target_pieces, target_subkeywords
    )

    print(f"  - 글자수: {analysis['chars']}자")
    print(f"  - 첫문단 통키워드: {analysis['첫문단_통키워드']}회 (목표: 2회)")
    print(f"  - 통키워드 문장시작: {analysis['통키워드_문장시작']}개 (목표: 2개)")
    print(f"  - 첫문단 키워드 사이 문장수: {analysis['첫문단_키워드사이_문장수']}개 (목표: 2개 이상)")

    if analysis['나머지_통키워드']:
        print(f"  - 나머지 통키워드:")
        for kw, data in analysis['나머지_통키워드'].items():
            print(f"    • {kw}: {data['actual']}회 (목표: {data['target']}회)")

    if analysis['나머지_조각키워드']:
        print(f"  - 나머지 조각키워드:")
        for kw, data in analysis['나머지_조각키워드'].items():
            print(f"    • {kw}: {data['actual']}회 (목표: {data['target']}회)")

    print(f"  - 서브키워드: {analysis['subkeywords']['actual']}개 (목표: {analysis['subkeywords']['target']}개)")

    # 금칙어 체크
    forbidden = rewriter.check_forbidden_words(manuscript)
    if forbidden:
        print(f"\n🚫 금칙어 발견: {len(forbidden)}개")
        for item in forbidden[:5]:
            print(f"    • '{item['word']}' → '{item['alternative']}'")

    print("\n" + "=" * 100)
    print("🤖 AI 수정 시작...")
    print("=" * 100)

    # 수정 실행
    result = rewriter.rewrite_manuscript(
        manuscript=manuscript,
        keyword=keyword,
        target_whole_str=target_whole,
        target_pieces_str=target_pieces,
        target_subkeywords=target_subkeywords
    )

    if result['success']:
        print("\n" + "=" * 100)
        print("✅ 수정 성공!")
        print("=" * 100)
        print("\n📝 수정된 원고:")
        print("-" * 100)
        print(result['rewritten'])
        print("-" * 100)
    else:
        print("\n" + "=" * 100)
        print("❌ 수정 실패")
        print("=" * 100)
        print(f"실패 이유: {result.get('error', 'Unknown')}")

        if 'rewritten' in result:
            print("\n📝 수정 시도한 원고 (기준 미달):")
            print("-" * 100)
            print(result['rewritten'])
            print("-" * 100)

if __name__ == '__main__':
    main()

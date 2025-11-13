#!/usr/bin/env python3
"""프롬프트 간소화 테스트"""

import sys
sys.path.insert(0, '원고자동화_최종')

from auto_manuscript_rewriter import AutoManuscriptRewriter

# 테스트 데이터
test_manuscript = """뉴트리원 콘드로이친 때문에 고민이 많습니다.
저는 50대 중반인데 요즘 무릎 건강이 걱정돼요.
관절 건강을 위해 여러 제품을 알아보고 있습니다.
효과가 있는 제품 좀 알려주세요.
정보 공유 부탁드립니다."""

keyword = "뉴트리원 콘드로이친"
target_whole = "뉴트리원 콘드로이친 : 1"
target_pieces = "뉴트리원 : 3\n콘드로이친 : 0"
target_subkeywords = 5

# Rewriter 초기화 (API 키 없이 테스트 - 프롬프트만 생성)
try:
    rewriter = AutoManuscriptRewriter(gemini_api_key='dummy_key_for_test')
except Exception as e:
    print(f"초기화 에러 (예상됨): {e}")
    # API 키 없이도 분석 및 프롬프트 생성은 가능
    import os
    os.environ['GEMINI_API_KEY'] = 'dummy_key_for_test'
    rewriter = AutoManuscriptRewriter()

# 분석
analysis = rewriter.analyze_manuscript(
    test_manuscript, keyword, target_whole, target_pieces, target_subkeywords
)

print("=" * 80)
print("📊 원고 분석 결과")
print("=" * 80)
print(f"글자수: {analysis['chars']}자")
print(f"첫문단 통키워드: {analysis['첫문단_통키워드']}회")
print(f"통키워드 문장시작: {analysis['통키워드_문장시작']}개")
print(f"나머지 통키워드: {analysis['나머지_통키워드']}")
print(f"조각키워드: {analysis['나머지_조각키워드']}")
print(f"서브키워드: {analysis['subkeywords']}")

# 수정 작업 목록 생성
actions = rewriter.create_action_plan(analysis, keyword, target_whole, target_pieces)

print("\n" + "=" * 80)
print("📋 Python이 계산한 수정 작업 목록")
print("=" * 80)
for i, action in enumerate(actions, 1):
    print(f"{i}. {action}")

# 금칙어 체크
forbidden = rewriter.check_forbidden_words(test_manuscript)
if forbidden:
    print("\n🚫 금칙어 발견:")
    for item in forbidden:
        print(f"   - {item['word']} → {item['alternative']}")
else:
    print("\n✅ 금칙어 없음")

# 프롬프트 생성
prompt = rewriter.create_rewrite_prompt(
    test_manuscript, keyword, analysis, target_whole, target_pieces
)

print("\n" + "=" * 80)
print("📝 생성된 프롬프트 (간소화 버전)")
print("=" * 80)
print(prompt)

print("\n" + "=" * 80)
print("📊 프롬프트 통계")
print("=" * 80)
print(f"프롬프트 길이: {len(prompt)} 문자")
print(f"프롬프트 라인 수: {len(prompt.split(chr(10)))} 줄")
print(f"수정 작업 개수: {len(actions)}개")

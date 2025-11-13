#!/usr/bin/env python3
"""키워드 감소 로직 테스트 - "이거 라는" 문제 확인"""

from search_optimizer import SearchOptimizer

# 테스트 케이스
test_cases = [
    {
        'text': """갱년기홍조 때문에 힘들어요.
갱년기홍조 라는 걸 처음 알았어요.
갱년기홍조를 최근에 알게 되었어요.
갱년기홍조가 심해서 고민이에요.
갱년기홍조 관리 방법이 궁금해요.
갱년기홍조는 정말 힘들어요.""",
        'keyword': '갱년기홍조',
        'expected_issues': [
            '이거 라는',  # 이게 나오면 안 됨
            '이거를',     # 조사 붙으면 안 됨
            '이거가',
        ]
    }
]

optimizer = SearchOptimizer()

for i, test in enumerate(test_cases, 1):
    print(f"=" * 80)
    print(f"테스트 케이스 {i}")
    print(f"=" * 80)

    keyword = test['keyword']
    text = test['text']

    print(f"\n키워드: {keyword}")
    print(f"원본 키워드 출현: {text.count(keyword)}회")

    print(f"\n원본:")
    print(text)

    # 최적화 실행
    result = optimizer.optimize_for_search(text, keyword)

    print(f"\n최적화 결과:")
    print("=" * 80)
    print(result['optimized_text'])
    print("=" * 80)

    print(f"\n키워드 출현: {result['keyword_count']}회 (목표: 2-3회)")

    # 문제 표현 확인
    print(f"\n⚠️ 문제 표현 확인:")
    found_issues = False
    for issue in test['expected_issues']:
        if issue in result['optimized_text']:
            print(f"  ❌ '{issue}' 발견! - 여전히 어색함")
            found_issues = True

    if not found_issues:
        print(f"  ✅ 모든 어색한 표현 수정됨!")

    # "이런 거 라는" 확인
    if '이런 거 라는' in result['optimized_text']:
        print(f"  ✅ '이런 거 라는' - 자연스럽게 대체됨")

    print()

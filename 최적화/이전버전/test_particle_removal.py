#!/usr/bin/env python3
"""한글자 조사 제거 테스트"""

from search_optimizer import SearchOptimizer

# 테스트 원고 (키워드+조사 포함)
test_text = """갱년기홍조를 최근에 알게 되었는데, 갱년기홍조가 너무 힘들어요.
갱년기홍조는 정말 고민이고, 갱년기홍조에 대해 알아보고 있어요.
갱년기홍조의 관리 방법이 궁금합니다.
갱년기홍조라는 걸 최근에 알았어요."""

keyword = "갱년기홍조"

print("=" * 80)
print("한글자 조사 제거 테스트")
print("=" * 80)

print(f"\n키워드: {keyword}")
print(f"\n원본 원고:")
print(test_text)

# 조사 카운트
print(f"\n원본 조사 사용:")
print(f"  - '{keyword}를': {test_text.count(keyword + '를')}회")
print(f"  - '{keyword}가': {test_text.count(keyword + '가')}회")
print(f"  - '{keyword}는': {test_text.count(keyword + '는')}회")
print(f"  - '{keyword}에': {test_text.count(keyword + '에')}회")
print(f"  - '{keyword}의': {test_text.count(keyword + '의')}회")
print(f"  - '{keyword}라는': {test_text.count(keyword + '라는')}회")

# 최적화 실행
optimizer = SearchOptimizer()
result = optimizer.optimize_for_search(test_text, keyword)

print(f"\n\n최적화된 원고:")
print("=" * 80)
print(result['optimized_text'])
print("=" * 80)

# 조사 카운트
print(f"\n최적화 후 조사 사용:")
print(f"  - '{keyword}를': {result['optimized_text'].count(keyword + '를')}회")
print(f"  - '{keyword}가': {result['optimized_text'].count(keyword + '가')}회")
print(f"  - '{keyword}는': {result['optimized_text'].count(keyword + '는')}회")
print(f"  - '{keyword}에': {result['optimized_text'].count(keyword + '에')}회")
print(f"  - '{keyword}의': {result['optimized_text'].count(keyword + '의')}회")
print(f"  - '{keyword}라는': {result['optimized_text'].count(keyword + '라는')}회")

# 검증
all_removed = True
for suffix in ['를', '가', '는', '에', '의']:
    if keyword + suffix in result['optimized_text']:
        print(f"\n❌ '{keyword}{suffix}' 아직 남아있음!")
        all_removed = False

if '라는' in result['optimized_text']:
    # '라는'은 띄어쓰기만 확인
    if keyword + '라는' in result['optimized_text']:
        print(f"❌ '{keyword}라는' (붙어있음) → 띄어쓰기 안 됨!")
        all_removed = False
    elif keyword + ' 라는' in result['optimized_text']:
        print(f"✅ '{keyword} 라는' (띄어쓰기) → 정상!")

if all_removed:
    print(f"\n✅ 모든 한글자 조사 제거 완료!")
else:
    print(f"\n⚠️ 일부 조사가 남아있습니다.")

print(f"\n키워드 출현: {result['keyword_count']}회 (목표: 2-3회)")

#!/usr/bin/env python3
"""금칙어 치환 테스트"""

from search_optimizer import SearchOptimizer

# 옵티마이저 초기화
optimizer = SearchOptimizer()

# 테스트 문장들
test_texts = [
    "정말 고민되네요. 어떻게 해야할까요?",
    "좋더라구요. 추천해요!",
    "병원 가서 상담 받았어요.",
    "효과가 좋네요.",
    "진단 받으러 가야하나요?",
]

print("=" * 80)
print("금칙어 치환 테스트")
print("=" * 80)

# 로드된 금칙어 확인
print(f"\n📋 로드된 금칙어: {len(optimizer.forbidden_words)}개")
print("\n주요 금칙어 목록:")
for i, (forbidden, replacement) in enumerate(list(optimizer.forbidden_words.items())[:10]):
    print(f"  {i+1}. '{forbidden}' → '{replacement if replacement else '(삭제)'}'")

print("\n" + "=" * 80)
print("테스트 실행")
print("=" * 80)

for i, text in enumerate(test_texts, 1):
    print(f"\n[{i}] 원본: {text}")
    replaced, changes = optimizer.replace_forbidden_words(text)
    print(f"    결과: {replaced}")
    if changes:
        print(f"    변경: {', '.join(changes)}")
    else:
        print(f"    변경: 없음")

# "네요" 특정 테스트
print("\n" + "=" * 80)
print("'네요' 치환 집중 테스트")
print("=" * 80)

test_neyo = [
    "고민되네요",
    "좋네요",
    "괜찮네요",
    "어려운 일이네요",
    "재미있네요"
]

for text in test_neyo:
    replaced, _ = optimizer.replace_forbidden_words(text)
    print(f"'{text}' → '{replaced}'")

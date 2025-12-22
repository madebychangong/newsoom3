#!/usr/bin/env python3
"""
빌드 전 최적화 결과 미리보기
"""

import sys
sys.path.append('/home/user/blogm')
from search_optimizer import SearchOptimizer

# 초기화
optimizer = SearchOptimizer()

# 테스트할 원고 입력
print("=" * 80)
print("🧪 블로그 원고 최적화 미리보기")
print("=" * 80)
print()

# 키워드 입력
keyword = input("키워드 입력: ").strip()
if not keyword:
    keyword = "고관절영양제"
    print(f"(기본값 사용: {keyword})")

print()

# 원고 입력 (여러 줄)
print("원고를 입력하세요 (끝나면 빈 줄에서 Ctrl+D 또는 Ctrl+Z):")
print("-" * 80)

lines = []
try:
    while True:
        line = input()
        lines.append(line)
except EOFError:
    pass

original_text = '\n'.join(lines)

if not original_text.strip():
    # 샘플 원고
    original_text = f"""# {keyword}에 대해 고민 중인데, 드셔보신 분 계신가요?

{keyword}라는 걸 최근에 알게 되었는데, 정말 효과가 있는지 궁금합니다.
사실 제가 무릎 때문에 너무 고생하고 있거든요.
{keyword}가 무릎 통증에도 도움이 될 수 있다는 얘기를 들었는데, 확신이 서지 않아서요.

50대에 접어들면서 무릎이 점점 더 아파오기 시작했어요.
의자에서 일어날 때마다 "아이고, 아이고" 소리가 절로 나옵니다.

혹시 {keyword}를 직접 사용해보신 분 계시면,
솔직한 경험담 좀 들려주실 수 있을까요?
효과를 보신 제품이 있다면 추천도 부탁드립니다."""
    print("\n(샘플 원고 사용)")

print()
print("=" * 80)
print("🔄 최적화 진행 중...")
print("=" * 80)
print()

# 최적화 실행
result = optimizer.optimize_for_search(original_text, keyword, brand="테스트브랜드")

# 결과 출력
print("=" * 80)
print("📊 최적화 결과")
print("=" * 80)
print(f"원본 길이: {result['original_length']}자")
print(f"최적화 길이: {result['optimized_length']}자")
print(f"차이: {result['length_diff']:+d}자")
print(f"키워드 출현: {result['keyword_count']}회")
print()

print("🔧 변경 사항:")
for change in result['changes']:
    print(f"  {change}")
print()

print("🏷️ 해시태그:")
print(' '.join(['#' + tag for tag in result['hashtags'][:10]]))
print()

# 키워드+조사 검증
print("=" * 80)
print("🔍 키워드+조사 검증")
print("=" * 80)
optimized = result['optimized_text']
patterns = [
    (f'{keyword}를', '❌'),
    (f'{keyword}을', '❌'),
    (f'{keyword}가', '❌'),
    (f'{keyword}이', '❌'),
    (f'{keyword}에', '❌'),
]

all_clear = True
for pattern, status in patterns:
    count = optimized.count(pattern)
    if count > 0:
        print(f"{status} '{pattern}': {count}회 남음 ⚠️")
        all_clear = False
    else:
        print(f"✅ '{pattern}': 제거 완료")

print()
if all_clear:
    print("✅ 모든 키워드+조사 제거 완료!")
else:
    print("⚠️ 일부 키워드+조사가 남아있습니다.")

print()
print("=" * 80)
print("📝 최적화된 원고 전체")
print("=" * 80)
print(optimized)
print()

# 파일로 저장할지 물어보기
print("=" * 80)
save = input("\n결과를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
if save == 'y':
    filename = f"{keyword}_최적화.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("블로그 원고 검색 최적화 결과\n")
        f.write("=" * 80 + "\n\n")
        f.write("📊 최적화 정보\n")
        f.write("-" * 80 + "\n")
        f.write(f"키워드: {keyword}\n")
        f.write(f"글자수: {result['optimized_length']}자 ({result['length_diff']:+d}자)\n")
        f.write(f"키워드 출현: {result['keyword_count']}회\n\n")
        f.write("🔧 변경 사항\n")
        f.write("-" * 80 + "\n")
        for change in result['changes']:
            f.write(f"{change}\n")
        f.write("\n")
        f.write("🏷️ 추천 해시태그\n")
        f.write("-" * 80 + "\n")
        f.write(' '.join(['#' + tag for tag in result['hashtags'][:10]]) + "\n\n")
        f.write("=" * 80 + "\n")
        f.write("📝 최적화된 원고\n")
        f.write("=" * 80 + "\n\n")
        f.write(result['optimized_text'])

    print(f"✅ 저장 완료: {filename}")

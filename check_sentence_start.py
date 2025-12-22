#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/user/newsoom3/최적화')
from auto_manuscript_rewriter import AutoManuscriptRewriter

class MockRewriter(AutoManuscriptRewriter):
    def __init__(self):
        self.forbidden_words_file = '/home/user/newsoom3/최적화/금칙어 리스트.xlsx'
        self.load_forbidden_words()

rewriter = MockRewriter()

manuscript = """뉴트리원 콘드로이친 때문에 요즘 고민이 많습니다. 저도 나이가 들어가니 무릎이 점점 말을 안 들어요. 사실 작년부터 무릎 통증이 심해져서 일상생활이 너무 힘들어요!! 의자에서 일어날 때마다 "아이고, 아이고" 소리가 절로 나오고, 특히 계단 오르내릴 때는 정말 고문 같아요. 뉴트리원 콘드로이친 제품이 괜찮다고 해서 알아보는 중인데, 정말 효과가 있는지 궁금합니다.

혹시 직접 드셔보신 분들 계시면 솔직한 후기 좀 들려주세요. 얼마나 드셔야 효과를 볼 수 있는지도 궁금하고, 혹시 뉴트리원 제품 말고 다른 더 좋은 관절 관리법이 있다면 추천 부탁드려요. 뉴트리원 제품 중에서 어떤 게 제일 나은지도 궁금해요. 제가 알아본 건 뉴트리원 콘드로이친 이거 하나뿐이라서요. 마지막으로 뉴트리원 브랜드 자체에 대한 이야기도 괜찮습니다.

나이 들수록 더 심해질까 봐 정말 걱정이에요. 가족들한테 짐이 되고 싶지도 않고... 아직 할 일도 많은데 무릎 때문에 포기하고 싶지 않고... 다양한 정보 공유 부탁드려요!"""

keyword = "뉴트리원 콘드로이친"

print("=" * 100)
print("문장 시작 카운팅 분석")
print("=" * 100)

# 현재 카운팅 방식
count = rewriter.count_sentences_starting_with(manuscript, keyword)
print(f"\n현재 카운팅 결과: {count}개")

# 줄 단위 분석
print("\n줄 단위 분석:")
print("-" * 100)
lines = manuscript.split('\n')
for i, line in enumerate(lines, 1):
    line = line.strip()
    if line:
        starts = "✅ 시작함" if line.startswith(keyword) else "❌ 시작 안함"
        preview = line[:80] + "..." if len(line) > 80 else line
        print(f"{i}. {starts}: {preview}")

# 문장 단위 분석 (., !, ? 기준)
import re
print("\n\n문장 단위 분석 (., !, ? 기준):")
print("-" * 100)

# 제목 제거
text_no_title = '\n'.join([line for line in manuscript.split('\n')
                           if not line.strip().startswith('#')])

# 문장 분리
sentences = []
for line in text_no_title.split('\n'):
    line = line.strip()
    if line:
        # 문장 분리
        parts = re.split(r'([.!?])\s*', line)
        current = ""
        for i, part in enumerate(parts):
            if part in '.!?':
                current += part
                if current.strip():
                    sentences.append(current.strip())
                current = ""
            else:
                current += part
        if current.strip():
            sentences.append(current.strip())

print(f"총 {len(sentences)}개 문장 발견:\n")
keyword_start_count = 0
for i, sentence in enumerate(sentences, 1):
    if sentence.startswith(keyword):
        keyword_start_count += 1
        print(f"{i}. ✅ [{keyword}]로 시작: {sentence}")
    else:
        preview = sentence[:60] + "..." if len(sentence) > 60 else sentence
        print(f"{i}. ❌ {preview}")

print(f"\n키워드로 시작하는 문장: {keyword_start_count}개")

print("\n\n" + "=" * 100)
print("문제점")
print("=" * 100)
print("""
현재 count_sentences_starting_with는 **줄(line)** 단위로 체크합니다.
하지만 사용자 원고는 첫 문단이 한 줄로 길게 이어져 있어서:
  - 첫 줄만 "뉴트리원 콘드로이친"로 시작
  - 나머지는 같은 줄 중간에 있음

해결 방법:
1. 문장 단위로 체크하도록 변경
2. 또는 줄바꿈을 추가하도록 프롬프트에 명시
""")

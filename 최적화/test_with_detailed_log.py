#!/usr/bin/env python3
"""
상세 로그 출력 테스트
"""

import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyCGjirKto6fE3p80uD0O4CnlJeW4Bbc588'

from auto_manuscript_rewriter import AutoManuscriptRewriter
import re

def count_keyword(text: str, keyword: str) -> int:
    """키워드 카운팅 (띄어쓰기 기준)"""
    if not keyword:
        return 0
    pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
    return len(re.findall(pattern, text))

def get_first_paragraph(text: str) -> str:
    """첫 문단 추출"""
    lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
    text_no_title = '\n'.join(lines)
    paragraphs = text_no_title.split('\n\n')
    return paragraphs[0].strip() if paragraphs else ""

def analyze_detail(text: str, keyword: str):
    """상세 분석"""
    print("\n" + "=" * 80)
    print("🔍 상세 분석")
    print("=" * 80)

    first_para = get_first_paragraph(text)
    print("\n📝 첫 문단:")
    print("-" * 80)
    print(first_para)
    print("-" * 80)

    # 모든 키워드 등장 위치
    print("\n📍 모든 키워드 등장 위치:")
    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        if keyword in line:
            idx = 0
            while True:
                idx = line.find(keyword, idx)
                if idx == -1:
                    break

                # 앞뒤 컨텍스트
                start = max(0, idx - 15)
                end = min(len(line), idx + len(keyword) + 15)
                context = line[start:end]

                # 키워드 바로 뒤 문자
                after = line[idx + len(keyword):idx + len(keyword) + 5] if idx + len(keyword) < len(line) else ""

                # 카운팅 여부
                pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
                if re.search(pattern, line[idx:]):
                    counted = "✅ 카운팅됨"
                else:
                    counted = "❌ 카운팅 안됨"

                is_first_para = line in first_para
                location = "📌 첫문단" if is_first_para else "   나머지"

                print(f"  {location} 줄{i}: ...{context}...")
                print(f"           뒤: '{after}' → {counted}")

                idx += len(keyword)

# 테스트 원고
test_manuscript = """갱년기홍조 때문에 정말 고민이 많습니다.
저는 50대 중반인데 요즘 너무 힘들어요.
증상이 심해서 병원에 갔더니 치료가 필요하다고 합니다."""

keyword = "갱년기홍조"

print("=" * 80)
print("🧪 단일 원고 테스트 (상세 로그)")
print("=" * 80)
print(f"키워드: {keyword}")
print(f"\n원본 원고:\n{test_manuscript}")

try:
    rewriter = AutoManuscriptRewriter(gemini_api_key='AIzaSyCGjirKto6fE3p80uD0O4CnlJeW4Bbc588')

    result = rewriter.rewrite_manuscript(
        manuscript=test_manuscript,
        keyword=keyword,
        target_whole_str="갱년기홍조 : 0",
        target_pieces_str="-",
        target_subkeywords=5,
        max_retries=3
    )

    if result['success']:
        print("\n" + "=" * 80)
        print("✅ 성공!")
        print("=" * 80)
        print(f"시도 횟수: {result.get('attempts', 'N/A')}")
        print(f"\n📄 수정된 원고:")
        print("-" * 80)
        print(result['rewritten'])
        print("-" * 80)

        analyze_detail(result['rewritten'], keyword)

    else:
        print("\n" + "=" * 80)
        print("❌ 실패")
        print("=" * 80)
        print(f"에러: {result.get('error', 'Unknown')}")

        if 'rewritten' in result:
            print(f"\n📄 마지막 시도 원고:")
            print("-" * 80)
            print(result['rewritten'])
            print("-" * 80)

            analyze_detail(result['rewritten'], keyword)

            print("\n" + "=" * 80)
            print("💡 문제 진단")
            print("=" * 80)

            first_para = get_first_paragraph(result['rewritten'])
            first_count = count_keyword(first_para, keyword)

            print(f"첫문단 카운팅: {first_count}회 (목표: 2회)")

            if first_count == 0:
                print("❌ 모든 키워드에 조사가 붙어있습니다!")
            elif first_count == 1:
                print("⚠️ 1개만 조사 없이 사용되었습니다.")
            elif first_count > 2:
                print("⚠️ 너무 많이 사용되었습니다!")

except Exception as e:
    print(f"\n❌ 테스트 실패: {e}")
    import traceback
    traceback.print_exc()

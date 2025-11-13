#!/usr/bin/env python3
"""
실제로 Gemini에게 전달되는 프롬프트 출력
"""

import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyCGjirKto6fE3p80uD0O4CnlJeW4Bbc588'

from auto_manuscript_rewriter import AutoManuscriptRewriter

# 테스트 원고
test_manuscript = """갱년기홍조 때문에 정말 고민이 많습니다.
저는 50대 중반인데 요즘 너무 힘들어요.
증상이 심해서 병원에 갔더니 치료가 필요하다고 합니다."""

keyword = "갱년기홍조"
target_whole = "갱년기홍조 : 0"
target_pieces = "-"

rewriter = AutoManuscriptRewriter(gemini_api_key='AIzaSyCGjirKto6fE3p80uD0O4CnlJeW4Bbc588')

# 분석
analysis = rewriter.analyze_manuscript(
    test_manuscript,
    keyword,
    target_whole,
    target_pieces,
    5
)

# 프롬프트 생성
prompt = rewriter.create_rewrite_prompt(
    test_manuscript,
    keyword,
    analysis,
    target_whole,
    target_pieces
)

print("=" * 100)
print("🔍 Gemini에게 실제로 전달되는 프롬프트:")
print("=" * 100)
print(prompt)
print("=" * 100)

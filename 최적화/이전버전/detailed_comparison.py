#!/usr/bin/env python3
"""
검수 전/후 상세 비교 분석
"""

import pandas as pd
import re
from difflib import SequenceMatcher


def count_keyword_with_spacing(text, keyword):
    """
    띄어쓰기 기준으로 키워드 카운팅
    키워드 뒤에 바로 조사가 붙으면 카운팅 X
    """
    if not keyword:
        return 0

    # 정규식: 키워드 뒤에 공백이나 문장부호가 오는 경우만 카운팅
    pattern = rf'\b{re.escape(keyword)}(?=\s|$|[^\w])'
    matches = re.findall(pattern, text)
    return len(matches)


def split_keyword(keyword):
    """통 키워드를 조각 키워드로 분리"""
    return keyword.split() if keyword else []


def analyze_first_paragraph(text, keyword):
    """첫 문단에서 키워드 출현 분석"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    if not paragraphs:
        return 0, ""

    first_para = paragraphs[0]
    count = count_keyword_with_spacing(first_para, keyword)

    return count, first_para


def compare_changes(before, after, keyword):
    """검수 전/후 변경 사항 분석"""

    print(f"\n{'=' * 100}")
    print(f"키워드: {keyword}")
    print(f"{'=' * 100}")

    # 1. 제목 확인
    before_has_title = before.strip().startswith('#')
    after_has_title = after.strip().startswith('#')

    print(f"\n1. 제목:")
    print(f"   검수전: {'있음' if before_has_title else '없음'}")
    print(f"   검수후: {'있음' if after_has_title else '없음'}")

    if before_has_title and not after_has_title:
        print(f"   ➡️ 변경: 제목 삭제됨")

    # 제목 제거한 텍스트
    before_no_title = '\n'.join([line for line in before.split('\n') if not line.strip().startswith('#')])
    after_no_title = '\n'.join([line for line in after.split('\n') if not line.strip().startswith('#')])

    # 2. 글자수
    print(f"\n2. 글자수:")
    print(f"   검수전: {len(before_no_title)} 자")
    print(f"   검수후: {len(after_no_title)} 자")
    print(f"   차이: {len(after_no_title) - len(before_no_title):+d} 자")

    # 3. 통 키워드 카운팅
    before_count = count_keyword_with_spacing(before_no_title, keyword)
    after_count = count_keyword_with_spacing(after_no_title, keyword)

    print(f"\n3. 통 키워드 출현:")
    print(f"   검수전: {before_count} 회")
    print(f"   검수후: {after_count} 회")
    print(f"   차이: {after_count - before_count:+d} 회")

    # 4. 조각 키워드 카운팅
    pieces = split_keyword(keyword)
    if len(pieces) > 1:
        print(f"\n4. 조각 키워드 출현:")
        for piece in pieces:
            before_piece_count = count_keyword_with_spacing(before_no_title, piece)
            after_piece_count = count_keyword_with_spacing(after_no_title, piece)
            print(f"   '{piece}':")
            print(f"     검수전: {before_piece_count} 회")
            print(f"     검수후: {after_piece_count} 회")
            print(f"     차이: {after_piece_count - before_piece_count:+d} 회")

    # 5. 첫 문단 키워드 출현
    before_first_count, before_first_para = analyze_first_paragraph(before_no_title, keyword)
    after_first_count, after_first_para = analyze_first_paragraph(after_no_title, keyword)

    print(f"\n5. 첫 문단 통 키워드 출현:")
    print(f"   검수전: {before_first_count} 회")
    print(f"   검수후: {after_first_count} 회")

    # 6. 텍스트 변경 사항 (중요 변경만)
    print(f"\n6. 주요 텍스트 변경:")

    # 줄 단위로 비교
    before_lines = [line.strip() for line in before_no_title.split('\n') if line.strip()]
    after_lines = [line.strip() for line in after_no_title.split('\n') if line.strip()]

    # 삭제된 줄
    deleted_lines = []
    for line in before_lines:
        if line not in after_no_title:
            deleted_lines.append(line)

    if deleted_lines:
        print(f"\n   삭제된 문장들:")
        for line in deleted_lines[:5]:  # 처음 5개만
            print(f"     ❌ {line[:80]}...")

    # 추가된 줄
    added_lines = []
    for line in after_lines:
        if line not in before_no_title:
            added_lines.append(line)

    if added_lines:
        print(f"\n   추가된 문장들:")
        for line in added_lines[:5]:
            print(f"     ✅ {line[:80]}...")

    # 7. 키워드가 다른 표현으로 교체된 경우 찾기
    print(f"\n7. 키워드 교체 패턴:")

    # 검수전에 있던 키워드가 검수후에 사라진 경우
    if before_count > after_count:
        print(f"   ➡️ 키워드 {before_count - after_count}회 감소")
        print(f"   키워드가 다른 표현으로 교체된 것으로 추정")

        # 교체된 표현 찾기 (대명사 등)
        replacements = ['이거', '이런 거', '그거', '그런 거', '괜찮은거', '저거', '저런 거']
        for replacement in replacements:
            if replacement in after_no_title and replacement not in before_no_title:
                print(f"   → '{keyword}' → '{replacement}'로 교체된 것으로 추정")


def main():
    """메인 분석"""

    # 엑셀 읽기
    before_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수전')
    after_df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')

    # 처음 5개 행만 비교
    for idx in range(min(5, len(before_df))):
        keyword = before_df.iloc[idx]['키워드']
        before_text = before_df.iloc[idx]['원고']
        after_text = after_df.iloc[idx]['원고']

        if pd.isna(before_text) or pd.isna(after_text):
            continue

        compare_changes(before_text, after_text, keyword)

    print(f"\n\n{'=' * 100}")
    print("전체 패턴 요약")
    print(f"{'=' * 100}")

    print("\n공통 패턴:")
    print("  1. # 제목 대부분 삭제")
    print("  2. 통 키워드 출현 횟수 감소 경향")
    print("  3. 키워드 → 대명사('이거', '그거' 등)로 교체")
    print("  4. 일부 문장 삭제 또는 축약")
    print("  5. 첫 문단 키워드 유지 또는 증가")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
원고 분석 데모 (Gemini API 불필요)
- 엑셀 파일에서 원고를 읽어서 회사 기준에 맞는지 분석
- API 키 없이 분석 기능만 테스트 가능
"""

import pandas as pd
import re
from collections import Counter


def count_keyword(text: str, keyword: str) -> int:
    """키워드 카운팅 (띄어쓰기 기준)"""
    if not keyword or pd.isna(keyword):
        return 0
    pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
    return len(re.findall(pattern, text))


def count_subkeywords(text: str, exclude_keywords: list = None) -> int:
    """서브키워드 목록 수 (2회 이상 등장하는 단어)"""
    if exclude_keywords is None:
        exclude_keywords = []

    words = re.findall(r'[가-힣]+', text)
    word_counter = Counter(words)

    subkeywords = set()
    for word, count in word_counter.items():
        if count >= 2 and len(word) >= 2 and word not in exclude_keywords:
            subkeywords.add(word)

    return len(subkeywords)


def parse_target_value(value_str) -> dict:
    """D, E열 목표값 파싱"""
    if pd.isna(value_str) or value_str == '-':
        return {}

    result = {}
    lines = str(value_str).split('\n')
    for line in lines:
        if ':' in line:
            parts = line.split(':')
            kw = parts[0].strip()
            count = int(parts[1].strip())
            result[kw] = count
    return result


def demo_analysis(max_rows=5):
    """원고 분석 데모"""

    print(f"\n{'=' * 100}")
    print(f"원고 분석 데모 (API 키 불필요)")
    print(f"{'=' * 100}\n")

    # 엑셀 파일 읽기
    try:
        df = pd.read_excel('블로그 작업_엑셀템플릿.xlsx', sheet_name='검수 후')
        print(f"✅ 엑셀 파일 로드 완료: {len(df)}개 행\n")
    except Exception as e:
        print(f"❌ 엑셀 파일 읽기 실패: {e}")
        return

    # 각 원고 분석
    for idx, row in df.iterrows():
        if idx >= max_rows:
            break

        keyword = row['키워드']
        원고 = row['원고']
        target_whole = row['통키워드 반복수']
        target_pieces = row['조각키워드 반복수']
        target_subkeywords = row['서브키워드 목록 수']

        if pd.isna(원고):
            print(f"[{idx+2}행] {keyword}: 원고 없음 - 건너뜀\n")
            continue

        print(f"{'=' * 100}")
        print(f"[{idx+2}행] {keyword}")
        print(f"{'=' * 100}")

        try:
            # 제목 제거
            lines = [line for line in 원고.split('\n') if not line.strip().startswith('#')]
            text_no_title = '\n'.join(lines)

            # 문단 분리
            paragraphs = text_no_title.split('\n\n')
            첫문단 = paragraphs[0] if paragraphs else ""
            나머지 = '\n\n'.join(paragraphs[1:]) if len(paragraphs) > 1 else ""

            # 글자수
            total_chars = len(text_no_title.replace(' ', '').replace('\n', ''))
            첫문단_chars = len(첫문단.replace(' ', '').replace('\n', ''))

            print(f"\n📄 원고 정보:")
            print(f"   총 글자수 (공백/줄바꿈 제외): {total_chars}자 (목표: 300-900자) {'✅' if 300 <= total_chars <= 900 else '❌'}")
            print(f"   문단 수: {len(paragraphs)}개")
            print(f"   첫 문단 글자수: {첫문단_chars}자")

            # 키워드 분석
            if keyword and not pd.isna(keyword):
                # 첫 문단 통키워드
                첫문단_통키워드 = count_keyword(첫문단, keyword)

                # 통키워드로 시작하는 문장 수
                문장시작_count = sum(1 for line in text_no_title.split('\n')
                                  if line.strip().startswith(keyword))

                print(f"\n🎯 키워드 분석:")
                print(f"   첫 문단 통키워드: {첫문단_통키워드}회 (목표: 2회) {'✅' if 첫문단_통키워드 == 2 else '❌'}")
                print(f"   통키워드로 시작하는 문장: {문장시작_count}개 (목표: 2개) {'✅' if 문장시작_count == 2 else '❌'}")

                # 나머지 부분 통키워드
                target_whole_dict = parse_target_value(target_whole)
                if target_whole_dict:
                    print(f"\n   나머지 부분 통키워드:")
                    for kw, target in target_whole_dict.items():
                        actual = count_keyword(나머지, kw)
                        status = '✅' if actual == target else f'❌ (차이: {actual - target:+d})'
                        print(f"      {kw}: {actual}회 / 목표: {target}회 {status}")

                # 나머지 부분 조각키워드
                target_pieces_dict = parse_target_value(target_pieces)
                if target_pieces_dict:
                    print(f"\n   나머지 부분 조각키워드:")
                    for kw, target in target_pieces_dict.items():
                        actual = count_keyword(나머지, kw)
                        status = '✅' if actual == target else f'❌ (차이: {actual - target:+d})'
                        print(f"      {kw}: {actual}회 / 목표: {target}회 {status}")

                # 서브키워드
                exclude_list = [keyword] if keyword else []
                if target_pieces_dict:
                    exclude_list.extend(target_pieces_dict.keys())
                actual_subkeywords = count_subkeywords(text_no_title, exclude_list)
                status = '✅' if actual_subkeywords >= target_subkeywords else f'❌ (부족: {target_subkeywords - actual_subkeywords}개)'
                print(f"\n   서브키워드: {actual_subkeywords}개 / 목표: {target_subkeywords}개 {status}")

                # 통키워드로 시작하는 문장들 표시
                if 문장시작_count > 0:
                    print(f"\n   통키워드로 시작하는 문장들:")
                    count = 0
                    for line in text_no_title.split('\n'):
                        if line.strip().startswith(keyword):
                            count += 1
                            preview = line[:80] + '...' if len(line) > 80 else line
                            print(f"      [{count}] {preview}")

            # 첫 문단 출력
            print(f"\n📝 첫 문단:")
            print("   " + "─" * 95)
            첫문단_lines = 첫문단.split('\n')
            for line in 첫문단_lines[:4]:  # 처음 4줄만
                print(f"   {line}")
            if len(첫문단_lines) > 4:
                print(f"   ... (총 {len(첫문단_lines)}줄)")
            print("   " + "─" * 95)

        except Exception as e:
            print(f"❌ 분석 중 오류: {e}")
            import traceback
            traceback.print_exc()

        print()

    print(f"\n{'=' * 100}")
    print(f"✅ 분석 완료!")
    print(f"{'=' * 100}\n")
    print("💡 실제 원고 수정을 하려면:")
    print("   1. GEMINI_API_KEY 환경변수를 설정하세요")
    print("   2. python auto_manuscript_rewriter.py 를 실행하세요")
    print("   3. 또는 python batch_rewrite_manuscripts.py 로 배치 처리하세요")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='원고 분석 데모')
    parser.add_argument('--max-rows', '-n', type=int, default=5,
                       help='분석할 최대 행수 (기본: 5)')

    args = parser.parse_args()

    demo_analysis(max_rows=args.max_rows)

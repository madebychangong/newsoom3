#!/usr/bin/env python3
"""
배치 원고 자동 수정 시스템
- 엑셀 파일의 검수전 원고를 읽어서 자동으로 수정
- Gemini API 사용
- 결과를 새 엑셀 파일로 저장
"""

import os
import sys
import pandas as pd
from datetime import datetime
from auto_manuscript_rewriter import AutoManuscriptRewriter


def batch_rewrite(input_file='블로그 작업_엑셀템플릿.xlsx',
                  output_file=None,
                  sheet_name='검수전',
                  max_rows=None,
                  gemini_api_key=None):
    """배치 원고 수정"""

    # API 키 확인
    api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수를 설정하거나 --api-key 파라미터를 전달하세요.")
        print("\n사용법:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        print("  python batch_rewrite_manuscripts.py")
        print("\n또는:")
        print("  python batch_rewrite_manuscripts.py --api-key 'your-api-key-here'")
        return

    # 출력 파일명 생성
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'원고수정결과_{timestamp}.xlsx'

    print(f"\n{'=' * 100}")
    print(f"배치 원고 자동 수정 시작")
    print(f"{'=' * 100}")
    print(f"입력 파일: {input_file}")
    print(f"출력 파일: {output_file}")
    print(f"시트명: {sheet_name}")

    # Rewriter 초기화
    try:
        rewriter = AutoManuscriptRewriter(gemini_api_key=api_key)
    except Exception as e:
        print(f"❌ Rewriter 초기화 실패: {e}")
        return

    # 엑셀 파일 읽기
    try:
        df = pd.read_excel(input_file, sheet_name=sheet_name)
        print(f"✅ 엑셀 파일 로드 완료: {len(df)}개 행")
    except Exception as e:
        print(f"❌ 엑셀 파일 읽기 실패: {e}")
        return

    # 처리 결과 저장용
    results = []

    # 각 행 처리
    total = len(df) if max_rows is None else min(max_rows, len(df))

    for idx, row in df.iterrows():
        if max_rows and idx >= max_rows:
            break

        # 키워드 읽기 (앞뒤 따옴표 제거)
        keyword = str(row['키워드']).strip().strip('"').strip("'").strip()
        원고 = row['원고']
        target_whole = row['통키워드 반복수']
        target_pieces = row['조각키워드 반복수']
        target_subkeywords = row['서브키워드 목록 수']

        if pd.isna(원고):
            print(f"\n[{idx+2}행] {keyword}: 원고 없음 - 건너뜀")
            results.append({
                'row': idx + 2,
                'keyword': keyword,
                'status': 'skipped',
                'reason': '원고 없음'
            })
            continue

        print(f"\n{'=' * 100}")
        print(f"[{idx+2}행] {keyword} 처리 중... ({idx+1}/{total})")
        print(f"{'=' * 100}")

        # 원고 수정
        result = rewriter.rewrite_manuscript(
            manuscript=원고,
            keyword=keyword,
            target_whole_str=target_whole,
            target_pieces_str=target_pieces,
            target_subkeywords=target_subkeywords
        )

        if result['success']:
            results.append({
                'row': idx + 2,
                'keyword': keyword,
                'status': 'success',
                'original': result['original'],
                'rewritten': result['rewritten'],
                'before_chars': result['before_analysis']['chars'],
                'after_chars': result['after_analysis']['chars'],
                'before_첫문단_통키워드': result['before_analysis']['첫문단_통키워드'],
                'after_첫문단_통키워드': result['after_analysis']['첫문단_통키워드'],
                'before_문장시작': result['before_analysis']['통키워드_문장시작'],
                'after_문장시작': result['after_analysis']['통키워드_문장시작'],
            })
            print(f"✅ 성공!")
        else:
            results.append({
                'row': idx + 2,
                'keyword': keyword,
                'status': 'failed',
                'error': result.get('error', 'Unknown error'),
                'original': result['original']
            })
            print(f"❌ 실패: {result.get('error', 'Unknown')}")

    # 결과를 엑셀로 저장
    print(f"\n\n{'=' * 100}")
    print(f"결과 저장 중...")
    print(f"{'=' * 100}")

    # 성공한 것들만 추출
    success_results = [r for r in results if r['status'] == 'success']

    if success_results:
        # 결과 DataFrame 생성
        output_df = pd.DataFrame([
            {
                '행번호': r['row'],
                '키워드': r['keyword'],
                '원본_글자수': r['before_chars'],
                '수정_글자수': r['after_chars'],
                '원본_첫문단_통키워드': r['before_첫문단_통키워드'],
                '수정_첫문단_통키워드': r['after_첫문단_통키워드'],
                '원본_문장시작': r['before_문장시작'],
                '수정_문장시작': r['after_문장시작'],
                '원본원고': r['original'],
                '수정원고': r['rewritten']
            }
            for r in success_results
        ])

        # 엑셀로 저장
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            output_df.to_excel(writer, sheet_name='수정결과', index=False)

            # 원본 데이터도 함께 저장
            df.to_excel(writer, sheet_name='원본데이터', index=False)

        print(f"✅ 결과 저장 완료: {output_file}")
        print(f"   수정 성공: {len(success_results)}개")
        print(f"   수정 실패: {len([r for r in results if r['status'] == 'failed'])}개")
        print(f"   건너뜀: {len([r for r in results if r['status'] == 'skipped'])}개")
    else:
        print(f"❌ 성공한 결과가 없어서 파일을 저장하지 않았습니다.")

    # 상세 통계
    print(f"\n\n{'=' * 100}")
    print(f"상세 통계")
    print(f"{'=' * 100}")

    if success_results:
        avg_before_chars = sum(r['before_chars'] for r in success_results) / len(success_results)
        avg_after_chars = sum(r['after_chars'] for r in success_results) / len(success_results)

        print(f"평균 글자수:")
        print(f"  수정 전: {avg_before_chars:.0f}자")
        print(f"  수정 후: {avg_after_chars:.0f}자")

        # 첫문단 통키워드 2회 달성률
        첫문단_2회_달성 = sum(1 for r in success_results if r['after_첫문단_통키워드'] == 2)
        print(f"\n첫문단 통키워드 2회 달성: {첫문단_2회_달성}/{len(success_results)} ({첫문단_2회_달성/len(success_results)*100:.1f}%)")

        # 문장시작 2개 달성률
        문장시작_2개_달성 = sum(1 for r in success_results if r['after_문장시작'] == 2)
        print(f"문장시작 2개 달성: {문장시작_2개_달성}/{len(success_results)} ({문장시작_2개_달성/len(success_results)*100:.1f}%)")

        # 글자수 범위 달성률 (300-900자)
        범위_달성 = sum(1 for r in success_results if 300 <= r['after_chars'] <= 900)
        print(f"글자수 범위 달성 (300-900자): {범위_달성}/{len(success_results)} ({범위_달성/len(success_results)*100:.1f}%)")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='배치 원고 자동 수정')
    parser.add_argument('--input', '-i', default='블로그 작업_엑셀템플릿.xlsx', help='입력 엑셀 파일')
    parser.add_argument('--output', '-o', help='출력 엑셀 파일 (기본: 자동생성)')
    parser.add_argument('--sheet', '-s', default='검수전', help='시트명 (기본: 검수전)')
    parser.add_argument('--max-rows', '-n', type=int, help='최대 처리 행수')
    parser.add_argument('--api-key', '-k', help='Gemini API 키')

    args = parser.parse_args()

    batch_rewrite(
        input_file=args.input,
        output_file=args.output,
        sheet_name=args.sheet,
        max_rows=args.max_rows,
        gemini_api_key=args.api_key
    )


if __name__ == '__main__':
    main()

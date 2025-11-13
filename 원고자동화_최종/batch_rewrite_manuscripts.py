#!/usr/bin/env python3
"""
배치 원고 자동 수정 시스템
- 엑셀 파일의 검수전 원고를 읽어서 자동으로 수정
- Gemini API 사용
- 결과를 개별 txt 파일로 저장 (제목 제외, 큰따옴표 제외)
"""

import os
import sys
import pandas as pd
from datetime import datetime
from auto_manuscript_rewriter import AutoManuscriptRewriter


def batch_rewrite(input_file='블로그 작업_엑셀템플릿.xlsx',
                  output_file=None,  # 사용하지 않음 (하위호환성 유지)
                  sheet_name='검수전',
                  max_rows=None,
                  gemini_api_key=None,
                  model_choice=1):
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

    print(f"\n{'=' * 100}")
    print(f"배치 원고 자동 수정 시작")
    print(f"{'=' * 100}")
    print(f"입력 파일: {input_file}")
    print(f"시트명: {sheet_name}")
    print(f"출력 형식: 개별 txt 파일 (제목 제외)")

    # Rewriter 초기화
    try:
        rewriter = AutoManuscriptRewriter(gemini_api_key=api_key, model_choice=model_choice)
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

        # 원고 수정 (재시도 1번 - 첫 시도에 성공하도록!)
        result = rewriter.rewrite_manuscript(
            manuscript=원고,
            keyword=keyword,
            target_whole_str=target_whole,
            target_pieces_str=target_pieces,
            target_subkeywords=target_subkeywords,
            max_retries=1
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
                'before_나머지_통키워드': result['before_analysis']['나머지_통키워드'],
                'after_나머지_통키워드': result['after_analysis']['나머지_통키워드'],
                'before_조각키워드': result['before_analysis']['나머지_조각키워드'],
                'after_조각키워드': result['after_analysis']['나머지_조각키워드'],
                'before_서브키워드': result['before_analysis']['subkeywords'],
                'after_서브키워드': result['after_analysis']['subkeywords'],
                'target_whole': target_whole,
                'target_pieces': target_pieces,
                'target_subkeywords': target_subkeywords,
            })
            print(f"✅ 성공!")
        else:
            # 실패해도 rewritten이 있으면 저장
            if 'rewritten' in result and result['rewritten']:
                before_analysis = result.get('before_analysis', {})
                after_analysis = result.get('after_analysis', {})

                results.append({
                    'row': idx + 2,
                    'keyword': keyword,
                    'status': 'partial',  # 부분 성공 (기준 미달이지만 텍스트는 있음)
                    'original': result['original'],
                    'rewritten': result['rewritten'],
                    'before_chars': before_analysis.get('chars', 0),
                    'after_chars': after_analysis.get('chars', 0),
                    'before_첫문단_통키워드': before_analysis.get('첫문단_통키워드', 0),
                    'after_첫문단_통키워드': after_analysis.get('첫문단_통키워드', 0),
                    'before_문장시작': before_analysis.get('통키워드_문장시작', 0),
                    'after_문장시작': after_analysis.get('통키워드_문장시작', 0),
                    'before_나머지_통키워드': before_analysis.get('나머지_통키워드', {}),
                    'after_나머지_통키워드': after_analysis.get('나머지_통키워드', {}),
                    'before_조각키워드': before_analysis.get('나머지_조각키워드', {}),
                    'after_조각키워드': after_analysis.get('나머지_조각키워드', {}),
                    'before_서브키워드': before_analysis.get('subkeywords', {}),
                    'after_서브키워드': after_analysis.get('subkeywords', {}),
                    'target_whole': target_whole,
                    'target_pieces': target_pieces,
                    'target_subkeywords': target_subkeywords,
                    'error': result.get('error', '기준 미달')
                })
                print(f"⚠️ 기준 미달 (저장함): {result.get('error', 'Unknown')}")
            else:
                results.append({
                    'row': idx + 2,
                    'keyword': keyword,
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error'),
                    'original': result['original']
                })
                print(f"❌ 실패: {result.get('error', 'Unknown')}")

    # 결과를 txt로 저장
    print(f"\n\n{'=' * 100}")
    print(f"결과 저장 중...")
    print(f"{'=' * 100}")

    # 성공 또는 부분 성공 (기준 미달이지만 텍스트 있음)
    success_results = [r for r in results if r['status'] in ['success', 'partial']]

    if success_results:
        # 출력 폴더 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_folder = f'원고수정결과_{timestamp}'
        os.makedirs(output_folder, exist_ok=True)

        # 각 원고를 개별 txt 파일로 저장
        for r in success_results:
            keyword = r['keyword']
            rewritten = r['rewritten']

            # 제목 제거 (# 로 시작하는 첫 줄 제거)
            lines = rewritten.split('\n')
            content_lines = []
            for line in lines:
                if line.strip().startswith('#'):
                    continue  # 제목 건너뛰기
                content_lines.append(line)

            # 맨 앞뒤 빈 줄 제거
            content = '\n'.join(content_lines).strip()

            # 파일명에 사용 불가능한 문자 제거
            safe_keyword = keyword.replace('/', '_').replace('\\', '_').replace(':', '_')
            filename = f"{output_folder}/{safe_keyword}.txt"

            # txt 파일로 저장 (제목 없이, 큰따옴표 없이)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"  ✅ {keyword} → {filename}")

        # 통계 파일 저장
        stats_file = f"{output_folder}/통계.txt"
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(f"원고 수정 결과 통계\n")
            f.write(f"{'=' * 80}\n\n")
            f.write(f"저장됨: {len(success_results)}개\n")
            f.write(f"  - 기준 충족 ✅: {len([r for r in success_results if r['status'] == 'success'])}개\n")
            f.write(f"  - 기준 미달 ⚠️: {len([r for r in success_results if r['status'] == 'partial'])}개\n")
            f.write(f"저장 안 됨: {len([r for r in results if r['status'] == 'failed'])}개\n")
            f.write(f"건너뜀: {len([r for r in results if r['status'] == 'skipped'])}개\n\n")

            f.write(f"{'=' * 80}\n")
            f.write(f"개별 원고 통계\n")
            f.write(f"{'=' * 80}\n\n")

            for r in success_results:
                status_icon = '✅' if r['status'] == 'success' else '⚠️'
                f.write(f"[{r['keyword']}] {status_icon}\n")
                f.write(f"  글자수: {r['before_chars']}자 → {r['after_chars']}자\n")
                f.write(f"  첫문단 통키워드: {r['before_첫문단_통키워드']}회 → {r['after_첫문단_통키워드']}회 {'✅' if r['after_첫문단_통키워드'] == 2 else '❌'}\n")
                f.write(f"  문장시작: {r['before_문장시작']}개 → {r['after_문장시작']}개 {'✅' if r['after_문장시작'] == 2 else '❌'}\n")

                # 나머지 통키워드
                after_나머지_통키워드 = r.get('after_나머지_통키워드', {})
                if after_나머지_통키워드:
                    for kw, data in after_나머지_통키워드.items():
                        target = data.get('target', 0)
                        actual = data.get('actual', 0)
                        icon = '✅' if actual >= target else '❌'
                        f.write(f"  나머지 [{kw}]: {actual}회 (목표: {target}회 이상) {icon}\n")

                # 조각키워드
                after_조각키워드 = r.get('after_조각키워드', {})
                if after_조각키워드:
                    for kw, data in after_조각키워드.items():
                        target = data.get('target', 0)
                        actual = data.get('actual', 0)
                        icon = '✅' if actual >= target else '❌'
                        f.write(f"  조각 [{kw}]: {actual}회 (목표: {target}회 이상) {icon}\n")

                # 서브키워드
                after_서브키워드 = r.get('after_서브키워드', {})
                if after_서브키워드:
                    target = after_서브키워드.get('target', 0)
                    actual = after_서브키워드.get('actual', 0)
                    icon = '✅' if actual >= target else '❌'
                    f.write(f"  서브키워드 목록 수: {actual}개 (목표: {target}개 이상) {icon}\n")

                if r['status'] == 'partial':
                    f.write(f"  ⚠️ {r.get('error', '기준 미달')}\n")
                f.write(f"\n")

        print(f"\n✅ 결과 저장 완료: {output_folder}/")
        print(f"   저장됨: {len(success_results)}개")
        print(f"     - 기준 충족: {len([r for r in success_results if r['status'] == 'success'])}개")
        print(f"     - 기준 미달: {len([r for r in success_results if r['status'] == 'partial'])}개")
        print(f"   저장 안 됨: {len([r for r in results if r['status'] == 'failed'])}개")
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

    parser = argparse.ArgumentParser(description='배치 원고 자동 수정 (txt 파일로 저장)')
    parser.add_argument('--input', '-i', default='블로그 작업_엑셀템플릿.xlsx', help='입력 엑셀 파일')
    parser.add_argument('--sheet', '-s', default='검수전', help='시트명 (기본: 검수전)')
    parser.add_argument('--max-rows', '-n', type=int, help='최대 처리 행수')
    parser.add_argument('--api-key', '-k', help='Gemini API 키')
    parser.add_argument('--model', '-m', type=int, default=1, choices=[1, 2], help='모델 선택 (1: pro, 2: flash)')

    args = parser.parse_args()

    batch_rewrite(
        input_file=args.input,
        sheet_name=args.sheet,
        max_rows=args.max_rows,
        gemini_api_key=args.api_key,
        model_choice=args.model
    )


if __name__ == '__main__':
    main()

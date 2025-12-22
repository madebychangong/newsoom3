#!/usr/bin/env python3
"""
엑셀 파일 분석 - 검수 전/후 비교
"""

import pandas as pd
import sys

def analyze_template():
    """블로그 작업 엑셀 템플릿 분석"""

    file_path = '블로그 작업_엑셀템플릿.xlsx'

    # 엑셀 파일의 시트 목록 확인
    excel_file = pd.ExcelFile(file_path)
    print("=" * 80)
    print("시트 목록:")
    print("=" * 80)
    for sheet in excel_file.sheet_names:
        print(f"  - {sheet}")

    # 각 시트 읽기
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        print(f"\n{'=' * 80}")
        print(f"시트: {sheet_name}")
        print(f"{'=' * 80}")
        print(f"행 수: {len(df)}")
        print(f"열 목록: {list(df.columns)}")
        print(f"\n첫 3행 미리보기:")
        print(df.head(3).to_string())

        # 원고 컬럼이 있으면 첫 번째 원고 출력
        if '원고' in df.columns and len(df) > 0:
            print(f"\n[첫 번째 원고 전체]:")
            print("-" * 80)
            print(df.iloc[0]['원고'])
            print("-" * 80)

def analyze_forbidden():
    """금칙어 리스트 분석"""

    file_path = '금칙어 리스트.xlsx'

    df = pd.read_excel(file_path)

    print("\n" + "=" * 80)
    print("금칙어 리스트 분석")
    print("=" * 80)
    print(f"행 수: {len(df)}")
    print(f"열 목록: {list(df.columns)}")
    print(f"\n첫 10행:")
    print(df.head(10).to_string())

    # B열(금칙어), C열 이후(대체어) 확인
    print(f"\n금칙어 구조:")
    for idx, row in df.head(10).iterrows():
        forbidden = row.iloc[1] if len(row) > 1 else None  # B열
        alternatives = [row.iloc[i] for i in range(2, len(row)) if pd.notna(row.iloc[i])]  # C열 이후

        if pd.notna(forbidden):
            print(f"  금칙어: {forbidden}")
            if alternatives:
                print(f"    대체어: {', '.join(str(alt) for alt in alternatives)}")

if __name__ == '__main__':
    try:
        analyze_template()
        analyze_forbidden()
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()

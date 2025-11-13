#!/usr/bin/env python3
"""
원고 자동 검수 및 수정 GUI
- Gemini API를 사용한 회사 기준 기반 원고 수정
- 엑셀 배치 처리
- 진행 상황 실시간 표시
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
from datetime import datetime

try:
    import pandas as pd
    from auto_manuscript_rewriter import AutoManuscriptRewriter
except ImportError as e:
    print(f"필요한 패키지가 설치되어 있지 않습니다: {e}")
    print("pip install pandas openpyxl google-generativeai")
    sys.exit(1)


class ManuscriptGUI:
    """원고 자동 수정 GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("원고 자동 검수 및 수정")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)

        # 변수
        self.gemini_api_key = tk.StringVar()
        self.input_file = tk.StringVar()
        self.max_rows = tk.IntVar(value=0)  # 0 = 전체

        # Rewriter (나중에 초기화)
        self.rewriter = None
        self.is_processing = False

        # UI 구성
        self.setup_ui()

    def setup_ui(self):
        """UI 구성"""
        # 스타일
        style = ttk.Style()
        style.theme_use('clam')

        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 타이틀
        title_label = ttk.Label(
            main_frame,
            text="📝 원고 자동 검수 및 수정",
            font=("맑은 고딕", 18, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        subtitle_label = ttk.Label(
            main_frame,
            text="회사 기준에 맞게 Gemini AI가 자동으로 원고를 수정합니다",
            font=("맑은 고딕", 10)
        )
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))

        # ─────────────────────────────────────────────────
        # 1. Gemini API 키
        # ─────────────────────────────────────────────────
        row = 2
        ttk.Label(
            main_frame,
            text="🔑 Gemini API 키:",
            font=("맑은 고딕", 10, "bold")
        ).grid(row=row, column=0, sticky=tk.W, pady=5)

        api_frame = ttk.Frame(main_frame)
        api_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        api_frame.columnconfigure(0, weight=1)

        self.api_entry = ttk.Entry(api_frame, textvariable=self.gemini_api_key, width=50, show="*")
        self.api_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(api_frame, text="표시", command=self.toggle_api_visibility, width=8).grid(row=0, column=1)

        ttk.Label(
            main_frame,
            text="Google AI Studio(aistudio.google.com)에서 무료로 발급 가능",
            font=("맑은 고딕", 8),
            foreground="gray"
        ).grid(row=row+1, column=1, columnspan=2, sticky=tk.W)

        # ─────────────────────────────────────────────────
        # 2. 엑셀 파일 선택
        # ─────────────────────────────────────────────────
        row += 2
        ttk.Label(
            main_frame,
            text="📁 엑셀 파일:",
            font=("맑은 고딕", 10, "bold")
        ).grid(row=row, column=0, sticky=tk.W, pady=5)

        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)

        ttk.Entry(file_frame, textvariable=self.input_file, width=50).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(file_frame, text="파일 선택", command=self.browse_file).grid(row=0, column=1)

        # ─────────────────────────────────────────────────
        # 3. 처리할 행 수
        # ─────────────────────────────────────────────────
        row += 1
        ttk.Label(main_frame, text="🔢 처리할 행 수:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )

        rows_frame = ttk.Frame(main_frame)
        rows_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)

        ttk.Spinbox(
            rows_frame,
            from_=0,
            to=100,
            textvariable=self.max_rows,
            width=10
        ).grid(row=0, column=0, padx=(0, 5))

        ttk.Label(
            rows_frame,
            text="(0 = 전체 처리)",
            font=("맑은 고딕", 8),
            foreground="gray"
        ).grid(row=0, column=1)

        # 구분선
        row += 1
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15
        )

        # ─────────────────────────────────────────────────
        # 5. 실행 버튼
        # ─────────────────────────────────────────────────
        row += 1
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(
            button_frame,
            text="🚀 원고 수정 시작",
            command=self.start_processing,
            width=25
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="⏸️ 중지",
            command=self.stop_processing,
            width=15,
            state='disabled'
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        ttk.Button(
            button_frame,
            text="📂 출력 폴더 열기",
            command=self.open_output_folder,
            width=20
        ).grid(row=0, column=2, padx=5)

        # ─────────────────────────────────────────────────
        # 7. 진행 상황
        # ─────────────────────────────────────────────────
        row += 1
        ttk.Label(main_frame, text="진행 상황:", font=("맑은 고딕", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5)
        )

        self.progress = ttk.Progressbar(main_frame, mode='determinate', maximum=100)
        self.progress.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))

        self.progress_label = ttk.Label(main_frame, text="대기 중...", font=("맑은 고딕", 9))
        self.progress_label.grid(row=row+1, column=1, columnspan=2, sticky=tk.W)

        # ─────────────────────────────────────────────────
        # 8. 로그
        # ─────────────────────────────────────────────────
        row += 2
        log_frame = ttk.LabelFrame(main_frame, text="실행 로그", padding="10")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        main_frame.rowconfigure(row, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=18,
            width=90,
            font=("맑은 고딕", 9),
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 초기 로그
        self.log("=" * 100)
        self.log("원고 자동 검수 및 수정 시스템 v2.0")
        self.log("=" * 100)
        self.log("✅ 시스템 준비 완료")
        self.log("")
        self.log("📌 회사 검수 기준:")
        self.log("   - 글자수: 300~900자")
        self.log("   - 첫 문단: 통키워드 정확히 2회, 통키워드로 시작하는 문장 2개")
        self.log("   - 나머지 부분: D, E열 목표 충족")
        self.log("   - 서브키워드: F열 목표 충족")
        self.log("   - 금칙어 자동 치환")
        self.log("")
        self.log("💡 Gemini API 키를 입력하고 엑셀 파일을 선택한 뒤 '원고 수정 시작'을 눌러주세요")
        self.log("")

    def log(self, message):
        """로그 출력"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def toggle_api_visibility(self):
        """API 키 표시/숨김 토글"""
        if self.api_entry.cget('show') == '*':
            self.api_entry.config(show='')
        else:
            self.api_entry.config(show='*')

    def browse_file(self):
        """파일 선택"""
        filename = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("엑셀 파일", "*.xlsx"), ("모든 파일", "*.*")]
        )
        if filename:
            self.input_file.set(filename)
            self.log(f"📁 파일 선택됨: {os.path.basename(filename)}")

    def open_output_folder(self):
        """출력 폴더 열기"""
        if not self.input_file.get():
            messagebox.showwarning("경고", "먼저 파일을 선택해주세요.")
            return

        folder = os.path.dirname(self.input_file.get()) or "."
        if sys.platform == 'win32':
            os.startfile(folder)
        elif sys.platform == 'darwin':
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def start_processing(self):
        """처리 시작"""
        # 유효성 검사
        api_key = self.gemini_api_key.get()
        if not api_key:
            messagebox.showerror(
                "오류",
                "Gemini API 키를 입력해주세요.\n\n"
                "Google AI Studio(aistudio.google.com)에서 발급받을 수 있습니다."
            )
            return

        input_file = self.input_file.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("오류", "유효한 엑셀 파일을 선택해주세요.")
            return

        # 버튼 상태 변경
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.is_processing = True

        # 로그 초기화
        self.log("")
        self.log("=" * 100)
        self.log("🚀 원고 수정 시작")
        self.log("=" * 100)
        self.log(f"📁 입력 파일: {os.path.basename(input_file)}")
        self.log(f"📊 시트명: 검수전")

        max_rows = self.max_rows.get()
        if max_rows > 0:
            self.log(f"🔢 처리할 행 수: {max_rows}개")
        else:
            self.log(f"🔢 처리할 행 수: 전체")
        self.log("")

        # 백그라운드 스레드에서 실행
        thread = threading.Thread(target=self.run_processing)
        thread.daemon = True
        thread.start()

    def stop_processing(self):
        """처리 중지"""
        self.is_processing = False
        self.log("\n⏸️ 사용자가 중지를 요청했습니다...")

    def run_processing(self):
        """백그라운드 처리"""
        try:
            # Rewriter 초기화
            api_key = self.gemini_api_key.get()
            self.log("🤖 Gemini API 초기화 중...")

            try:
                self.rewriter = AutoManuscriptRewriter(gemini_api_key=api_key)
                self.log("✅ Gemini API 초기화 완료")
                self.log("")
            except Exception as e:
                self.log(f"❌ Gemini API 초기화 실패: {e}")
                messagebox.showerror("오류", f"Gemini API 초기화 실패:\n{e}")
                return

            # 엑셀 읽기
            input_file = self.input_file.get()
            sheet_name = "검수전"

            self.log(f"📊 엑셀 파일 읽는 중...")
            df = pd.read_excel(input_file, sheet_name=sheet_name)

            total_rows = len(df)
            max_rows = self.max_rows.get()
            if max_rows > 0:
                total_rows = min(max_rows, total_rows)

            self.log(f"✅ {total_rows}개 행을 처리합니다")
            self.log("")

            # 결과 저장용
            results = []

            # 각 행 처리
            for idx, row in df.iterrows():
                if not self.is_processing:
                    self.log("\n⏸️ 처리 중지됨")
                    break

                if max_rows > 0 and idx >= max_rows:
                    break

                # 키워드 읽기 (앞뒤 따옴표 제거)
                keyword = str(row['키워드']).strip().strip('"').strip("'").strip()
                원고 = row['원고']
                target_whole = row['통키워드 반복수']
                target_pieces = row['조각키워드 반복수']
                target_subkeywords = row['서브키워드 목록 수']

                if pd.isna(원고):
                    self.log(f"[{idx+1}/{total_rows}] {keyword}: 원고 없음 - 건너뜀")
                    continue

                # 진행 상황 업데이트
                progress = int((idx + 1) / total_rows * 100)
                self.progress['value'] = progress
                self.progress_label.config(text=f"{idx+1}/{total_rows} 처리 중... ({progress}%)")

                self.log(f"[{idx+1}/{total_rows}] {keyword} 처리 중...")

                # 원고 수정 (한 번만 시도)
                result = self.rewriter.rewrite_manuscript(
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
                    self.log(f"   ✅ 성공: {result['before_analysis']['chars']}자 → {result['after_analysis']['chars']}자")
                else:
                    # 실패해도 rewritten이 있으면 저장
                    if 'rewritten' in result and result['rewritten']:
                        before_analysis = result.get('before_analysis', {})
                        after_analysis = result.get('after_analysis', {})

                        results.append({
                            'row': idx + 2,
                            'keyword': keyword,
                            'status': 'partial',
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
                        self.log(f"   ⚠️ 기준 미달 (저장함): {result.get('error', 'Unknown')}")
                    else:
                        self.log(f"   ❌ 실패: {result.get('error', 'Unknown')}")

                self.log("")

            if not results:
                self.log("❌ 수정된 원고가 없습니다.")
                return

            # 결과 저장
            self.log("💾 결과를 txt 파일로 저장 중...")

            # 출력 폴더 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_folder = f'원고수정결과_{timestamp}'
            output_path = os.path.join(os.path.dirname(input_file), output_folder)
            os.makedirs(output_path, exist_ok=True)

            # 각 원고를 개별 txt 파일로 저장
            for r in results:
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
                filename = os.path.join(output_path, f"{safe_keyword}.txt")

                # txt 파일로 저장 (제목 없이, 큰따옴표 없이)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)

            # 통계 파일 저장
            stats_file = os.path.join(output_path, '통계.txt')
            with open(stats_file, 'w', encoding='utf-8') as f:
                f.write(f"원고 수정 결과 통계\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(f"저장됨: {len(results)}개\n")
                f.write(f"  - 기준 충족 ✅: {len([r for r in results if r['status'] == 'success'])}개\n")
                f.write(f"  - 기준 미달 ⚠️: {len([r for r in results if r['status'] == 'partial'])}개\n\n")

                f.write(f"{'=' * 80}\n")
                f.write(f"개별 원고 통계\n")
                f.write(f"{'=' * 80}\n\n")

                for r in results:
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
                            icon = '✅' if actual == target else '❌'
                            f.write(f"  나머지 [{kw}]: {actual}회 (목표: {target}회) {icon}\n")

                    # 조각키워드
                    after_조각키워드 = r.get('after_조각키워드', {})
                    if after_조각키워드:
                        for kw, data in after_조각키워드.items():
                            target = data.get('target', 0)
                            actual = data.get('actual', 0)
                            icon = '✅' if actual == target else '❌'
                            f.write(f"  조각 [{kw}]: {actual}회 (목표: {target}회) {icon}\n")

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

            self.log(f"✅ 저장 완료: {output_folder}/")
            self.log("")
            self.log("=" * 100)
            self.log("✅ 모든 작업 완료!")
            self.log("=" * 100)

            success_count = len([r for r in results if r['status'] == 'success'])
            partial_count = len([r for r in results if r['status'] == 'partial'])

            self.log(f"📊 총 {len(results)}개 원고 저장")
            self.log(f"   - 기준 충족 ✅: {success_count}개")
            self.log(f"   - 기준 미달 ⚠️: {partial_count}개")

            # 통계
            avg_before = sum(r['before_chars'] for r in results) / len(results)
            avg_after = sum(r['after_chars'] for r in results) / len(results)
            self.log(f"📏 평균 글자수: {avg_before:.0f}자 → {avg_after:.0f}자")

            첫문단_달성 = sum(1 for r in results if r['after_첫문단_통키워드'] == 2)
            self.log(f"🎯 첫문단 통키워드 2회 달성: {첫문단_달성}/{len(results)} ({첫문단_달성/len(results)*100:.1f}%)")

            문장시작_달성 = sum(1 for r in results if r['after_문장시작'] == 2)
            self.log(f"🎯 문장시작 2개 달성: {문장시작_달성}/{len(results)} ({문장시작_달성/len(results)*100:.1f}%)")

            # 완료 메시지
            self.progress['value'] = 100
            self.progress_label.config(text="완료!")

            messagebox.showinfo(
                "완료",
                f"✅ 원고 수정 완료!\n\n"
                f"저장: {len(results)}개\n"
                f"  - 기준 충족 ✅: {success_count}개\n"
                f"  - 기준 미달 ⚠️: {partial_count}개\n\n"
                f"저장 위치: {output_folder}/"
            )

        except Exception as e:
            self.log(f"\n❌ 오류 발생: {e}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("오류", f"처리 중 오류가 발생했습니다:\n{e}")

        finally:
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.is_processing = False


def main():
    """메인 실행"""
    root = tk.Tk()
    app = ManuscriptGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

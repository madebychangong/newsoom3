"""
블로그 원고 최적화 GUI 프로그램
- 엑셀/TXT 파일 선택
- 드래그 앤 드롭 지원
- 진행 상황 표시
- 결과 미리보기
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
from pathlib import Path
import threading

# 상대 import 처리
try:
    from search_optimizer import SearchOptimizer
    import pandas as pd
except ImportError:
    messagebox.showerror("오류", "필요한 패키지가 설치되어 있지 않습니다.\npip install -r requirements.txt")
    sys.exit(1)


class BlogOptimizerGUI:
    """블로그 최적화 GUI 애플리케이션"""

    def __init__(self, root):
        self.root = root
        self.root.title("블로그 검색 최적화")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # 옵티마이저 초기화 (나중에 설정됨)
        self.optimizer = None

        # 변수
        self.input_file = tk.StringVar()
        self.output_folder = tk.StringVar(value="자동 (입력 파일과 같은 폴더)")
        self.keyword = tk.StringVar()
        self.brand = tk.StringVar()
        self.use_ai = tk.BooleanVar(value=False)
        self.gemini_api_key = tk.StringVar()

        # UI 구성
        self.setup_ui()

    def setup_ui(self):
        """UI 구성"""
        # 스타일 설정
        style = ttk.Style()
        style.theme_use('clam')

        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 타이틀
        title_label = ttk.Label(
            main_frame,
            text="🎯 블로그 검색 최적화",
            font=("맑은 고딕", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        subtitle_label = ttk.Label(
            main_frame,
            text="검색 노출 최적화 · 키워드 띄어쓰기 · 금칙어 치환",
            font=("맑은 고딕", 9)
        )
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))

        # 1. 파일 선택
        row = 2
        ttk.Label(main_frame, text="📁 입력 파일:", font=("맑은 고딕", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )

        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)

        self.file_entry = ttk.Entry(file_frame, textvariable=self.input_file, width=50)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        ttk.Button(file_frame, text="파일 선택", command=self.browse_file).grid(row=0, column=1)

        # 파일 형식 안내
        ttk.Label(
            main_frame,
            text="지원 형식: .xlsx (엑셀), .txt (텍스트)",
            font=("맑은 고딕", 8),
            foreground="gray"
        ).grid(row=row+1, column=1, columnspan=2, sticky=tk.W)

        # 2. 키워드 (선택)
        row += 2
        ttk.Label(main_frame, text="🔑 키워드:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.keyword, width=50).grid(
            row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        ttk.Label(
            main_frame,
            text="TXT 파일: 자동 추출 가능 (빈칸 가능) | 엑셀: 자동 인식",
            font=("맑은 고딕", 8),
            foreground="gray"
        ).grid(row=row+1, column=1, columnspan=2, sticky=tk.W)

        # 3. 브랜드 (선택)
        row += 2
        ttk.Label(main_frame, text="🏷️ 브랜드:", font=("맑은 고딕", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.brand, width=50).grid(
            row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        ttk.Label(
            main_frame,
            text="선택사항 (해시태그에 포함됩니다)",
            font=("맑은 고딕", 8),
            foreground="gray"
        ).grid(row=row+1, column=1, columnspan=2, sticky=tk.W)

        # 4. AI 재구성 (선택)
        row += 2
        ai_frame = ttk.Frame(main_frame)
        ai_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        self.ai_checkbox = ttk.Checkbutton(
            ai_frame,
            text="🤖 AI 자연스러운 재구성 사용 (Gemini API)",
            variable=self.use_ai,
            command=self.toggle_ai_options
        )
        self.ai_checkbox.grid(row=0, column=0, sticky=tk.W)

        # API 키 입력 (AI 체크 시에만 표시)
        row += 1
        self.api_key_frame = ttk.Frame(main_frame)
        self.api_key_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.api_key_frame, text="   API Key:", font=("맑은 고딕", 9)).grid(
            row=0, column=0, sticky=tk.W, padx=(20, 5)
        )
        self.api_key_entry = ttk.Entry(self.api_key_frame, textvariable=self.gemini_api_key, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        ttk.Label(
            self.api_key_frame,
            text="또는 환경변수 GEMINI_API_KEY 설정",
            font=("맑은 고딕", 8),
            foreground="gray"
        ).grid(row=1, column=1, sticky=tk.W, padx=5)

        # 초기에는 숨김
        self.api_key_frame.grid_remove()

        # 구분선
        row += 1
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20
        )

        # 5. 실행 버튼
        row += 1
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=10)

        self.optimize_button = ttk.Button(
            button_frame,
            text="🚀 최적화 시작",
            command=self.start_optimization,
            width=20
        )
        self.optimize_button.grid(row=0, column=0, padx=5)

        ttk.Button(
            button_frame,
            text="📂 출력 폴더 열기",
            command=self.open_output_folder,
            width=20
        ).grid(row=0, column=1, padx=5)

        # 6. 진행 상황
        row += 1
        ttk.Label(main_frame, text="진행 상황:", font=("맑은 고딕", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5)
        )

        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))

        # 7. 로그
        row += 1
        log_frame = ttk.LabelFrame(main_frame, text="실행 로그", padding="5")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        main_frame.rowconfigure(row, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=80,
            font=("맑은 고딕", 9),
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 초기 로그
        self.log("=" * 80)
        self.log("블로그 검색 최적화 v1.0")
        self.log("=" * 80)
        self.log("✅ 시스템 준비 완료")
        self.log("📝 파일을 선택하고 '최적화 시작' 버튼을 눌러주세요")
        self.log("")

    def log(self, message):
        """로그 출력"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def toggle_ai_options(self):
        """AI 옵션 표시/숨김"""
        if self.use_ai.get():
            self.api_key_frame.grid()
            self.log("🤖 AI 재구성 모드 활성화")
        else:
            self.api_key_frame.grid_remove()
            self.log("ℹ️ AI 재구성 모드 비활성화")

    def browse_file(self):
        """파일 선택 대화상자"""
        filename = filedialog.askopenfilename(
            title="원고 파일 선택",
            filetypes=[
                ("지원 파일", "*.xlsx *.txt"),
                ("엑셀 파일", "*.xlsx"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        if filename:
            self.input_file.set(filename)
            self.log(f"📁 파일 선택됨: {os.path.basename(filename)}")

    def open_output_folder(self):
        """출력 폴더 열기"""
        if not self.input_file.get():
            messagebox.showwarning("경고", "먼저 파일을 선택해주세요.")
            return

        input_path = self.input_file.get()
        output_folder = os.path.dirname(input_path)

        if os.path.exists(output_folder):
            os.startfile(output_folder) if sys.platform == 'win32' else os.system(f'open "{output_folder}"')
        else:
            messagebox.showerror("오류", "출력 폴더를 찾을 수 없습니다.")

    def start_optimization(self):
        """최적화 시작"""
        # 유효성 검사
        if not self.input_file.get():
            messagebox.showerror("오류", "파일을 선택해주세요.")
            return

        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("오류", "파일을 찾을 수 없습니다.")
            return

        # AI 사용 시 API 키 확인
        if self.use_ai.get():
            api_key = self.gemini_api_key.get() or os.getenv('GEMINI_API_KEY')
            if not api_key:
                messagebox.showerror(
                    "오류",
                    "Gemini API 키가 필요합니다.\n\n"
                    "1. API 키를 입력하거나\n"
                    "2. 환경변수 GEMINI_API_KEY를 설정하세요."
                )
                return

        # 옵티마이저 초기화 (AI 옵션 적용)
        try:
            use_ai = self.use_ai.get()
            api_key = self.gemini_api_key.get() if self.gemini_api_key.get() else None
            self.optimizer = SearchOptimizer(use_ai=use_ai, gemini_api_key=api_key)
            if use_ai:
                self.log("🤖 AI 재구성 모드로 초기화됨")
        except Exception as e:
            messagebox.showerror("오류", f"옵티마이저 초기화 실패:\n{str(e)}")
            return

        # 버튼 비활성화
        self.optimize_button.config(state='disabled')
        self.progress.start()

        # 로그 초기화
        self.log("")
        self.log("=" * 80)
        self.log("🚀 최적화 시작")
        self.log("=" * 80)

        # 별도 스레드에서 실행
        thread = threading.Thread(target=self.run_optimization)
        thread.daemon = True
        thread.start()

    def run_optimization(self):
        """최적화 실행 (백그라운드)"""
        try:
            input_path = self.input_file.get()
            ext = os.path.splitext(input_path)[1].lower()

            if ext == '.xlsx':
                self.optimize_excel(input_path)
            elif ext == '.txt':
                self.optimize_txt(input_path)
            else:
                self.log(f"❌ 지원하지 않는 파일 형식: {ext}")
                messagebox.showerror("오류", f"지원하지 않는 파일 형식입니다: {ext}")
                return

        except Exception as e:
            self.log(f"❌ 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"최적화 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.progress.stop()
            self.optimize_button.config(state='normal')

    def optimize_excel(self, input_file):
        """엑셀 최적화"""
        self.log(f"📊 엑셀 파일 처리 중: {os.path.basename(input_file)}")

        # 엑셀 읽기
        df = pd.read_excel(input_file)
        self.log(f"✅ {len(df)}개 행 발견")

        # 출력 파일
        output_file = input_file.replace('.xlsx', '_검색최적화.xlsx')

        # 각 행 처리
        for idx, row in df.iterrows():
            keyword = row.get('키워드', '')
            brand = row.get('브랜드', '') or self.brand.get()
            original_text = row.get('원고', '')

            self.log(f"[{idx+1}/{len(df)}] {keyword} 처리 중...")

            # 최적화
            result = self.optimizer.optimize_for_search(original_text, keyword, brand)

            # 결과 저장
            df.at[idx, '원고'] = result['optimized_text']
            if result.get('optimized_title'):
                df.at[idx, '제목'] = result['optimized_title']

            df.at[idx, '글자수(공백포함)'] = result['optimized_length']
            df.at[idx, '통키워드 반복수'] = f"{keyword} : {result['keyword_count']}"
            df.at[idx, '추천_해시태그'] = ' '.join(['#' + tag for tag in result['hashtags'][:10]])
            df.at[idx, '최적화_변경사항'] = '\n'.join(result['changes'])

            self.log(f"  ✅ {result['optimized_length']}자 | 키워드: {result['keyword_count']}회")

        # 저장
        df.to_excel(output_file, index=False)

        self.log("")
        self.log("=" * 80)
        self.log("✅ 최적화 완료!")
        self.log("=" * 80)
        self.log(f"💾 저장됨: {os.path.basename(output_file)}")

        messagebox.showinfo("완료", f"최적화가 완료되었습니다!\n\n{len(df)}개 원고 처리\n저장: {os.path.basename(output_file)}")

    def optimize_txt(self, input_file):
        """TXT 최적화"""
        self.log(f"📝 TXT 파일 처리 중: {os.path.basename(input_file)}")

        # 읽기
        with open(input_file, 'r', encoding='utf-8') as f:
            original_text = f.read()

        self.log(f"✅ 원본 글자수: {len(original_text)}자")

        # 키워드 추출
        keyword = self.keyword.get()
        if not keyword:
            # 자동 추출 시도
            lines = original_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('#'):
                    line = line.lstrip('#').strip()
                    for suffix in ['관련해서', '에 대해', '관련', '사용', '후기', '정보']:
                        if suffix in line:
                            line = line.split(suffix)[0].strip()
                            break
                    keyword = line
                    break

        if not keyword:
            keyword = "키워드"

        self.log(f"🔑 키워드: {keyword}")

        # 최적화
        brand = self.brand.get()
        result = self.optimizer.optimize_for_search(original_text, keyword, brand)

        self.log(f"✅ 최종 글자수: {result['optimized_length']}자 ({result['length_diff']:+d}자)")
        self.log(f"✅ 키워드 출현: {result['keyword_count']}회")

        # 저장
        output_file = input_file.replace('.txt', '_최적화.txt')

        with open(output_file, 'w', encoding='utf-8') as f:
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
            if result.get('optimized_title'):
                f.write("📌 제목\n")
                f.write("-" * 80 + "\n")
                f.write(f"{result['optimized_title']}\n\n")
            f.write("=" * 80 + "\n")
            f.write("📝 최적화된 원고\n")
            f.write("=" * 80 + "\n\n")
            f.write(result['optimized_text'])

        self.log(f"\n💾 저장됨: {os.path.basename(output_file)}")

        messagebox.showinfo("완료", f"최적화가 완료되었습니다!\n\n{result['optimized_length']}자\n키워드: {result['keyword_count']}회\n저장: {os.path.basename(output_file)}")


def main():
    """메인 실행"""
    root = tk.Tk()
    app = BlogOptimizerGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

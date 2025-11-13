"""
블로그 원고 키워드 띄어쓰기 최적화 (템플릿 패턴 기반)
- 검색 노출 최적화
- 키워드+조사 제거
- 키워드 출현 2-3회로 감소
- AI 재구성 (선택)
"""

import re
import random
import os
from typing import Dict, List, Optional
import pandas as pd
from blog_optimizer import BlogOptimizer


class SearchOptimizer(BlogOptimizer):
    """검색 노출 최적화 (키워드 띄어쓰기 + 키워드 감소)"""

    def __init__(self, forbidden_words_file='금칙어 리스트.xlsx', use_ai=False, gemini_api_key=None):
        """
        초기화

        Args:
            forbidden_words_file: 금칙어 파일 경로
            use_ai: AI 재구성 사용 여부 (기본: False)
            gemini_api_key: Gemini API 키 (없으면 환경변수 GEMINI_API_KEY 사용)
        """
        super().__init__(forbidden_words_file)
        self.use_ai = use_ai
        self.ai_rewriter = None

        # AI 재구성 활성화
        if self.use_ai:
            try:
                from ai_rewriter import AIRewriter
                self.ai_rewriter = AIRewriter(api_key=gemini_api_key)
                print("✅ AI 재구성 모드 활성화")
            except Exception as e:
                print(f"⚠️ AI 재구성 초기화 실패: {e}")
                print("   환경변수 GEMINI_API_KEY를 설정하거나 gemini_api_key 파라미터를 전달하세요.")
                self.use_ai = False

    def remove_hashtag_title(self, text: str) -> str:
        """# 제목 삭제"""
        lines = text.split('\n')
        if lines and lines[0].strip().startswith('#'):
            return '\n'.join(lines[1:]).strip()
        return text

    def remove_keyword_particles(self, text: str, keyword: str) -> str:
        """
        키워드+조사 제거 또는 수정

        전략:
        1. 키워드+를/을 → 키워드 + 동사 또는 제거
        2. 키워드+가/이 → 키워드 또는 문장 재구성
        3. 키워드+에 → 키워드 관해서 또는 제거
        4. 키워드+라는 → 키워드 라는 (띄어쓰기)
        """
        if not keyword or pd.isna(keyword):
            return text

        modified = text

        # 1. 키워드+를/을 처리
        # "키워드를 먹고" → "키워드 먹고"
        # "키워드를 최근에" → "키워드 라는 걸 최근에"
        pattern1 = f'({re.escape(keyword)})[를을]\\s+'
        modified = re.sub(pattern1, f'{keyword} ', modified)

        # 2. 키워드+가/이 처리
        # "키워드가 좋다" → "키워드 좋다" 또는 "키워드 먹으면"
        pattern2 = f'({re.escape(keyword)})[가이]\\s+'

        def replace_subject(match):
            # 랜덤하게 제거 또는 대체
            choices = [
                f'{keyword} ',
                f'{keyword} 먹으면 ',
                f'{keyword} 사용하면 ',
            ]
            return random.choice(choices)

        modified = re.sub(pattern2, replace_subject, modified)

        # 3. 키워드+에 처리
        # "키워드에 대해" → 문장 삭제 또는 "키워드 관해서"
        pattern3 = f'({re.escape(keyword)})에\\s+대해'
        modified = re.sub(pattern3, '', modified)  # 제목이므로 삭제

        pattern3b = f'({re.escape(keyword)})에\\s+'
        modified = re.sub(pattern3b, f'{keyword} 관해서 ', modified)

        # 4. 키워드+의 처리
        pattern4 = f'({re.escape(keyword)})의\\s+'
        modified = re.sub(pattern4, f'{keyword} 관련 ', modified)

        # 5. 키워드+라는 → 키워드 라는 (띄어쓰기)
        pattern5 = f'({re.escape(keyword)})라는'
        modified = re.sub(pattern5, f'{keyword} 라는', modified)

        # 6. 키워드+는/은 일부 제거
        # 너무 많으면 일부만 제거
        pattern6 = f'({re.escape(keyword)})[는은]\\s+'
        count = len(re.findall(pattern6, modified))
        if count > 1:
            # 첫 번째만 제거
            modified = re.sub(pattern6, f'{keyword} ', modified, count=1)

        return modified

    def reduce_keyword_frequency(self, text: str, keyword: str, target_count: int = 2) -> str:
        """
        키워드 출현 횟수 줄이기

        5-6회 → 2-3회로 감소
        """
        if not keyword or pd.isna(keyword):
            return text

        current_count = text.count(keyword)

        if current_count <= target_count:
            return text

        # 초과된 키워드를 대명사나 다른 표현으로 교체
        remove_count = current_count - target_count

        # 키워드를 찾아서 일부만 제거
        lines = text.split('\n')
        removed = 0

        for i, line in enumerate(lines):
            if removed >= remove_count:
                break

            if keyword in line:
                # 이 줄의 키워드를 대명사로 교체
                line_keyword_count = line.count(keyword)

                # 교체할 횟수 계산
                to_replace = min(line_keyword_count - 1, remove_count - removed) if line_keyword_count > 1 else (1 if removed < remove_count and i > 0 else 0)

                if to_replace > 0:
                    # 키워드 위치 찾기
                    import re
                    positions = [m.start() for m in re.finditer(re.escape(keyword), line)]

                    # 뒤에서부터 교체 (앞쪽 키워드는 유지)
                    new_line = line
                    replaced_count = 0

                    for pos in reversed(positions[1:] if line_keyword_count > 1 else positions):
                        if replaced_count >= to_replace:
                            break

                        # 키워드 뒤에 뭐가 있는지 확인
                        after_keyword = new_line[pos + len(keyword):pos + len(keyword) + 5] if pos + len(keyword) < len(new_line) else ""

                        # "키워드 라는" → 그냥 제거 (라는 유지)
                        if after_keyword.startswith(' 라는'):
                            # 키워드만 제거, 공백과 '라는'은 유지하되 자연스럽게
                            new_line = new_line[:pos] + '이런 거' + new_line[pos + len(keyword):]
                        # "키워드를/가/는" 등 조사 → 이미 2단계에서 처리됐어야 하므로 단순 제거
                        elif after_keyword and after_keyword[0] in ['를', '을', '가', '이', '는', '은', '에', '의']:
                            new_line = new_line[:pos] + '이거' + new_line[pos + len(keyword):]
                        else:
                            # 일반적인 경우 "이거"로 교체
                            new_line = new_line[:pos] + '이거' + new_line[pos + len(keyword):]

                        replaced_count += 1

                    lines[i] = new_line
                    removed += replaced_count

        return '\n'.join(lines)

    def optimize_for_search(self, text: str, keyword: str, brand: str = '') -> Dict:
        """
        검색 노출 최적화

        작업 순서:
        1. # 제목 삭제
        2. 키워드+조사 제거
        3. 키워드 출현 감소 (2-3회)
        4. 금칙어 치환
        5. AI 표현 제거
        6. AI 재구성 (선택)
        """
        if pd.isna(text) or not text:
            return {
                'optimized_text': '',
                'original_length': 0,
                'optimized_length': 0,
                'keyword_count': 0,
                'changes': []
            }

        original_text = text
        original_length = len(text)
        all_changes = []

        # 1. # 제목 삭제
        text = self.remove_hashtag_title(text)
        all_changes.append('✅ # 제목 삭제')

        # 2. 키워드+조사 제거
        before_particle = text.count(keyword)
        text = self.remove_keyword_particles(text, keyword)
        after_particle = text.count(keyword)
        all_changes.append(f'✅ 키워드+조사 제거 ({before_particle}회)')

        # 3. 키워드 출현 감소 (2-3회 목표)
        text = self.reduce_keyword_frequency(text, keyword, target_count=2)
        final_count = text.count(keyword)
        all_changes.append(f'✅ 키워드 출현 감소 → {final_count}회')

        # 4. 금칙어 치환
        text, forbidden_changes = self.replace_forbidden_words(text)
        if forbidden_changes:
            all_changes.append(f'✅ 금칙어 {len(forbidden_changes)}개 치환')

        # 5. AI 패턴 다양화
        text, ai_changes = self.diversify_ai_patterns(text)
        if ai_changes:
            all_changes.append(f'✅ AI 표현 {len(ai_changes)}개 수정')

        # 6. 자연스러운 변형
        text = self.add_natural_variations(text)

        # 7. AI 재구성 (선택)
        if self.use_ai and self.ai_rewriter:
            try:
                print(f"  🤖 AI 재구성 중...")
                ai_text = self.ai_rewriter.rewrite(text, keyword)
                if ai_text and len(ai_text) > 100:  # 유효한 결과인지 확인
                    text = ai_text
                    all_changes.append('✅ AI 자연스러운 재구성 완료')
                    # AI 재구성 후 키워드 개수 재확인
                    final_count = text.count(keyword)
            except Exception as e:
                print(f"  ⚠️ AI 재구성 오류: {e}")
                all_changes.append('⚠️ AI 재구성 실패 (원본 유지)')

        # 8. 해시태그 생성
        hashtags = self.generate_hashtags(keyword, brand)

        # 9. 제목 생성
        title = self.generate_title(keyword, text)

        return {
            'optimized_text': text,
            'optimized_title': title,
            'original_length': original_length,
            'optimized_length': len(text),
            'keyword_count': final_count,
            'changes': all_changes,
            'hashtags': hashtags,
            'length_diff': len(text) - original_length
        }

    def process_excel(self, input_file: str, output_file: str = None) -> str:
        """
        엑셀 파일 일괄 처리
        """
        if output_file is None:
            output_file = input_file.replace('.xlsx', '_검색최적화.xlsx')

        # 엑셀 읽기
        df = pd.read_excel(input_file)

        # 새 컬럼 추가
        if '최적화_원고' not in df.columns:
            df['최적화_원고'] = ''
        if '키워드_출현' not in df.columns:
            df['키워드_출현'] = 0
        if '변경사항' not in df.columns:
            df['변경사항'] = ''
        if '추천_해시태그' not in df.columns:
            df['추천_해시태그'] = ''

        # 각 행 처리
        for idx, row in df.iterrows():
            keyword = row.get('키워드', '')
            brand = row.get('브랜드', '')
            text = row.get('원고', '')

            if pd.isna(text) or not text:
                continue

            # 최적화
            result = self.optimize_for_search(text, keyword, brand)

            # 결과 저장
            df.at[idx, '최적화_원고'] = result['optimized_text']
            df.at[idx, '키워드_출현'] = result['keyword_count']
            df.at[idx, '변경사항'] = '\n'.join(result['changes'])
            df.at[idx, '추천_해시태그'] = ' '.join(['#' + tag for tag in result['hashtags'][:10]])

        # 저장
        df.to_excel(output_file, index=False)
        return output_file

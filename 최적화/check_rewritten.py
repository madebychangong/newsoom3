#!/usr/bin/env python3
"""수정 후 원고 3개 회사 기준 체크"""

import re
from collections import Counter

def count_keyword(text: str, keyword: str) -> int:
    """키워드 카운팅 (띄어쓰기 기준)"""
    if not keyword:
        return 0
    pattern = rf'{re.escape(keyword)}(?=\s|[^\w가-힣]|$)'
    return len(re.findall(pattern, text))

def get_first_paragraph(text: str) -> str:
    """첫 문단 추출"""
    paragraphs = text.split('\n\n')
    return paragraphs[0].strip() if paragraphs else ""

def get_rest_paragraphs(text: str) -> str:
    """첫 문단 제외한 나머지"""
    paragraphs = text.split('\n\n')
    return '\n\n'.join(paragraphs[1:]).strip() if len(paragraphs) > 1 else ""

def count_sentences_starting_with(text: str, keyword: str) -> int:
    """키워드로 시작하는 문장(줄) 개수"""
    if not keyword:
        return 0
    count = 0
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith(keyword):
            count += 1
    return count

def count_subkeywords(text: str, exclude_keywords: list) -> int:
    """서브키워드 목록 수 (2회 이상 등장하는 단어)"""
    words = re.findall(r'[가-힣]+', text)
    word_counter = Counter(words)

    subkeywords = set()
    for word, count in word_counter.items():
        if count >= 2 and len(word) >= 2 and word not in exclude_keywords:
            subkeywords.add(word)

    return len(subkeywords)

# 3개 원고
manuscripts = [
    {
        'keyword': '잠실유방외과',
        'text': '''잠실유방외과에 대해 궁금해서 글을 올립니다. 잠실유방외과 관련 정보를 찾고 있는데, 갱년기 증상 때문에 너무 힘든 요즘입니다.

50대 초반 주부인데, 작년부터 갑자기 열이 오르는 증상이 심해지면서 일상생활이 어려워졌어요. 밤에 잠도 제대로 못 자고 감정 기복도 심해져서 가족들에게 미안한 마음입니다. '나도 이제 늙어가는구나'라는 생각에 우울해지기도 하고요.

산부인과에서 호르몬 치료 상담을 받았지만, 암 위험성 같은 부작용이 걱정되어 망설여지네요. 석류즙이나 칡즙, 한약도 먹어봤지만 뚜렷한 효과는 보지 못했습니다. 그러다 친구가 잠실유방외과 얘기를 해줬는데, 건강기능식품 효과에 대한 의구심도 들고, 온라인 후기는 너무 많아서 뭘 믿어야 할지 혼란스럽습니다.

혹시 잠실유방외과에 방문해보신 분 계실까요? 솔직한 경험담을 듣고 싶습니다. 효과를 보셨다면 어떤 점이 좋았는지, 갱년기 증상 완화에 도움이 되는 다른 방법이나 제품이 있다면 추천 부탁드립니다. 정보 공유 좀 해주세요.'''
    },
    {
        'keyword': '여성호르몬 가슴',
        'text': '''여성호르몬 가슴 때문에 답답한 마음에 글을 올립니다. 여성호르몬 가슴 관련 정보를 찾다가 너무 막막해서 이렇게 넋두리하게 되었어요. 갱년기가 시작되면서 일상생활이 예전 같지 않다는 걸 느껴요. 인터넷에 여성호르몬 가슴 정보는 넘쳐나지만, 어떤 게 진짜인지 분간하기 어려워서 직접 경험자분들의 이야기를 듣고 싶어요.

갱년기 증상인지 얼굴이 갑자기 화끈거리고 땀이 쏟아지는 횟수가 늘었어요. 특히 밤에 열 때문에 잠을 설치는 일이 잦아졌고, 사소한 일에도 짜증이 솟고 우울해지네요. 가족들에게 괜히 미안한 마음이 들어요. 갱년기, 나이 듦에 대한 생각에 더 울적해지기도 하고요.

산부인과에서는 여성호르몬 치료를 권했지만, 암 위험성 같은 부작용 때문에 망설여져요. 석류즙이나 칡즙을 꾸준히 챙겨 먹었지만, 눈에 띄는 변화는 없었어요. 한약도 잠깐 먹었지만 비용 부담이 커서 그만뒀고요.

그러다 비슷한 시기를 겪는 친구로부터 여성호르몬 건강기능식품에 대한 이야기를 들었어요. 이걸로 효과를 볼 수 있을까 반신반의하며 찾아봤는데, 온라인에는 홍보 글만 가득한 것 같아서 뭘 믿어야 할지 혼란스러워요.

혹시 갱년기 때문에 여성호르몬 관련 건강기능식품 드셔보신 분 계신가요? 어떤 제품을 드셨고, 효과는 어떠셨는지 솔직한 후기를 듣고 싶어요. 부작용은 없었는지, 얼마나 꾸준히 먹어야 효과를 볼 수 있는지도 궁금합니다.

영양제가 아니더라도 갱년기 증상 완화에 도움이 되는 다른 방법이 있다면 추천 부탁드려요. 예전처럼 편안한 일상을 되찾고 싶습니다. 작은 정보라도 좋으니 공유해주시면 정말 감사하겠습니다.'''
    },
    {
        'keyword': '여성헤어라인 모발이식',
        'text': '''여성헤어라인 모발이식에 관심이 생겨 글을 올립니다. 여성헤어라인 모발이식 알아보면서 효과가 정말 있을지 궁금해졌어요. 갱년기 때문에 힘든 시기에 알게 되었거든요.

얼굴이 화끈거리고 잠도 제대로 못 자서 너무 피곤한 요즘이에요. 감정 기복도 심하고 자꾸 우울해지네요. 호르몬 치료는 부작용이 걱정되고, 석류즙이나 칡즙은 효과를 못 봤고, 한약은 부담스러워서 포기했어요.

그러다 친구가 여성 헤어라인 모발이식 얘기를 해줘서 알아보고 있는데, 수원에 있는 모발이식병원 중에 특히 모모가 여자 헤어라인 모발이식을 잘하는지 궁금합니다. 후기도 많고 지점도 많다고 들었는데, 실제로 받아보신 분들의 경험이 궁금해요. 모발이식 후 관리도 중요한 것 같은데, 모모에서 모발이식 받으신 분들의 후기가 궁금하네요.

솔직히 건강식품은 반신반의하게 되고, 인터넷 후기는 너무 홍보 같아서 뭘 믿어야 할지 모르겠어요. 혹시 여성헤어라인 모발이식 직접 받아보신 분 계시면 효과는 어떠셨는지, 부작용은 없었는지 솔직한 조언 부탁드립니다. 다른 갱년기 관리 방법이나 제품 추천도 해주시면 정말 감사하겠습니다. 정보 공유 좀 해주세요!'''
    }
]

print("="*100)
print("수정 후 원고 3개 - 회사 기준 체크")
print("="*100)

for i, ms in enumerate(manuscripts, 1):
    keyword = ms['keyword']
    text = ms['text']

    # 조각 키워드 추출
    pieces = keyword.split() if ' ' in keyword else []

    # 제외할 키워드 리스트
    exclude = [keyword] + pieces

    # 글자수 (공백/줄바꿈 제외)
    chars = len(text.replace(' ', '').replace('\n', ''))

    # 첫 문단
    first_para = get_first_paragraph(text)
    first_para_keyword_count = count_keyword(first_para, keyword)

    # 통키워드로 시작하는 문장
    sentence_starts = count_sentences_starting_with(text, keyword)

    # 나머지 부분
    rest = get_rest_paragraphs(text)

    # 나머지 부분 통키워드
    rest_whole = count_keyword(rest, keyword)

    # 나머지 부분 조각키워드
    rest_pieces = {}
    for piece in pieces:
        rest_pieces[piece] = count_keyword(rest, piece)

    # 서브키워드
    subkeywords = count_subkeywords(text, exclude)

    print(f"\n[원고 {i}] 키워드: {keyword}")
    print(f"  {'✅' if 300 <= chars <= 900 else '❌'} 글자수: {chars}자 (목표: 300~900자)")
    print(f"  {'✅' if first_para_keyword_count == 2 else '❌'} 첫문단 통키워드: {first_para_keyword_count}회 (목표: 2회)")
    print(f"  {'✅' if sentence_starts == 2 else '❌'} 통키워드 문장 시작: {sentence_starts}개 (목표: 2개)")
    print(f"  나머지 부분 통키워드: {rest_whole}회")
    if pieces:
        print(f"  나머지 부분 조각키워드:")
        for piece, count in rest_pieces.items():
            print(f"    - {piece}: {count}회")
    print(f"  서브키워드: {subkeywords}개")

    # 자연스러움 평가
    print(f"\n  🤔 자연스러움:")
    if '잠실유방외과' in keyword:
        print(f"     - 갱년기 얘기하다가 갑자기 유방외과? → 부자연스러움")
    elif '모발이식' in keyword:
        print(f"     - 갱년기 얘기하다가 갑자기 모발이식? → 부자연스러움")
    elif '여성호르몬' in keyword:
        print(f"     - 갱년기 + 여성호르몬은 자연스러운 조합")
        if '가슴' in keyword:
            print(f"     - 하지만 '여성호르몬 가슴'이라는 표현이 다소 어색함")

print("\n" + "="*100)
print("결론:")
print("  - 회사 기준(글자수, 첫문단, 문장시작)은 대체로 맞춤")
print("  - 하지만 원본 원고 주제(갱년기)와 키워드가 안 맞으면 억지스러움")
print("  - 해결: 키워드 주제에 맞게 원고 내용을 일부 수정해야 함")
print("="*100)

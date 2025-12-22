#!/usr/bin/env python3
"""Gemini API 모델 확인"""

import os
import google.generativeai as genai

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ GEMINI_API_KEY 환경변수를 설정해주세요.")
    print("   export GEMINI_API_KEY='your-api-key'")
    exit(1)

print(f"✅ API 키 있음 (길이: {len(api_key)}자)")

try:
    genai.configure(api_key=api_key)

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("사용 가능한 Gemini 모델:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    models = list(genai.list_models())

    if not models:
        print("⚠️ 사용 가능한 모델이 없습니다.")
        print("   API 키가 유효한지 확인하세요.")
    else:
        for i, model in enumerate(models, 1):
            print(f"\n{i}. {model.name}")
            print(f"   Display name: {model.display_name}")
            print(f"   Description: {model.description[:100]}..." if len(model.description) > 100 else f"   Description: {model.description}")

            # generateContent를 지원하는 모델만 표시
            if 'generateContent' in model.supported_generation_methods:
                print(f"   ✅ generateContent 지원 (텍스트 생성 가능)")

    # 추천 모델
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("블로그 글 재구성 추천 모델:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    recommended = [
        'models/gemini-1.5-flash',
        'models/gemini-1.5-pro',
        'models/gemini-pro',
        'models/gemini-1.0-pro'
    ]

    for model_name in recommended:
        try:
            # 모델이 존재하는지 확인
            model = genai.GenerativeModel(model_name)
            print(f"✅ {model_name} - 사용 가능")
        except Exception as e:
            print(f"❌ {model_name} - 사용 불가 ({str(e)[:50]}...)")

except Exception as e:
    print(f"\n❌ API 오류: {e}")
    print(f"\n오류 타입: {type(e).__name__}")

    if '404' in str(e):
        print("\n💡 해결 방법:")
        print("   1. API 키가 유효한지 확인")
        print("   2. https://aistudio.google.com/app/apikey 에서 새 키 발급")
        print("   3. API 키 권한 확인 (Generative Language API 활성화)")

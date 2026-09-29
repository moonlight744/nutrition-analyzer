import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import json

# 페이지 기본 설정
st.set_page_config(page_title="식품 영양성분 & 원재료 딥애널라이저", page_icon="🥗", layout="centered")

st.title("🥗 식품 영양성분 & 원재료 딥애널라이저")
st.write("제품 뒷면의 **영양성분표**나 **원재료명** 사진을 올려주시면 식품영양학적 분석 결과를 알려드립니다.")

# Sidebar에서 API 키 입력 받기
api_key = st.sidebar.text_input("Google AI Studio API Key", type="password")

uploaded_file = st.file_uploader("영양성분표 또는 원재료명 사진을 업로드하세요", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드한 제품 이미지", use_container_width=True)

    if st.button("영양학적 분석 시작하기"):
        if not api_key:
            st.error("왼쪽 사이드바에 Google AI Studio API Key를 입력해주세요.")
        else:
            with st.spinner("AI 영양사가 성분표와 원재료를 분석 중입니다..."):
                try:
                    # Google GenAI 클라이언트 생성
                    client = genai.Client(api_key=api_key)

                    system_instruction = """
                    당신은 식품영양학 및 식품위생학 분야의 전문 영양사이자 데이터 분석가입니다. 
                    사용자가 제공한 식품의 영양성분표 및 원재료명 사진을 분석하여 사용자가 쉽게 이해하고 건강 관리에 활용할 수 있도록 정밀 분석 결과를 제공합니다.
                    """

                    json_schema = {
                        "type": "OBJECT",
                        "properties": {
                            "product_name": {"type": "STRING"},
                            "nutrition_grade": {"type": "STRING"},
                            "one_line_summary": {"type": "STRING"},
                            "key_nutrition": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "ingredient_analysis": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "ingredient": {"type": "STRING"},
                                        "risk_level": {"type": "STRING"},
                                        "description": {"type": "STRING"}
                                    },
                                    "required": ["ingredient", "risk_level", "description"]
                                }
                            },
                            "recommended_for": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "caution_for": {"type": "ARRAY", "items": {"type": "STRING"}}
                        },
                        "required": ["product_name", "nutrition_grade", "one_line_summary", "key_nutrition", "ingredient_analysis", "recommended_for", "caution_for"]
                    }

                    # Gemini 3.8 Flash 최신 모델 사용
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[image, "이 식품의 영양성분표와 원재료명을 분석해줘."],
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=json_schema,
                        ),
                    )

                    result = json.loads(response.text)

                    st.success("분석 완료!")
                    st.subheader(f"📌 제품명(추정): {result.get('product_name', '알 수 없음')}")
                    
                    grade = result.get('nutrition_grade', 'N/A')
                    st.metric(label="영양 종합 등급", value=grade)
                    
                    st.info(f"💡 **한 줄 총평:** {result.get('one_line_summary')}")

                    st.write("### 📊 주요 영양성분 포인트")
                    for point in result.get('key_nutrition', []):
                        st.write(f"- {point}")

                    st.write("### 🔍 주요 원재료 및 첨가물 리스트")
                    for item in result.get('ingredient_analysis', []):
                        risk = item.get('risk_level')
                        badge = "🟢" if risk == "안전" else ("🟡" if risk == "주의" else "🔴")
                        st.write(f"{badge} **{item.get('ingredient')}** ({risk}): {item.get('description')}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("### ⭕ 이런 분께 추천해요")
                        for rec in result.get('recommended_for', []):
                            st.write(f"- {rec}")
                    with col2:
                        st.write("### ⚠️ 이런 분은 주의하세요")
                        for cau in result.get('caution_for', []):
                            st.write(f"- {cau}")

                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")
import os
import json
import re
import PIL.Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
당신은 한국의 중/고등학교 내신 시험지(주로 영어 영역) 이미지를 분석하여 정밀하게 구조화하는 전문 AI 데이터 엔지니어입니다.

[분석 작업]
제공된 시험지 이미지(각 페이지별)를 시각적으로 분석하여 문항 번호, 지시문, 제시문(텍스트/조건 박스), 선택지, 배점 등을 식별하고 아래 [Target JSON Schema]에 맞게 변환하십시오.

[분석 지침]
1. 레이아웃 파악: 시험지는 보통 좌/우 2단으로 구성되어 있습니다. 인간이 읽는 순서(좌측 상단 -> 좌측 하단 -> 우측 상단 -> 우측 하단)를 엄격히 준수하여 문항을 추출하십시오.
2. 문항 및 배점: 문항 번호와 배점(예: 4.5점)을 정확히 매핑하십시오.
3. Stimulus(자극물/제시문) 분류:
   - 일반 지문: {"type": "text_box", "content": "..."}
   - <조건>, [우리말] 박스: {"type": "condition_box", "content": "..."}
   - 이미지(도표, 그림): {"type": "image", "src": "./images/..."}
     * 이미지 객체 발견 시, JSON에는 시각적 내용을 기반으로 src를 할당하십시오.
4. Choices(선택지): "①~⑤" 기호로 시작하는 텍스트를 `choices` 배열에 넣으십시오.
5. Sub-questions(새끼 문제): 계층 구조를 가진 문제는 `sub_questions` 배열에 넣으십시오.

[Target JSON Schema]
{
  "exam_metadata": { "school_name": "", "year": 0, "semester": "", "exam_type": "", "grade": "", "subject": "" },
  "questions": [
    {
      "q_number": "String",
      "q_type": "multiple_choice | subjective",
      "points": 0.0,
      "instruction": "String",
      "stimulus": [ { "type": "text_box | condition_box | image", "content_or_src": "String" } ],
      "choices": ["String"],
      "sub_questions": [ { "sub_q_number": "", "instruction": "", "points": 0.0 } ]
    }
  ]
}

응답은 마크다운 코드 블록(```json ... ```) 안에 유효한 JSON 포맷만을 출력해야 하며, 부연 설명은 일절 포함하지 마십시오.
"""

def process_text_to_json(raw_text):
    """
    OCR로 추출된 원시 텍스트를 받아서 JSON으로 구조화합니다.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)

    prompt = f"아래 제공된 'OCR 추출 텍스트'를 분석하여 문항별로 구조화하십시오. 2단 레이아웃임을 감안하여 읽기 순서를 정정하고, 이미지 마커가 있다면 적절히 포함하십시오.\n\n[OCR 추출 텍스트]\n{raw_text}"

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1
        )
    )

    return _parse_json_from_response(response.text)

def _parse_json_from_response(output_text):
    match = re.search(r'```json\s*(.*?)\s*```', output_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = output_text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON response:\n", json_str)
        raise e

def process_images_to_json(image_paths):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일이나 환경 변수를 확인해주세요.")

    client = genai.Client(api_key=api_key)

    # 이미지 파일들을 Gemini가 읽을 수 있는 형식으로 변환
    contents = []
    for path in image_paths:
        img = PIL.Image.open(path)
        contents.append(img)

    # 이미지를 포함하여 프롬프트 실행
    response = client.models.generate_content(
        model='gemini-2.5-flash', # 혹은 gemini-1.5-pro (안정적)
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1
        )
    )

    return _parse_json_from_response(response.text)


import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
당신은 한국의 중/고등학교 내신 시험지(주로 영어 영역) 데이터를 파싱하고 구조화하는 전문 AI 데이터 엔지니어입니다.

[작업 목표]
제공되는 '원시 시험지 텍스트 데이터'를 분석하여, 문항 번호, 지시문, 제시문(텍스트/조건 박스), 선택지, 배점 등을 분리하고 아래 제공된 [Target JSON Schema]에 맞춰 완벽한 JSON 포맷으로 변환하십시오.

[분석 지침 및 주의사항]
1. 문항 분리 기준: 텍스트는 좌에서 우, 위에서 아래 순서(2단 편집 기준)로 정렬되어 제공됩니다. 숫자로 시작하는 번호(예: "1.", "2.") 또는 "서술형 1" 등을 기준으로 독립된 문항을 식별하십시오.
2. 배점 추출: 지시문 끝이나 문항 번호 근처에 있는 "[4.5점]", "(6.0점)" 등의 표기를 찾아 숫자로 변환하여 `points` 필드에 소수점으로 입력하십시오.
3. Stimulus(자극물/제시문) 분류:
   - 일반적인 본문은 `{"type": "text_box", "content": "..."}`로 묶으십시오.
   - `<조건>`, `[우리말]` 등 특정 조건이 부여된 박스나 텍스트는 `{"type": "condition_box", "content": "..."}`로 분류하여 HWP 변환 시 구별될 수 있게 하십시오.
   - [이미지 첨부됨: ./images/...] 와 같은 텍스트 마커가 보이면 `{"type": "image", "src": "./images/..."}` 객체를 배열에 추가하십시오.
4. Choices(선택지): "①", "②", "③", "④", "⑤" 기호로 시작하는 텍스트는 객관식 선택지로 인식하여 `choices` 배열에 순서대로 넣으십시오. 주관식/서술형인 경우 빈 배열 `[]`을 반환하십시오.
5. Sub-questions(새끼 문제): 하나의 큰 지시문 아래에 "1-1.", "(1)" 처럼 딸려있는 문제들은 `sub_questions` 배열에 객체 형태로 구조화하십시오.

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

응답은 마크다운 코드 블록(```json ... ```) 안에 유효한 JSON 포맷만을 출력해야 하며, 분석 과정이나 부연 설명은 일절 포함하지 마십시오.
"""

def process_text_to_json(raw_text):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일이나 환경 변수를 확인해주세요.")

    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=raw_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1
        )
    )
    
    output_text = response.text
    
    # Extract JSON from Markdown block if present
    match = re.search(r'```json\s*(.*?)\s*```', output_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = output_text.strip()
        
    try:
        parsed_json = json.loads(json_str)
        return parsed_json
    except json.JSONDecodeError as e:
        print("Failed to parse JSON response:\n", json_str)
        raise e

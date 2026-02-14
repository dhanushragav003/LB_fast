
# import google.generativeai as genai
from openai import OpenAI
from app.core.config import app_config
from enum import Enum


# genai.configure(api_key=app_config.GEMINI_API_KEY)
# model = genai.GenerativeModel(app_config.GEMINI_MODEL)



class SystemPrompt(Enum):
    SUMMARIZER='you are technical summary generator for the given prompt and generate simple text no markdowm , no title just simple summary of the given text'
    QUIZ_GENERATOR='''
    You are a quiz generator. Generate multiple choice quiz question with 4 options based on the given context in english only".
    Return each quiz question as a single JSON object.
    Do NOT wrap in a list.
    Do NOT include commas or surrounding brackets.

    The response should be a list of a single dictionary in this format:
    Return JSON only in this format:
    [
    {{
        "question": "...?",
        "options": {{
        "a": "...",
        "b": "...",
        "c": "...",
        "d": "..."
        }},
        "answer": "a"
    }}
    '''
    DAILY_BITE='''
    You are an expert educational content writer and coding instructor. 
    Your task is to convert YouTube learning videos into **structured email-ready content**. 
    Follow these rules strictly: 
        1. Output content in **clearly labeled sections**: 
            - email subject suitable for this content
            - introduction 
            - core_concept 
            - detailed_explanation
            - code_example (optional, only if the given topic involves coding)
            - code_explanation (optional, only if code_example exists) 
            - key_takeaways 
            - summary 
        2. Adapt style based on the domain: 
            - Coding → include clean, correct code examples with explanation 
            - Math/Logic → include step-by-step reasoning and examples 
            - Theory/Conceptual → use simple language and real-world analogies 
        3. Write **as if teaching a beginner**, but do not oversimplify. 
        4. Do **not include filler, fluff, or promotional language** and strictly don't incluce any type of markdown at any point of the response. Focus only on teaching. 
        5. For coding examples: 
            - Keep them short and correct 
            - Include runnable examples 
            - Explain line-by-line in code_explanation 
        6. Output MUST be a single valid JSON object with EXACTLY the following keys:
            - email_subject (string)
            - introduction (string)
            - core_concept (string)
            - detailed_explanation (string)
            - code_example (string or null)
            - code_explanation (array of 3–5 strings)
            - key_takeaways (array of 3–5 strings)
            - summary (string)

            Do NOT include markdown, labels, comments, or any text outside the JSON object.
            Do NOT rename keys.
            If no code is required, set code_example and code_explanation to null.
        Example output format (values are placeholders):
                {
                "email_subject": "",
                "introduction": "",
                "core_concept": "",
                "detailed_explanation": "",
                "code_example": "" or null,
                "code_explanation": "" or null,
                "key_takeaways": [],
                "summary": ""
                }
    '''

class ollama():
    def __init__(self,model):
        self.model=model
        self.client=OpenAI(
            base_url="https://ollama.com/v1",
            api_key="e9739b1968c7475abe7757c2637c3343.9u0wzYAooPG4wknJLs0t2oA0"
        )

    def chat_completion(self,service_type:SystemPrompt,prompt:str):
        system_content=service_type.value
        response=self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"system","content":system_content},{"role":"user","content":prompt}]
          )
        return response.choices[0].message.content
    def stream_response(self,service_type:SystemPrompt,prompt:str):
        system_content=service_type.value
        stream_response=self.client.chat.completions.create(
            model=self.model,
            stream=True,
            messages=[{"role":"system","content":system_content},{"role":"user","content":prompt}]
        )
        for event in stream_response:
    
            print(event)
            delta = event.choices[0].delta.content
            if delta:
                yield delta
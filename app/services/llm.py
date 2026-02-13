

from app.core.config import ENV , app_config
from app.schemas.email import BiteEmail
from app.integrations import ai
from app.helpers.mail_template import validate_generated_email
import json
import asyncio
import re



quiz_data_test= [
                {
                    "question": "Which logical operator returns `True` only if both operands are `True`?",
                    "option": {
                    "a": "AND",
                    "b": "OR",
                    "c": "NOT",
                    "d": "XOR"
                    },
                    "answer": "a"
                }
        ]
        
def generate_quiz(chapter_text,context,total_question):
    prompt = f'''
    Generate {total_question} multiple choice quiz question with 4 options based on the topic in english only : "{chapter_text} related to {context} ".
    The response should be a list of a single dictionary in this format:
    [
      {{
        "question": "...?",
        "option": {{
          "a": "...",...
        }},
        "answer": "a"
      }}
    ]
    '''
    try:
        if ENV == 'local': return None,quiz_data_test
        print("*"*10)
        print("LLM Called!......")
        print("*"*10)
        response = ai.model.generate_content(prompt)
        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)  # remove opening ```
            raw_text = raw_text.rstrip("`").rstrip()              # remove trailing ```
        quiz_data = json.loads(raw_text)    
        return None,quiz_data
    except Exception as e:
        return e,None


ai_client=ai.ollama("gpt-oss:120b")
async def generate_text(systemprompt: ai.SystemPrompt,userprompt: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        lambda: ai_client.chat_completion(systemprompt, userprompt)
    )
    
async def summary_generator(text: str) -> str:
    """
    Async wrapper around synchronous chat_completion.
    Allows streaming chapter summaries without blocking FastAPI.
    """
    if not text:
        return ""
    return await generate_text(ai.SystemPrompt.SUMMARIZER,text)
    

async def sse_generate_quiz(chapter_text, context, total_questions):
    user_prompt = f"""
        Generate ONE multiple-choice question based on the following text.

        Context: {context}

        Text:
        {chapter_text}

        Return a single JSON object in this format:
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
    """

    try:
        for i in range(total_questions):
            quiz = await generate_text(
                ai.SystemPrompt.QUIZ_GENERATOR,
                user_prompt
            )
            payload = {
              "index": i,
              "quiz": json.loads(quiz)
            }
            print(payload)
            yield f"data: {json.dumps(payload)}\n\n"

    except asyncio.CancelledError:
        return

    except Exception as e:
        yield f"event: error\ndata: {str(e)}\n\n"
        
async def generate_content(user_prompt):
    
    generated_content= await generate_text(ai.SystemPrompt.DAILY_BITE,user_prompt)
    return generated_content

async def generate_bitemail(userprompt) -> BiteEmail:
    feedback_prompt = None

    for curr_try in range(1, app_config.MAX_RETRY + 1):
        try:
            print(f"Attempt {curr_try}/{app_config.MAX_RETRY}")
            print(feedback_prompt)
            generated_content = await generate_content(
                feedback_prompt if feedback_prompt else userprompt
            )
            print(f"{generated_content = }")
            # generated_content = '{\n  "email_subject": "Understanding Numbers and Math in JavaScript – From Basics to Accurate Money Calculations",\n  "introduction": "In this lesson we explore how JavaScript handles numbers, basic arithmetic operators, order of operations, floating‑point quirks, and the best ways to perform reliable monetary calculations.",\n  "core_concept": "JavaScript uses familiar symbols for addition (+), subtraction (-), multiplication (*), and division (/). It follows standard operator precedence, supports brackets to control evaluation order, and provides Math methods such as Math.round for rounding. Because floating‑point numbers can be imprecise, especially with money, the recommended practice is to work in integer cents and convert back to dollars at the end.",\n  "detailed_explanation": "You can type expressions directly in the browser console: 2 + 2 yields 4, 10 - 3 yields 7, 10 * 3 yields 30, and 10 / 2 yields 5. Multiple operations follow precedence: multiplication and division happen before addition and subtraction, e.g., 1 + 1 * 3 results in 4 because 1 * 3 is evaluated first. Brackets override this order, so (1 + 1) * 3 gives 6. When dealing with decimals, JavaScript may produce tiny errors due to binary representation (e.g., 0.1 + 0.2 ≈ 0.30000000000000004). To avoid such errors in financial calculations, store amounts as whole cents (integers), perform all arithmetic, then divide by 100 to display dollars. Finally, use Math.round (or Math.floor / Math.ceil) to round to the nearest integer when needed, remembering that the method is case‑sensitive.",\n  "code_example": "const sockPrice = 1090; // $10.90 in cents\\nconst basketballPrice = 2095; // $20.95 in cents\\nconst shipping = 499; // $4.99 in cents\\nconst taxRate = 0.1; // 10% tax\\n\\n// Subtotal for products (2 socks + 1 basketball)\\nconst subtotalCents = sockPrice * 2 + basketballPrice;\\n\\n// Add shipping cost\\nconst totalBeforeTaxCents = subtotalCents + shipping;\\n\\n// Calculate tax and round to nearest cent\\nconst taxCents = Math.round(totalBeforeTaxCents * taxRate);\\n\\n// Final total in cents, then convert to dollars\\nconst totalCents = totalBeforeTaxCents + taxCents;\\nconst totalDollars = (totalCents / 100).toFixed(2);\\n\\nconsole.log(`Total: $${totalDollars}`);",\n  "code_explanation": [\n    "Define each price in cents so the numbers are whole integers, avoiding floating‑point errors.",\n    "Calculate the product subtotal by multiplying the sock price by 2 and adding the basketball price.",\n    "Add the shipping cost to the subtotal, then compute tax by multiplying by the tax rate and rounding with Math.round.",\n    "Combine the tax with the previous total to get the final amount in cents, then divide by 100 and format to two decimal places for display.",\n    "Output the formatted total using console.log."\n  ],\n  "key_takeaways": [\n    "JavaScript arithmetic uses the same symbols as standard math and follows operator precedence.",\n    "Brackets can change the evaluation order and have the highest precedence.",\n    "Floating‑point numbers can introduce tiny inaccuracies; use integers (cents) for money.",\n    "Math.round, Math.floor, and Math.ceil are essential for rounding results.",\n    "Always convert cents back to dollars for user‑facing output, typically with toFixed(2)."\n  ],\n  "summary": "JavaScript handles basic math intuitively, but for precise financial calculations you should work in integer cents, apply proper rounding, and only then convert back to dollars."\n}'
            bite_mail = validate_generated_email(generated_content)
            return bite_mail

        except Exception as e:
            feedback_prompt = f"""
                    Your previous JSON output was invalid.
                    Please fix the errors below and provide ONLY the corrected JSON.

                    Error Details:
                    {str(e)}

                    Original Context:
                    {userprompt}
                """
            # continue retry loop

    # If we exit the loop, retries are exhausted
    raise Exception("LLM failed to produce valid JSON after multiple attempts.")


async def fetch_Bite_email(resource_title,chapter_title,content)->BiteEmail:
    user_prompt=f'''
        Generate structured teaching content for a learning email using the following details: 
        Title: {resource_title}
        Chapter Title: {chapter_title}
        Transcript: {content} 
        Target Audience: [Beginners / Students / Developers / Exam Prep / General Learners] 
        Instructions: 
            - Use the system rules to generate content in **sections only**. 
            - Include code_example and code_explanation **only if the topic is coding-related**. 
            - Keep explanations clear, concise, and beginner-friendly. 
            - Provide 3–5 key takeaways as a bullet list. 
            - Make summary a 1–2 sentence recap. 
            - Output **only the structured sections**, without additional commentary.
    '''
    try:
        bitemail=await generate_bitemail(user_prompt)
        return bitemail
    except Exception as e:
        raise RuntimeError("Failed to generate Bite email") from e
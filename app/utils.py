import json
from flask import current_app

def categorize_decision(decision):
    api_key = current_app.config.get('AI_API_KEY')
    provider = current_app.config.get('AI_PROVIDER')
    base_url = current_app.config.get('AI_BASE_URL')

    if not api_key:
        return "General"

    try:
        if provider in ['openai', 'grok', 'groq']:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            model = "gpt-3.5-turbo"
            if provider == 'grok':
                model = "grok-2-1212"
            elif provider == 'groq':
                model = "llama-3.3-70b-versatile"
            
            prompt = f"""
            Categorize the following decision into a single short category (1-3 words).
            Examples: Career, Personal Finance, Health, Education, Travel, Shopping, Technology.

            Decision Title: {decision.title}
            
            Return ONLY the category name. No JSON, no preamble, no explanation.
            """
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Categorization Error: {e}")
    
    return "General"

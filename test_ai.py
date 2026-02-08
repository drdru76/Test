import os
import sys
from dotenv import load_dotenv

def test_config():
    print("--- AI API Key Diagnostic Tool ---")
    
    # Load .env file
    if os.path.exists('.env'):
        print("[✓] .env file found.")
        load_dotenv()
    else:
        print("[!] .env file NOT found. Please create one based on .env.example")
        return

    api_key = os.getenv('AI_API_KEY')
    provider = os.getenv('AI_PROVIDER', 'openai')
    base_url = os.getenv('AI_BASE_URL')

    if not api_key:
        print("[!] AI_API_KEY is missing in .env")
        return
    
    print(f"[✓] AI_PROVIDER set to: {provider}")
    if base_url:
        print(f"[✓] AI_BASE_URL set to: {base_url}")
    print(f"[✓] AI_API_KEY found: {api_key[:5]}...{api_key[-4:] if len(api_key) > 4 else ''}")

    if provider in ['openai', 'grok', 'groq']:
        try:
            from openai import OpenAI
            print(f"[...] Connecting to {provider.upper()}...")
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            model = "gpt-3.5-turbo"
            if provider == 'grok':
                model = "grok-2-1212"
            elif provider == 'groq':
                model = "llama-3.3-70b-versatile"

            # Simple test call
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say 'Connection Successful'"}],
                max_tokens=10
            )
            result = response.choices[0].message.content.strip()
            print(f"[✓] {provider.upper()} Response: {result}")
            print("\nSUCCESS: Your API key is working correctly!")
            
        except ImportError:
            print("[!] 'openai' library not installed. Run: pip install openai")
        except Exception as e:
            print(f"[!] API Error: {e}")
            print("\nPlease check if your API key is valid and has sufficient credits.")

if __name__ == "__main__":
    test_config()

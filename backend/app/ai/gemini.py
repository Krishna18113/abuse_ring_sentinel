import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.ai.prompts import SYSTEM_PROMPT
from app.ai.schemas import RiskExplanation

# Load environment variables
load_dotenv()

def query_gemini_explanation(evidence_package: dict) -> dict:
    """Sends the sanitized evidence package to Gemini and returns a structured risk explanation."""
    
    # 1. Fetch API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
        
    # 2. Initialize the GenAI Client
    client = genai.Client(api_key=api_key)
    
    # 3. Serialize evidence package as contents
    evidence_json = json.dumps(evidence_package, indent=2)
    
    # 4. Determine model name
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    
    # 5. Generate structured content
    response = client.models.generate_content(
        model=model_name,
        contents=f"Evidence Package:\n{evidence_json}",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RiskExplanation,
            temperature=0.1 # Low temperature to ensure high grounding accuracy
        )
    )
    
    # 6. Parse response text
    if not response.text:
        raise ValueError("Empty response received from Gemini API.")
        
    explanation_dict = json.loads(response.text)
    return explanation_dict

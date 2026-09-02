import os
import json
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.ai.prompts import SYSTEM_PROMPT
from app.ai.schemas import RiskExplanation

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# High-speed active candidate models in priority order
CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
    "gemini-flash-lite-latest",
    "gemini-3.6-flash"
]

def query_gemini_explanation(evidence_package: dict) -> dict:
    """Sends the sanitized evidence package to Gemini with fast failover and returns a structured risk explanation."""
    
    # 1. Fetch API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
        
    # 2. Initialize the GenAI Client
    client = genai.Client(api_key=api_key)
    
    # 3. Serialize evidence package as contents
    evidence_json = json.dumps(evidence_package, indent=2)
    
    last_error = None
    for model_name in CANDIDATE_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=f"Evidence Package:\n{evidence_json}",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=RiskExplanation,
                    temperature=0.1
                )
            )
            
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}. Trying next candidate...")
            last_error = e
            continue
            
    raise ValueError(f"All candidate Gemini models failed. Last error: {last_error}")

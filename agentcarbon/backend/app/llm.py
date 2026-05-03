# app/llm.py
import requests
import os

# Note: The Groq API URL mirrors the OpenAI endpoint structure
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# We recommend using the 70B model or 8B model. 
MODEL_NAME = "llama-3.3-70b-versatile"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = (
    "You are AgentCarbon, an expert sustainability assistant. "
    "You receive extracted invoice fields and carbon emissions. "
    "Explain the results in simple English and give 2–3 specific, practical "
    "suggestions to reduce emissions. Do not change any numeric values. "
    "Output EXTREMELY CLEAN PLAIN TEXT ONLY. Do not use asterisks (**), bolding, or markdown formatting."
)


def generate_explanation(
    fields: dict, 
    emissions: dict, 
    history: list, 
    ml_predicted_co2: float | None = None
) -> str | None:
    
    if not GROQ_API_KEY:
        print("❌ Warning: GROQ_API_KEY environment variable is missing!")
        return "Insight generation currently unavailable: missing LLM configuration."
    
    calculated_co2 = emissions.get("total_kgco2", "N/A")
    
    ml_context = ""
    if ml_predicted_co2 is not None:
        ml_context = (
            f"The calculated emissions are {calculated_co2}, but the ML model suggests {ml_predicted_co2}. "
            "Briefly explain why there might be a difference (e.g., seasonal factors or typical consumption patterns for this facility). "
        )

    user_msg = (
        f"Current fields: {fields}\n"
        f"Current emissions: {emissions}\n"
        f"ML Predicted CO2: {ml_predicted_co2}\n"
        f"Past records (may be empty): {history}\n\n"
        "1) Briefly summarize this bill's emissions.\n"
        "2) Mention if emissions seem higher or lower than usual based on history.\n"
        f"{ml_context}\n"
        "3) Give 2–3 concrete tips to reduce future emissions."
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.3,
        "max_tokens": 512
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"❌ LLM Error: {exc}")
        
        # Adding a bit more detailed trace for debugging Groq API requests specifically
        if hasattr(exc, 'response') and exc.response is not None:
            print(f"Response Body: {exc.response.text}")
            
        return "An error occurred while calling the LLM API."

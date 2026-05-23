import os
from .ai.gemini import GeminiLLM

def get_llm():
    """
    Factory function to get the configured LLM.
    Currently hardcoded to Gemini, but can fallback if the API is unavailable.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        return GeminiLLM()
    # elif provider == "openai":
    #     from .ai.openai import OpenAILLM
    #     return OpenAILLM()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def process_inbound_message(message_body: str, platform: str, sender: str) -> str:
    """
    Processes an inbound message using the AI.
    """
    platform = (platform or "unknown").lower()
    sender = sender or "unknown"
    llm = get_llm()
    
    system_prompt = f"""You are Jarvis, a highly intelligent and capable AI assistant. 
You are currently communicating with a user on {platform} (Sender ID/Number: {sender}).
Your goal is to be helpful, concise, and professional. 
IMPORTANT: Your responses will NOT be sent immediately. They will be placed in a queue for the system owner to review and approve.
Draft the best possible response to the user's message."""

    return llm.generate_response(system_prompt=system_prompt, user_message=message_body)

def process_vision_input(image_path: str, context_message: str = "") -> str:
    """
    Foundation for screen sharing. Analyzes an image and returns a text summary/action plan.
    """
    llm = get_llm()
    system_prompt = """You are Jarvis. The user has provided an image/screenshot of their screen.
Analyze the image carefully. Identify key applications open, the context of what the user is doing, and if there are any obvious issues or tasks they might need help with.
If the user provided a context message, answer their question based on the image."""
    
    return llm.analyze_image(system_prompt=system_prompt, image_path=image_path, user_message=context_message)

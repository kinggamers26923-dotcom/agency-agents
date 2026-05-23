import os
import time
from .base import BaseLLM
from google import genai
from google.genai import types

class GeminiLLM(BaseLLM):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not set, switching to local fallback response.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"  # Standard model for fast reasoning

    def _local_fallback(self, system_prompt: str, user_message: str) -> str:
        return (
            "I can't reach the Gemini API right now, so I'm using a local fallback response. "
            "Please check your internet connection or your GEMINI_API_KEY setting. "
            f"Received message: {user_message}"
        )

    def _try_model(self, model: str, system_prompt: str, user_message: str) -> str:
        response = self.client.models.generate_content(
            model=model,
            contents=[user_message],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7
            )
        )
        return response.text

    def generate_response(self, system_prompt: str, user_message: str) -> str:
        if self.client is None:
            return self._local_fallback(system_prompt, user_message)

        models_to_try = [self.model_name, "gemini-2.5-mini", "gemini-2.1"]
        for index, model in enumerate(models_to_try):
            try:
                return self._try_model(model, system_prompt, user_message)
            except Exception as e:
                print(f"Gemini model {model} error: {e}")
                if index < len(models_to_try) - 1:
                    time.sleep(2)
                    continue
                return self._local_fallback(system_prompt, user_message)

    def analyze_image(self, system_prompt: str, image_path: str, user_message: str = "") -> str:
        # Foundation for vision - assumes image exists locally
        try:
            # Note: For google-genai, we can upload files using client.files.upload or pass raw bytes.
            # We'll use the upload method for simplicity here.
            myfile = self.client.files.upload(file=image_path)
            contents = [myfile]
            if user_message:
                contents.append(user_message)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.5
                )
            )
            return response.text
        except Exception as e:
            print(f"Error analyzing image with Gemini: {e}")
            return "I could not analyze the screen/image."

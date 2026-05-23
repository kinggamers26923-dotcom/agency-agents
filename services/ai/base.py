from abc import ABC, abstractmethod

class BaseLLM(ABC):
    """
    Abstract base class for all LLM implementations.
    This ensures our assistant is LLM-agnostic and can easily switch models.
    """

    @abstractmethod
    def generate_response(self, system_prompt: str, user_message: str) -> str:
        """
        Generates a text response from the LLM.
        """
        pass

    @abstractmethod
    def analyze_image(self, system_prompt: str, image_path: str, user_message: str = "") -> str:
        """
        Foundation for vision/screen-sharing capabilities.
        Analyzes an image and returns a text response.
        """
        pass

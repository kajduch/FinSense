import requests

class OllamaClient:
    def __init__(
        self,
        model: str = "qwen3:8b",
        host: str = "http://localhost:11434"
    ):
        self.model = model
        self.host = host.rstrip("/")

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        json_schema: dict | None = None,
        num_ctx: int = 8192,    
        num_predict: int = 4096   
    ) -> str:

        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
       
            "options": {
                "num_ctx": num_ctx,        
                "num_predict": num_predict, 
                "temperature": 0.3,
                "repeat_penalty": 1.15,    
            }
        }

        if system:
            data["system"] = system


        if json_schema:
            data["format"] = json_schema


        response = requests.post(
            f"{self.host}/api/generate",
            json=data,
            timeout=300
        )

        response.raise_for_status()

        result = response.json()

        return result["response"]
import openai

class OpenAiService:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        openai.api_key = self.api_key
        openai.api_base = "https://openrouter.ai/api/v1"
        

    def call_openai(self, request_id: int):
        response = openai.ChatCompletion.create(
            model="perplexity/llama-3.1-sonar-small-128k-online",
            messages=[
                {"role": "user", "content": f" request_id: {request_id}, return a object with three fields: request_id, title, issue, solution , return nothing esle but the object, i i don't want your comment or thoughts, just the object, please, just the object"},
            ],
           
        )
        print(response['choices'][0]['message']['content'])

# Example usage
openai_service = OpenAiService(api_key='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')

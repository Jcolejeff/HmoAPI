class OpenAiService:
    def __init__(self, api_key: str, app_id: str) -> None:
        self.api_key = api_key
        self.app_id = app_id

    def call_openai(self):
        pass

openai_service = OpenAiService(api_key='xxx', app_id='ddd')
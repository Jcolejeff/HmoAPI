from typesense import Client
from decouple import config



class TypesenseClient(Client):
    def __init__(self, timeout=config('TYPESENSE_CONN_TIMEOUT')) -> None:
        self.connection_timeout_seconds = timeout
        super().__init__(
            {
                'nodes': [{
                    'host': config('TYPESENSE_HOST') or 'localhost',
                    'port': config('TYPESENSE_PORT') or 8108,
                    'protocol': config('TYPESENSE_PROTOCOL') or 'http'
                }],
                'api_key': config('TYPESENSE_API_KEY'),
                'connection_timeout_seconds': float(self.connection_timeout_seconds)
            }
        )



       
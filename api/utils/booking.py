class BookingService:
    def __init__(self, api_key: str, app_id: str) -> None:
        self.api_key = api_key
        self.app_id = app_id

    def create_booking(self):
        pass

booking_service = BookingService(api_key='xxx', app_id='ddd')
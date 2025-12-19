from schemas import NotificationRead
from datetime import datetime
from pydantic import ValidationError

class MockNotification:
    def __init__(self):
        self.id = 1
        self.user_id = 1
        self.type = "info"
        self.title = "Test"
        self.body = "Body"
        self.notification_metadata = {"key": "value"}
        self.is_read = False
        self.created_at = datetime.now()

class MockNotificationStringMetadata:
    def __init__(self):
        self.id = 3
        self.user_id = 1
        self.type = "info"
        self.title = "Test"
        self.body = "Body"
        self.notification_metadata = '{"event_id": 1}' # Test string input
        self.is_read = False
        self.created_at = datetime.now()

print("\nTesting object with String Metadata...")
try:
    obj = MockNotificationStringMetadata()
    model = NotificationRead.model_validate(obj)
    print("Success:", model)
    print("Metadata Type:", type(model.notification_metadata))
except ValidationError as e:
    print("Validation Error with String:", e)

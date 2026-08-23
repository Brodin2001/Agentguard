from datetime import datetime


class AuditLog:
    def __init__(self):
        self.events = []

    def record(self, event):
        event = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            **event
        }

        self.events.append(event)

    def get_events(self):
        return self.events
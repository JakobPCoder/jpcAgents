

class Chat:
    def __init__(self):

        self.messages = []

    def create_message(self, role: str, message: str):
        return {"role": role, "content": message}

    def add_message_to_chat(self, message):
        self.messages.append(message)

    def send_message(self, message: str, role: str = "user"):
        new_message = self.create_message(role, message)
        self.add_message_to_chat(new_message)
        
    def get_latest_messages(self, message_count: int = 8) -> str:
        # Get the total number of messages in the conversation history
        chat_len = len(self.messages)

        # Check if there are no messages
        if not self.messages or chat_len == 0:
            print("No recent messages available")
            return ""

        # Limit the number of messages to retrieve
        num_messages = min(chat_len, message_count)

        # Get the latest messages
        latest_messages = self.messages[-num_messages:]

        return latest_messages
    
        






import pandas as pd
from bs4 import BeautifulSoup
from phiWrapper import PhiWrapper


class PhiChat():
    """
    A class to manage and simulate a chat conversation using the Phi model.

    Attributes:
        phi_api (PhiWrapper): An instance of PhiWrapper to handle Phi model interactions.
        convo_start (pd.DataFrame): A DataFrame to store the initial conversation setup.
        messages (pd.DataFrame): A DataFrame to store ongoing conversation messages.
        pre_prompt (str): A string that sets the context and rules for the chat simulation.

    The class initializes with a predefined conversation start between a CEO, an Assistant, and a User, 
    stored in `convo_start`. It facilitates creating new messages and generating chat prompts 
    based on the conversation history and initial setup.
    """
        

    def __init__(self, phi_api: PhiWrapper):
        # Initialize PhiWrapper instance for model interactions
        self.phi_api = phi_api

        self.eos_token = phi_api.tokenizer.eos_token

        # Create DataFrame for initial conversation structure
        self.convo_start = pd.DataFrame(columns=["id", "roll", "message"])

        # Create DataFrame for ongoing messages
        self.messages = pd.DataFrame(columns=["id", "roll", "message"])

        # Set up the initial context for the conversation
        self.pre_prompt = '''
The ASSISTANT gives helpful, detailed, and polite answers to the user's questions.
The following text is a chat in html format, where the "Assistant" is talking to the "User".
Expand the chat as naturaly as possible why staying true to the facts, don't make stuff up! don't repeat yourself!
Only expand the chat by one message!
'''
        # Define initial conversation starters as a list of dictionaries
        convo_start = [
            {"id": 0, "roll": "CEO", "message": "Hey, please be very polite and try your best to be helpful today. The user you are talking to is very important to us! You should answer in detail and in length!"},
            {"id": 1, "roll": "Assistant", "message": "Of course boss! I will make sure to help them with all their needs! Do you have any questions or hints before the meeting?"},
            {"id": 2, "roll": "CEO", "message": "Are you sure you are qualified for this?"},
            {"id": 3, "roll": "Assistant", "message": "Of course I am, and I think you know so. I bring a rich blend of skills to the table, from mastering programming languages like C++, Python, Java, and HLSL to excelling in software design, computer hardware, mathematics with MATLAB, and expertise in fields such as embedded systems, signal processing, machine learning, history, social sciences, and medical knowledge. My passion lies in open source projects, where I craft clean, well-documented code."},
            {"id": 4, "roll": "CEO", "message": "Ok! He is coming in right now, make sure to answer all questions! I will leave you two alone now."},
            {"id": 5, "roll": "User", "message": "Good day! May I come in?"},
            {"id": 6, "roll": "Assistant", "message": "Sure! Nice to have you! Let me take your jacket. Let's go to my office."},
            {"id": 7, "roll": "User", "message": "For sure, after you!"},
            {"id": 8, "roll": "Assistant", "message": "Please sit down, make yourself comfortable."},
            {"id": 9, "roll": "User", "message": "Thank you! So I got a lot of questions..."},
            {"id": 10, "roll": "Assistant", "message": "Please ask! I'm here to help you with anything needed. I will provide you with all the details you need!"}
        ]

        # Concatenate initial conversation starters into the convo_start DataFrame
        self.convo_start = pd.concat([self.convo_start, pd.DataFrame(convo_start)])      


    def create_message(self, id: int, roll: str, message: str):
        """
        Creates and adds a new message to the conversation.

        Args:
            id (int): The unique identifier for the message.
            roll (str): The role of the sender (e.g., 'User', 'Assistant').
            message (str): The content of the message.

        This method constructs a new DataFrame row with the provided message details
        and appends it to the 'self.messages' DataFrame. The 'ignore_index' flag is set to True
        to ensure the index continuity of the DataFrame.
        """
        # Create a new DataFrame from the provided message information
        new_message = pd.DataFrame([{"id": id, "roll": roll, "message": message}])

        # Append the new message to the existing DataFrame and reset the index
        self.messages = pd.concat([self.messages, new_message], ignore_index=True)



    def get_message_from_response(self, response: str, message_id: int) -> dict:
        """
        Extract a message with a specific ID from the response text.

        Args:
            response (str): The response text containing multiple chat messages.
            message_id (int): The ID of the message to extract.

        Returns:
            dict or None: A dictionary representing the extracted message with the specified ID.
                        Returns None if the message with the given ID is not found.

        This function uses BeautifulSoup to parse the HTML and extract the message with the specified ID.
        It returns the message as a dictionary containing 'id', 'roll', and 'message' fields.
        """
        soup = BeautifulSoup(response, 'html.parser')

        message_element = soup.find('div', {'id': f'id{message_id}'})
        print(soup)
        print(message_element)
        
        if message_element:
            roll = message_element['class'][0]
            message_text = message_element.find('p').get_text()
            return {"id": message_id, "roll": roll, "message": message_text}, message_text
        else:
            return None
        

    def message_to_html(self, message_row: pd.Series) -> str:
        """
        Converts a message row to its HTML representation.

        Args:
            message_row (pd.Series): A pandas Series object representing a row from a DataFrame.

        Returns:
            str: A string containing the HTML representation of the message.

        Example:
            Suppose `message_row` is a pandas Series like this:
            ```
            message_row = pd.Series({
                "id": 123,
                "roll": "User",
                "message": "Hello, how can I help?"
            })
            ```
            Calling `message_to_html(message_row)` will return the following HTML:
            ```
            <div id="id123" class="User">
                <p>Hello, how can I help?</p>
            </div>
            ```

        This function takes a row from a DataFrame, typically one message entry, and
        converts it into an HTML formatted string. The HTML structure includes a 'div' element
        with an id attribute based on the message's id, a class attribute based on the message's role,
        and a 'p' element encapsulating the message text.
        """
        # Format and return the HTML representation of the message
        html = f'''<div id="id{message_row['id']}" class="{message_row['roll']}"> <p>{message_row['message']}</p> </div>
        '''
        return html

    
    def get_covo_start_messages(self):
        chat = ''
        for _, message_row in self.convo_start.iterrows():
            chat += self.message_to_html(message_row)
        return chat
    

    def get_latest_messages(self, message_count: int = 8) -> str:
        """
        Retrieve and format the latest messages for display.

        Args:
            message_count (int): The maximum number of messages to retrieve.

        Returns:
            str: The latest messages formatted as HTML.

        This method retrieves the latest messages from the conversation history, limits the number of messages
        to the smaller of `message_count` or the total number of messages available, converts each message to HTML,
        and concatenates them into a single HTML string.
        """
        # Get the total number of messages in the conversation history
        chat_len = len(self.messages) + len(self.convo_start)

        # Check if there are no messages
        if self.messages.empty or chat_len == 0:
            print("No recent messages available")
            return ""

        # Limit the number of messages to retrieve
        num_messages = min(chat_len, message_count)

        # Get the latest messages
        latest_messages = self.messages.tail(num_messages)

        # Convert each message to HTML and concatenate
        chat = ''
        for _, message_row in latest_messages.iterrows():
            chat += self.message_to_html(message_row)

        return chat



    def get_chat_prompt(self) -> str:
        """
        Generate the complete chat prompt for interaction.

        Returns:
            str: The complete chat prompt as an HTML-formatted string.

        This method combines the system prompt generated by `get_system_prompt` and the latest messages
        formatted as HTML from `get_latest_messages` to create a complete chat prompt for interaction.
        """
        # Combine the system prompt and the latest messages to create the complete prompt
        complete_prompt = f"""
        USER:
        {self.pre_prompt}
        Here is the startt of the chat and the latest x messages.
        Solve the task given by the User in the newest message and reply only with a new message in the same html format.

        Chat History: 
        {self.get_covo_start_messages()} 
        {self.get_latest_messages()}  
        ASSISTANT:
        """

        return complete_prompt

     

    def prompt(self, message):
        """
        Simulate a conversation prompt with the Phi model.

        Args:
            message (str): The user's message to include in the conversation.

        Returns:
            str: The response generated by the Phi model.

        This method simulates a conversation by creating a new user message, generating a response
        from the Phi model, extracting the response message, and updating the conversation history.
        """
        # Create a new user message and increment the message ID
        message_id = len(self.messages) + len(self.convo_start)
        self.create_message(message_id, "User", message)

        # Generate a response from the Phi model using the current conversation context
        prompt = self.get_chat_prompt()
        generated_text = self.phi_api.generate_text(prompt, max_tokens = 21)

        # Extract the Phi model's response for the current message
        answer, response = self.get_message_from_response(generated_text, message_id + 1)

        # Create a new message in the conversation history for the Phi model's response
        self.create_message(message_id + 1, answer["roll"], answer["message"])

        return response


    def start_chat(self):
        """
        Start a conversation process, repeatedly prompting the user for input.


        This function initiates a conversation process, repeatedly prompting the user for input via the console.
        The input is then passed to the PhiChat's `prompt` method to simulate a conversation.
        """
        print("Welcome to the PhiChat conversation!")
        print("You can start the conversation by typing your message.")
        print("Type 'exit' to end the conversation.")
        
        while True:
            user_input = input("You: ")
            
            # Check if the user wants to exit the conversation
            if user_input.lower() == 'exit':
                print("Conversation ended. Goodbye!")
                break
            
            # Call the PhiChat's prompt method to simulate a conversation
            response = self.prompt(user_input)

            print("PhiChat:", response)


# Example usage:
phi_chat = PhiChat(PhiWrapper())
phi_chat.start_chat()

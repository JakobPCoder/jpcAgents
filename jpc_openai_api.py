

import os

import openai
import jpcLogger


class OpenApi:
    """
    A class that provides wrappers for various OpenAI API calls.
    """
    def __init__(self, api_key = None):
        """
        Initializes an instance of the OpenApi class.

        Args:
            api_key (str): Your OpenAI API key.
        """

        # Checking for OpenAI API Key
        if api_key:
            print(f"OpenAI API Key has been provided")
            self.api_key = api_key
        else:
            print(f"No OpenAI API Key has been provided, checking if already set...")
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                print(f"OpenAI API Key has been found {api_key}")
                self.api_key = api_key
            else:
                raise ValueError("No OpenAI API Key has been found, please provide one via the api_key parameter")
            
        self.openai_client = openai.OpenAI()
        self.openai_client.api_key = self.api_key
        self.logger = jpcLogger.Logger()


    def get_cost(self, prompt_tokens, output_tokens, prompt_token_cost = 0.0010, output_tokens_cost = 0.0020):
        factor = 1.0 / 1000
        return (prompt_tokens * factor * prompt_token_cost) + (output_tokens * factor * output_tokens_cost)



    def text_complete(self, prompt, system_prompt=None, model="gpt-3.5-turbo", response_format = "text"):
        """
        Generate text completion using the OpenAI GPT-3.5 Turbo model.

        Args:
            prompt (str): The user's input or prompt for text generation.
            system_prompt (str, optional): A system prompt to provide context and instructions.
                Defaults to a predefined system prompt.

            response_format (str): text or {"type": "json_object"}

        Returns:
            str: The generated text as a response to the user's input.

        Raises:
            ValueError: If 'prompt' is None or empty.
        """
        # Check if 'prompt' is provided and not empty
        if not prompt:
            raise ValueError("The parameter 'prompt' was None or empty. Please provide a valid prompt in the form of a string.")

        # Use a default system prompt if not provided
        if not system_prompt:
            system_prompt = """
As a highly advanced AI assistant, you excel in performing diverse tasks with precision and expertise.
Your responses are well-structured and maintain consistent formatting, ensuring clarity and professionalism.
Please assist with the following described tasks precisely without additional questions or delays.
Only answer with the requested output."""

        #(system_prompt)

        # Generate text completion using OpenAI GPT-3.5 Turbo model
        response = self.openai_client.chat.completions.create(
            model=model,
            response_format={"type": response_format},
            max_tokens = 256,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )

        # Get the generated message from the response
        message = response.choices[0].message.content

        cost_usd = self.get_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
        print(f"Cost in USD: {cost_usd}")


        # Log usage statistics and input/output
        self.logger.log([
            "text_complete",
            f"prompt_tokens: {response.usage.prompt_tokens}",
            f"completion_tokens: {response.usage.completion_tokens}",
            f"total_tokens: {response.usage.total_tokens}",
            f"Cost $: {cost_usd}",
            system_prompt,
            prompt,
            message
        ])

        return message
    
    def speech_to_text(self, audio_path):
        transcript = self.openai_client.audio.translations.create(
            model="whisper-1", 
            file=audio_path,
            response_format="text"
            )
        return transcript


    def text_to_speech(self, text, output_filename="speech.mp3", voice="alloy", speed=1.0, model="tts-1"):
        """
        Generate speech from text using the OpenAI GPT-3.5 Turbo model.

        Args:
            text (str): The text you want to convert to speech.
            voice (str, optional): The voice model to use (e.g., "alloy").
            output_path (str, optional): The folder path where the generated speech will be saved.

        Returns:
            None

        Raises:
            ValueError: If 'text' is None or empty.
        """
        # Check if 'text' is provided and not empty
        if not text:
            raise ValueError("The parameter 'text' was None or empty. Please provide a valid text input as a string.")

        # Generate speech using OpenAI GPT-3.5 Turbo model
        response = self.openai_client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed = 1.0,
            response_format="mp3"  
        )


        output_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "outputs")

        # Create the 'outputs' folder if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Specify the output file path within the 'outputs' folder
        output_file_path = os.path.join(output_path, output_filename)


        self.logger.log(["text_to_speech", text, voice, speed, output_file_path])

        # Stream the generated speech to the output file
        response.stream_to_file(output_file_path)

        # Log usage statistics and input/output if needed
        # You can add logging here similar to what you did in 'text_complete'

        print(f"Speech generated and saved to '{output_file_path}'.")





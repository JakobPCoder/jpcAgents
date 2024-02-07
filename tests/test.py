import openai
import together



MODEL_COSTS = {
    "mistralai/Mistral-7B-Instruct-v0.2":   0.0002,
    "mistralai/Mixtral-8x7B-Instruct-v0.1": 0.0006,
}



class TogetherApi:
    def __init__(self, api_key = None):

        self.client: openai.OpenAI = openai.OpenAI(
        api_key="9e14c2e12b0399ccd2d2a7dd58a13074f7b4765265c74da40e2a429db49aae98",
        base_url="https://api.together.xyz/v1")
        self.default_system_prompt = """As a highly advanced AI assistant, you excel in performing diverse tasks with precision and expertise.
Your responses are well-structured and maintain consistent formatting, ensuring clarity and professionalism.
Please assist with the described tasks or question precisely and concise, without additional questions or delays.
Only answer with the requested output.
"""



    def get_cost(self, response):
        model_used = response.model
        prompt_token_cost = MODEL_COSTS[model_used]
        output_tokens_cost = MODEL_COSTS[model_used]

        factor = 1.0 / 1000
        usd_dec = 6
        cent_dec = 4
        cost_usd = ((response.usage.prompt_tokens * factor * prompt_token_cost) + (response.usage.completion_tokens * factor * output_tokens_cost))
        print(f"Cost of this prompt with {response.usage.total_tokens} tokens was ${cost_usd:.{usd_dec}f}, or {cost_usd * 100:.{cent_dec}f}¢.")
        return cost_usd

    def respond_to_chat(self, messages, system_prompt = None, model="mistralai/Mistral-7B-Instruct-v0.2"):

        system_prompt = system_prompt or self.default_system_prompt

        messages = [{"role": "system", "content": system_prompt}] + messages

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )

        cost = self.get_cost(response)
        text_response = response.choices[0].message.content
        return text_response
    

    def single_prompt(self, message, system_prompt = None, model="mistralai/Mistral-7B-Instruct-v0.2"):

        system_prompt = system_prompt or self.default_system_prompt

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        cost = self.get_cost(response)

        text_response = response.choices[0].message.content
        return text_response
    
    
# togetherApi = TogetherApi("9e14c2e12b0399ccd2d2a7dd58a13074f7b4765265c74da40e2a429db49aae98")


# user_content = "Tell me about the company VW please."
# messages = [{"role": "user", "content": user_content}]

# response = togetherApi.respond_to_chat(messages)

# print("Together response:\n", response)
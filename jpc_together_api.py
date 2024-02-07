
import os
import base64
from typing import Optional
import math

import openai
import together

MODELS_TEXT = {
    "MIST_7B_INSTRUCT": "mistralai/Mistral-7B-Instruct-v0.2",
    "MIST_8X7B_INSTRUCT": "mistralai/Mixtral-8x7B-Instruct-v0.1",  
    "SNROKEL_7B_DPO": "snorkelai/Snorkel-Mistral-PairRM-DPO",  

}


MODELS_TEXT_COSTS = {
    "mistralai/Mistral-7B-Instruct-v0.2":   0.0002,
    "mistralai/Mixtral-8x7B-Instruct-v0.1": 0.0006,
    "snorkelai/Snorkel-Mistral-PairRM-DPO": 0.0002,
}


MODELS_IMAGE = {
    "STABLE_DIFFUSION_1_5": "runwayml/stable-diffusion-v1-5",               
    "STABLE_DIFFUSION_2_1": "stabilityai/stable-diffusion-2-1",             
    "STABLE_DIFFUSION_XL_1": "stabilityai/stable-diffusion-xl-base-1.0",    
    "REALISTIC_VISION_3": "SG161222/Realistic_Vision_V3.0_VAE",             
    "OPEN_JOURNEY_4": "prompthero/openjourney",                             
    "ANALOG_DIFFUSION": "wavymulder/Analog-Diffusion",                             
}

MODELS_IMAGE_DESCRIPTION = {
    "STABLE_DIFFUSION_1_5": "Latent text-to-image diffusion model capable of generating photo-realistic images given any text input." ,
    "STABLE_DIFFUSION_2_1": " Latent text-to-image diffusion model capable of generating photo-realistic images given any text input.",
    "STABLE_DIFFUSION_XL_1": "A text-to-image generative AI model that excels at creating 1024x1024 images.",
    "REALISTIC_VISION_3": "Fine-tune version of Stable Diffusion focused on photorealism.",
    "OPEN_JOURNEY_4": "An open source Stable Diffusion model fine tuned model on Midjourney images.",
    "ANALOG_DIFFUSION": "Dreambooth model trained on a diverse set of analog photographs to provide an analog film effect.",
    
}


class TogetherApi:
    def __init__(self, api_key = None):

        self.client: openai.OpenAI = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.together.xyz/v1")
        together.api_key = api_key

        self.default_system_prompt = """As a highly advanced AI assistant, you excel in performing diverse tasks with precision and expertise.
Your responses are well-structured and maintain consistent formatting, ensuring clarity and professionalism.
Please assist with the described tasks or question precisely and be polite and concise.
Only answer with the requested output.
"""

    def get_cost(self, response):
        model_used = response.model
        prompt_token_cost = MODELS_TEXT_COSTS[model_used]
        output_tokens_cost = MODELS_TEXT_COSTS[model_used]
        factor = 1.0 / 1000
        usd_dec = 6
        cent_dec = 4
        cost_usd = ((response.usage.prompt_tokens * factor * prompt_token_cost) + (response.usage.completion_tokens * factor * output_tokens_cost))
        print(f"Cost of this prompt with {response.usage.prompt_tokens} prompt tokens and {response.usage.completion_tokens} response tokens was ${cost_usd:.{usd_dec}f}, or {cost_usd * 100:.{cent_dec}f}¢.")
        return cost_usd

    def get_cost_images(self, x_res, y_res, steps, results=1):
        base_cost = 0.001
        scaling_factor = 10 ** (math.log10(x_res * y_res) / 4)  # Adjusted the scaling factor
        price = base_cost * scaling_factor * steps * results
        return round(price, 3)

    def respond_to_chat(self, messages, system_prompt = None, model=MODELS_TEXT["MIST_7B_INSTRUCT"], temperature=0.7, max_tokens=1024):

        system_prompt = system_prompt or self.default_system_prompt

        messages = [{"role": "system", "content": system_prompt}] + messages

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=['<\SYS>', '<s>']
        )

        cost = self.get_cost(response)
        text_response = response.choices[0].message.content
        return text_response
    


    def single_prompt(self, message, system_prompt = None, model=MODELS_TEXT["MIST_7B_INSTRUCT"], temperature=0.7, max_tokens=1024, stop=['</s>']):
        # system_prompt = system_prompt or self.default_system_prompt

        if system_prompt:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        else:
            messages = [
                {"role": "user", "content": message}
            ]

        response = self.client.chat.completions.create(
            model=model,
            messages = messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop = stop
        )

        
        cost = self.get_cost(response)
        text_response = response.choices[0].message.content
        return text_response, cost
    

    def generate_image_and_save(self,
        prompt: str,
        model: Optional[str] = "",
        steps: Optional[int] = 20,
        seed: Optional[int] = 42,
        results: Optional[int] = 1,
        height: Optional[int] = 256,
        width: Optional[int] = 256,
        negative_prompt: Optional[str] = "",
        filename: Optional[str] = "generated_image.png"):

        # Generate image 
        response = together.Image.create(
            prompt=prompt,
            model = model,
            steps = steps,
            seed = seed,
            results = results,
            height = height,
            width = width,
            negative_prompt = negative_prompt
            )

        # Extract the first generated image from the response
        image = response["output"]["choices"][0]

        # Decode the base64 image representation
        decoded_image = base64.b64decode(image["image_base64"])
        # Determine the output directory
        script_path = os.path.dirname(os.path.realpath(__file__))
        output_directory = os.path.join(script_path, "workspace", "chat", "images", "created")
        os.makedirs(output_directory, exist_ok=True)  # Create the output directory if it doesn't exist

        # Combine the output directory and specified filename
        output_path = os.path.join(output_directory, filename)

        # Save the image to the specified path
        with open(output_path, "wb") as f:
            f.write(decoded_image)

        return output_path
    


# TOKEN_TOGETHER = "9e14c2e12b0399ccd2d2a7dd58a13074f7b4765265c74da40e2a429db49aae98"

# api = TogetherApi(TOKEN_TOGETHER)

# #print(api.get_cost_images(1024, 1024, 75))

# print(api.generate_image_and_save(
#     prompt = """photgraph of a spaceship leaving planets athmosshpere in cinematic style, hd, unreal engine, pbr, raytraced""",
#     model = "stabilityai/stable-diffusion-xl-base-1.0",
#     height = 512,
#     width = 1024,
#     steps = 50,
#     seed = 42,
#     results = 1,
#     negative_prompt = ""
#     ))

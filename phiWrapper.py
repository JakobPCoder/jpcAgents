import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MAX_SEQUENCE_LENGTH = 2048 


# models
MODEL_PHI15 = "microsoft/phi-1_5"
MODEL_PHI15_WIZVIC = "jphme/phi-1_5_wizzard_vicuna_uncensored"
#MODEL_PHI15_PUFFIN_V2 = "teknium/Puffin-Phi-v2"
MODEL_PHI15_HERMES = "teknium/Phi-Hermes-1.3B"
MODEL_PHI15_NO_LLM = "totally-not-an-llm/EveryPHIngLM-1.3b-V3"


import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class PhiWrapper:
    """
    Wrapper class for Phi language model interactions.

    Attributes:
        model_name (str): The name or path of the pre-trained Phi model.
        device (str): The device (e.g., 'cuda' or 'cpu') to run the model on.
        model (AutoModelForCausalLM): The loaded Phi language model.
        tokenizer (AutoTokenizer): The tokenizer for the Phi model.

    The PhiWrapper class facilitates interactions with the Phi language model, including text generation.
    """

    def __init__(self, model_name=MODEL_PHI15):
        """
        Initialize the PhiWrapper.

        Args:
            model_name (str): The name or path of the pre-trained Phi model.

        This constructor initializes the PhiWrapper with the specified model and tokenizer.
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None

        # Determine the path for the cache directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        custom_cache_dir = os.path.join(script_dir, "models")

        torch.set_default_device(self.device)

        # Initialize the tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=custom_cache_dir, trust_remote_code=True, torch_dtype=torch.float16)
        print("Tokenizer loaded", self.tokenizer.eos_token, self.tokenizer.eos_token_id, self.tokenizer.pad_token, self.tokenizer.pad_token_id)

        # Initialize the model
        self.model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True, torch_dtype=torch.float16)
        print("Model loaded")


    def generate_text(self, prompt, max_tokens=128):
        """
        Generate text using the Phi model based on a given prompt.

        Args:
            prompt (str): The input prompt for text generati[{ 7on.
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            str: The generated text.

        This method generates text based on the provided prompt using the Phi model.
        """
        if not self.model:
             self.load_model(self.model_name)

        inputs = self.tokenizer(prompt, return_tensors="pt", return_attention_mask=False)
        
        #with torch.autocast(self.model.device.type, dtype=torch.float16, enabled=True):
        outputs = self.model.generate(
            **inputs, 
            max_new_tokens=max_tokens, 
            eos_token_id=self.tokenizer.eos_token_id,

            do_sample=True, 
            temperature=0.2, 
            top_p=0.9, 
            use_cache=True, 
            repetition_penalty=1.2, 
            )
        text = self.tokenizer.batch_decode(outputs, skip_special_tokens = True)[0]
        return text


    def unload_model(self):
        """
        Unload the Phi model and tokenizer.

        This method unloads the Phi model and tokenizer from memory.
        """
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None
            print("Tokenizer unloaded")
    
        if self.model:
            del self.model
            self.model = None
            print("Model unloaded")

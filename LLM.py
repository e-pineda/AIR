from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM
import torch

model_name = "mistralai/Mistral-7B-v0.1"

model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto')

tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side="left")
tokenizer.pad_token = tokenizer.eos_token  # Most LLMs don't have a pad token by default

model_inputs = tokenizer(["A list of colors: red, blue", "Portugal is"], return_tensors="pt", padding=True).to('cuda')

generated_ids = model.generate(**model_inputs)
results = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
print(results)


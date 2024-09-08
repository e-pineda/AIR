from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM
from trl import SFTConfig, SFTTrainer
from datasets import Dataset
from peft import LoraConfig

class LLM:
    def __init__(self, artist, song_section):
        self.model_name = "mistralai/Mistral-7B-v0.1"
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, device_map='auto', load_in_4bit=True)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, padding_side="left")
        self.tokenizer.pad_token = self.tokenizer.eos_token  # Most LLMs don't have a pad token by default

        self.song_section = song_section
        self.artist = artist

        self.sft_config = SFTConfig(
            max_seq_length=100,
            output_dir="/tmp",
        )

        self.peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="QUESTION_ANS",
        )


    def finetune(self, data):
        dataset = Dataset.from_pandas(data)

        def formatting_prompts_func(example):
            output_texts = []
            for i in range(len(example['question'])):
                text = f"### Question: {example['question'][i]}\n ### Answer: {example['answer'][i]}"
                output_texts.append(text)
            return output_texts

        trainer = SFTTrainer(
            self.model,
            args=self.sft_config,
            train_dataset=dataset,
            formatting_func=formatting_prompts_func,
            peft_config=self.peft_config
        )

        trainer.train()

    def write_lyrics(self):
        model_inputs = self.tokenizer([f"### Question: Write a {self.song_section} like {self.artist}"], return_tensors="pt", padding=True)

        generated_ids = self.model.generate(**model_inputs)
        results = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        
        return results


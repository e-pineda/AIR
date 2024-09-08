import user_interface
from LLM import *

# get categories
text, section, artists = user_interface.interface()

print(text)

LLM_model = LLM(section, artists[0])
LLM_model.finetune(text)

lyrics = LLM_model.write_lyrics()
print(lyrics)

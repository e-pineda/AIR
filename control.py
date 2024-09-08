import user_interface
from LLM import *

# get categories
text, section, artists = user_interface.interface()

print(text)
print(artists)

LLM_model = LLM(artists[0], section)
LLM_model.finetune(text)

lyrics = LLM_model.write_lyrics()
print(lyrics)

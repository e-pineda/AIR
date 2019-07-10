# Artifical Intelligence Rap -- A.I.R.

This program utilizes a Long short-term memory neural net to generate rap lyrics. The AI is trained with scraped lyrics from a list of artists I created. 
The AI can generate lyrics according to a set of artists, a bpm range or both.


## Installation
Please make sure the following libraries are installed before running the program:
```
numpy
pandas
scrapy
tensorflow-gpu
keras
```

Note 1: Scrapy is only required for installation if you wish to scrape additional song data.

Note 2: I recommend training on a gpu as training time will decrease significantly. 


## Usage

To scrape additional song info, run control_spiders.py.

To run the AI, run lyric_generator.py

##Meta
Elijah Pineda - epineda@conncoll.edu
https://github.com/e-pineda

## License
[MIT](https://choosealicense.com/licenses/mit/)
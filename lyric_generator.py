from __future__ import print_function
import helper
import numpy as np
import sys
import user_interface


SEQUENCE_LENGTH = 40
SEQUENCE_STEP = 3
EPOCHS = 20
DIVERSITY = 1.0
BATCH_SIZE = 256

# get categories
text = user_interface.interface()


# Get unique characters from the corpus
chars = helper.extract_characters(text)

"""
    Create sequences that will be used as the input to the network.
    Create next_chars array that will serve as the labels during the training.
"""
sequences, next_chars = helper.create_sequences(text, SEQUENCE_LENGTH, SEQUENCE_STEP)
char_to_index, indices_char = helper.get_chars_index_dicts(chars)

"""
    The network is not able to work with characters and strings, we need to vectorise.
"""
X, y = helper.vectorize(sequences, SEQUENCE_LENGTH, chars, char_to_index, next_chars)

"""
    Define the structure of the model.
"""
model = helper.build_model(SEQUENCE_LENGTH, chars)

"""
    Train the model
"""

model.fit(X, y, batch_size=BATCH_SIZE, nb_epoch=EPOCHS)

"""
    Pick a random sequence and make the network continue
"""


for diversity in [0.1, 0.25, .5, .75, .9, 1, 1.2, 1.5, 2]:
    print()
    print('----- diversity:', diversity)

    generated = ''
    # insert your 40-chars long string. OBS it needs to be exactly 40 chars!
    sentence = "rolling in the deep got me some type of "
    sentence = sentence.lower()
    generated += sentence

    print('----- Generating with seed: "' + sentence + '"')
    sys.stdout.write(generated)

    for i in range(400):
        x = np.zeros((1, SEQUENCE_LENGTH, len(chars)))
        for t, char in enumerate(sentence):
            x[0, t, char_to_index[char]] = 1.

        predictions = model.predict(x, verbose=0)[0]
        next_index = helper.sample(predictions, diversity)
        next_char = indices_char[next_index]

        generated += next_char
        sentence = sentence[1:] + next_char

        sys.stdout.write(next_char)
        sys.stdout.flush()
    print()

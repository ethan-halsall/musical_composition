import os
import random

import numpy as np
from music21 import environment

import midi_helper as helper
from l_system import lsystem, parse_lengths
from markov import Markov

"""# us['midiPath'] = '/path/to/midi/program'

seed = random.randint(0, 2 ** 32 - 1)

print(f"Generating using seed: {seed}")

# Set numpy seed for random
np.random.seed(seed)

# Get a list of all files in the midi dir with the .mid extension
files = [f for f in os.listdir('./midi') if f.endswith(".mid")]
for count, f in enumerate(files):
    print(f"{count + 1}: {f}")

filename = files[int(input("Select file: ")) - 1]

# Extract the notes from midi file using midi helper
midi_extraction = helper.Extract(f"midi/{filename}")
midi_extraction.parse_midi()
chords = midi_extraction.get_chords()
values, size = midi_extraction.get_frequency()
print(values)
print(size)

# Generate markov chain
markov_chain = Markov(3)
markov = markov_chain.transition_matrix(chords)

# Generate a sequence of notes using the markov chain
notes = markov_chain.generate_sequence(markov)

# rules = {"a": "b[a]b(a)a", "b": "bb"}
rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}

rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cdb"}

tree = lsystem("abacd", rules, 7)

durations = parse_lengths(tree)

helper.write_to_midi(f"{filename[:-4]}_{seed}.mid", notes, durations)

# Play midi file using timidity binary
# os.system(f"timidity -Os out/{filename[:-4]}_{seed}.mid")"""
test = helper.Extract("../out/ty_januar_64849935.mid")
test.parse_midi()
print(test.get_chords())
values, size = test.get_frequency()
print(values)
print(size)

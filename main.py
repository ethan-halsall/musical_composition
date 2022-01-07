import os
import random

import numpy as np
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.stream import Part

import midi_helper as helper
from markov import Markov
from l_system import lsystem, parse_lengths

seed = random.randint(0, 2 ** 32 - 1)

print(f"Generating using seed: {seed}")

# Set numpy seed for random
np.random.seed(seed)

# Extract the notes from midi file using midi helper
midi_extraction = helper.Extract("midi/brahms_opus1_1.mid")
midi_extraction.parse_midi()
chords = midi_extraction.get_chords()
duration = midi_extraction.get_durations()

# Generate markov chain
markov_chain = Markov(3)
markov = markov_chain.transition_matrix(chords)

# Generate a sequence of notes using the markov chain
notes = markov_chain.generate_sequence(markov)

# rules = {"a": "b[a]b(a)a", "b": "bb"}
rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}

rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cdb"}

tree = lsystem("abacd", rules, 6)

durations = parse_lengths(tree)

part = Part()
for i in range(len(notes)):
    note = notes[i]
    duration = durations[i]

    if note == "rest":
        part.append(Rest(quarterLength=duration))
    else:
        part.append(Chord(note, quarterLength=duration))

mf = streamToMidiFile(part)

mf.open('chords.mid', 'wb')
mf.write()
mf.close()

# Play midi file using timidity binary
os.system("timidity -Os chords.mid")

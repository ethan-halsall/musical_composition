import os
import random

import numpy as np
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.stream import Part

import midi_helper as helper
from markov import Markov

seed = random.randint(0, 2 ** 32 - 1)

print(f"Generating using seed: {seed}")

# Set numpy seed for random
np.random.seed(seed)

# Extract the notes from midi file using midi helper
midi_extraction = helper.Extract("midi/CLASSICAL_beemoonlightson.mid")
midi_extraction.parse_midi()
chords = midi_extraction.get_chords()
duration = midi_extraction.get_durations()

# Generate markov chain of order 3
markov_chain = Markov(3)
markov = markov_chain.transition_matrix(chords)

# Generate a sequence of notes using the markov chain
notes = markov_chain.generate_sequence(markov)

# rules = {"a": "b[a]b(a)a", "b": "bb"}
rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}

rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cdb"}


def lsystem(axiom, rules, n):
    out = axiom
    for _ in range(n):
        pos = 0
        for char in out:
            if char in rules:
                out = out[:pos] + rules[char] + out[pos + 1:]
                pos += len(rules[char])
            else:
                pos += 1

    return out


def parse_lengths(tree, minimum=0.5):
    curr = tree[0]
    length = minimum
    durations = []
    direction = ""
    m = 1
    for i in range(1, len(tree)):
        char = tree[i]
        curr = tree[i - 1]
        if char == "[" or curr == "(":
            m = 2
        elif char == "]" or curr == ")":
            m = 3
        if curr == char:
            length += (minimum * m)
        else:
            if length > 0:
                durations.append(length)
            length = minimum

    return durations


tree = lsystem("abacd", rules, 6)

durations = parse_lengths(tree, minimum=0.33)

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

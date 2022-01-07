import os
import random

import numpy as np
import pandas as pd
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.stream import Part

import midi_helper as helper

seed = random.randint(0, 2 ** 32 - 1)

print(f"Generating using seed: {seed}")

np.random.seed(seed)

# Extract the notes from midi file using midi helper
midi_extraction = helper.Extract("midi/CLASSICAL_beemoonlightson.mid")
midi_extraction.parse_midi()
chords = midi_extraction.get_chords()
duration = midi_extraction.get_durations()


class Markov:
    def __init__(self, order):
        self.order = order

    def transition_matrix(self, transitions):
        values, size = np.unique(transitions, return_counts=True)
        n = len(values)

        dict = {}

        for x in range(len(transitions)):
            if len(transitions[x:x + self.order + 1]) == self.order + 1:
                key = ",".join(transitions[x:x + self.order + 1])
                if key not in dict:
                    dict[key] = 1

                else:
                    dict[key] += 1

        M = np.zeros((len(dict), n), int)

        states = []

        for i, (key, value) in enumerate(dict.items()):
            splits = key.split(",")
            column = splits[self.order]
            j = np.where(values == column)[0][0]
            M[i][j] = value
            states.append(",".join(splits[:self.order]))

        df = pd.DataFrame(M)  # convert to dataframe

        # Set axis labels
        df = df.set_axis(states)
        df = df.set_axis(values, axis=1)

        # Combine rows with same keys
        df = df.groupby(df.index).sum()

        # calculate the total frequency each of the columns
        df['sum'] = df.sum(axis=1)

        # Calculate the probability of the transition occurring
        df = df.div(df['sum'], axis=0)

        # Drop the sum column
        df = df.drop('sum', 1)
        return df

    def generate_sequence(self, df, length=400):
        cur = df.sample()
        notes = cur.index.values[0].split(",")
        columns = list(df.columns.values)
        for i in range(length - 1):
            probs = cur.values.flatten().tolist()
            note_index = np.random.choice(cur.size, p=probs)
            note = columns[note_index]
            cur = df.loc[[",".join(notes[i + 1:i + self.order]) + f",{note}"]]
            notes.append(note)
        return notes


markov_chain = Markov(3)

markov = markov_chain.transition_matrix(chords)

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
# part.append(signature)
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

os.system("timidity -Os chords.mid")

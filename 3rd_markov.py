import os
import random

import numpy as np
import pandas as pd
from music21 import *
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.stream import Part

seed = random.randint(0, 2 ** 32 - 1)

print(f"Generating using seed: {seed}")

np.random.seed(seed)


def parse_midi(filename):
    music = converter.parse(filename)
    # chopin.plot('histogram', 'pitch'

    chords = []
    duration = []

    for part in instrument.partitionByInstrument(music).parts:
        # signature = part[meter.TimeSignature][0]
        # select elements of only piano
        if 'Piano' in str(part):
            notes_to_parse = part.recurse()
            # finding whether a particular element is note or a chord
            for element in notes_to_parse:
                # notes
                if isinstance(element, note.Note):
                    chords.append(str(element.pitch))
                    duration.append(element.quarterLength)
                # chords
                elif isinstance(element, chord.Chord):
                    chords.append(' '.join(str(n.pitch) for n in element))
                    duration.append(element.quarterLength)
                # rests
                elif isinstance(element, note.Rest):
                    chords.append(element.name)
                    duration.append(element.quarterLength)

    return chords, duration


def transition_matrix(transitions):
    values, size = np.unique(transitions, return_counts=True)
    n = len(values)

    dict = {}

    for (w, x, y, z) in zip(transitions, transitions[1:], transitions[2:], transitions[3:]):
        if f"{w},{x},{y},{z}" not in dict:
            dict[f"{w},{x},{y},{z}"] = 1

        else:
            dict[f"{w},{x},{y},{z}"] += 1

    print(dict)

    M = np.zeros((len(dict), n), int)

    states = []

    for i, (key, value) in enumerate(dict.items()):
        splits = key.split(",")
        column = splits[3]
        j = np.where(values == column)[0][0]
        M[i][j] = value
        # print(value)
        states.append(",".join(splits[:3]))


    df = pd.DataFrame(M)  # convert to dataframe

    # Set axis labels
    df = df.set_axis(states)
    df = df.set_axis(values, axis=1)

    # Combine rows with same keys
    df = df.groupby(df.index).sum()
    # calculate the total frequency of the each column
    df['sum'] = df.sum(axis=1)

    # Calculate the probability of the transition occurring
    df = df.div(df['sum'], axis=0)

    # Drop the sum column
    df = df.drop('sum', 1)
    return df


def generate(df, length=400):
    cur = df.sample()
    notes = cur.index.values[0].split(",")
    columns = list(df.columns.values)
    for i in range(length - 1):
        probs = cur.values.flatten().tolist()
        note_index = np.random.choice(cur.size, p=probs)
        note = columns[note_index]
        cur = df.loc[[f"{notes[i + 1]},{notes[i + 2]},{note}"]]
        notes.append(note)
    return notes


chords, duration = parse_midi('midi/CLASSICAL_beemoonlightson.mid')

markov = transition_matrix(chords)

notes = generate(markov)

# rules = {"a": "b[a]b(a)a", "b": "bb"}
rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}


rules = {"a" : "b[a[ba]]", "b" : "b((b)a)c" , "c" : "cd"}


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


def parse_lengths(tree, minium=0.5):
    curr = tree[0]
    length = minium
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
            length += (minium * m)
        else:
            if length > 0:
                durations.append(length)
            length = minium

    return durations


tree = lsystem("abacd", rules, 8)

durations = parse_lengths(tree)

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

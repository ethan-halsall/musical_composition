import random

import numpy as np
import pandas as pd
from music21 import *
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.stream import Part
import os
import itertools

seed = random.randint(0, 2 ** 32 - 1)

print(f"Generating using seed: {seed}")

np.random.seed(seed)


def parse_midi(filename):
    music = converter.parse(filename)
    # chopin.plot('histogram', 'pitch'

    chords = []
    duration = []

    print(music)

    for part in instrument.partitionByInstrument(music).parts:
        #signature = part[meter.TimeSignature][0]
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

    states = np.array(list(itertools.product(values, repeat=2)))

    #print(states)

    M = np.zeros((len(states), n), int)

    for (x, y, z) in zip(transitions, transitions[1:], transitions[2:]):
        i = np.where(states == (x, y))[0][0]
        j = np.where(values == z)[0][0]
        M[i][j] += 1

    T = np.nan_to_num((M.T / M.sum(axis=1)).T)
    #print(T)

    # T = np.linalg.matrix_power(T, order)

    df = pd.DataFrame(T)  # convert to dataframe

    # Set axis labels
    df = df.set_axis(states)
    df = df.set_axis(values, axis=1)
    df = df.loc[~(df == 0).all(axis=1)]

    return df


chords, duration = parse_midi('midi/classical_bachminuet_in_g.mid')

print(chords)

markov = transition_matrix(chords)



def generate(df, length=400):
    cur = df.sample()
    notes = [cur.index.values[0][0], cur.index.values[0][1]]
    print(cur.index.values[0])
    columns = list(df.columns.values)
    for i in range(length - 1):
        probs = cur.values.flatten().tolist()
        #print(probs)
        try:
            note_index = np.random.choice(cur.size, p=probs)
            note = columns[note_index]
            cur = df[(notes[i + 1], note)]
            notes.append(note)
            print(notes)
        except KeyError:
            cur = df.sample()
            notes.append(cur.index.values[0][0])
            notes.append(cur.index.values[0][1])
    return notes


notes = generate(markov)
print(notes)
#markov_duration = transition_matrix(duration)
#durations = generate(markov_duration)

#rules = {"a": "b[a]b(a)a", "b": "bb"}
rules = {"a": "d[dbe](dce)e", "b" : "d[daf](dcf)f", "c" : "d[dbg](dag)g"}
#rules = {"a" : "b[a[ba]]", "b" : "b((b)a)c" , "c" : "cd"}


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

def parse_lengths(tree, minium = 0.5):
    curr = tree[0]
    length = minium
    durations = []
    direction = ""
    m = 1
    for i in range(1, len(tree)):
        char = tree[i]
        curr = tree[i-1]
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

print('Converting to MIDI')
part = Part()
#part.append(signature)
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

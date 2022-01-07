import random

import numpy as np
import pandas as pd
from music21 import *
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.stream import Part
import os

seed = random.randint(0, 2 ** 32 - 1)

print(f"Generating using seed: {seed}")

np.random.seed(seed)


def parse_midi(filename):
    music = converter.parse(filename)
    # chopin.plot('histogram', 'pitch'

    chords = []
    duration = []

    for part in instrument.partitionByInstrument(music).parts:
        signature = part[meter.TimeSignature][0]
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

    return chords, duration, signature


def transition_matrix(transitions):
    values, size = np.unique(transitions, return_counts=True)
    n = len(values)

    M = np.zeros((n, n), int)

    for (x, y) in zip(transitions, transitions[1:]):
        i = np.where(values == x)[0][0]
        j = np.where(values == y)[0][0]
        M[i][j] += 1

    T = (M.T / M.sum(axis=1)).T

    # T = np.linalg.matrix_power(T, order)

    df = pd.DataFrame(T)  # convert to dataframe

    # Set axis labels
    df = df.set_axis(values)
    df = df.set_axis(values, axis=1)

    return df


def generate(df, length=400):
    cur = df.sample()
    notes = [cur.index.values[0]]
    columns = list(df.T.columns.values)
    for _ in range(length - 1):
        probs = cur.values.flatten().tolist()
        note_index = np.random.choice(cur.size, p=probs)
        note = columns[note_index]
        notes.append(note)
        cur = df.loc[[note]]
    return notes


chords, duration, signature = parse_midi('../midi/brahms-waltz-15.mid')

markov = transition_matrix(chords)
markov_duration = transition_matrix(duration)

notes = generate(markov)
durations = duration

print('Converting to MIDI')
part = Part()
part.append(signature)
for i in range(len(notes)):
    note = notes[i]
    duration = durations[i]

    if note == "rest":
        part.append(Rest(quarterLength=duration))
    else:
        part.append(Chord(note, quarterLength=duration))

mf = streamToMidiFile(part)

mf.open('../chords.mid', 'wb')
mf.write()
mf.close()

os.system("timidity -Os chords.mid")

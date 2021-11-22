import random

from music21 import *
import numpy as np
import pandas as pd
from music21.chord import Chord
from music21.note import Note
from music21.note import Rest

chopin = converter.parse('mz_570_1.mid')
# chopin.plot('histogram', 'pitch')

#key = chopin.analyze('key')
#print(key.tonic.name, key.mode)

s2 = instrument.partitionByInstrument(chopin)

notes = []
chords = []
notes_to_parse = None
duration = []

# Looping over all the instruments
for part in s2.parts:
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

def transition_matrix(transitions):
    values, size = np.unique(transitions, return_counts=True)
    n = len(values)

    M = np.zeros((n, n), int)

    print(values)

    for (x, y) in zip(transitions, transitions[1:]):
        i = np.where(values == x)[0][0]
        j = np.where(values == y)[0][0]

        M[i][j] += 1

    df = pd.DataFrame(M)  # convert to dataframe

    # calculate the total frequency of the each column
    df['sum'] = df.sum(axis=1)

    # Calculate the probability of the transition occurring
    df = df.div(df['sum'], axis=0)

    # Drop the sum column
    df = df.drop('sum', 1)

    # Set axis labels
    df = df.set_axis(values)
    df = df.set_axis(values, axis=1)
    
    return df

markov = transition_matrix(chords)
markov_duration = transition_matrix(duration)

def generate(df, length=200):
    cur = df.sample()
    notes = [cur.index.values[0]]
    columns = list(df.columns.values)
    for _ in range(length - 1):
        probs = cur.values.flatten().tolist()
        note_index = np.random.choice(cur.size, p=probs)
        note = columns[note_index]
        notes.append(note)
        cur = df.loc[[note]]
    return notes

notes = generate(markov)
durations = generate(markov_duration)

from music21.stream import Part
from music21.midi.translate import streamToMidiFile

print('Converting to MIDI')
part = Part()
for i in range(len(notes)):
    note = notes[i]
    duration = durations[i]

  #  print(note)
    if note == "rest":
         part.append(Rest(quarterLength=duration))
    else: 
        part.append(Chord(note, quarterLength=duration))

mf = streamToMidiFile(part)

mf.open('chords.mid', 'wb')
mf.write()
mf.close()
import random

from music21 import *
import numpy as np
import pandas as pd
from music21.chord import Chord
from music21.note import Note

chopin = converter.parse('chpn_op7_2.mid')
# chopin.plot('histogram', 'pitch')

#key = chopin.analyze('key')
#print(key.tonic.name, key.mode)

s2 = instrument.partitionByInstrument(chopin)

notes = []
notes_to_parse = None
duration = []

# Looping over all the instruments
for part in s2.parts:
    # select elements of only piano
    if 'Piano' in str(part):
        notes_to_parse = part.recurse()
        # finding whether a particular element is note or a chord
        for element in notes_to_parse:
            # note
            if isinstance(element, note.Note):
                notes.append(element.pitch.midi)
                duration.append(element.quarterLength)
            # chord
            elif isinstance(element, chord.Chord):
                # notes.append('.'.join(str(n) for n in element.normalOrder))
                pass

notes_arr = np.array(notes)
duration_arr = np.array(duration)

#duration_df = pd.DataFrame(duration)
#duration_df = duration_df.groupby(0)[1].apply(np.array)

def generate_markov(arr, is_float = False, org=None):
    unique = np.unique(arr)
    if is_float:
        size = np.max(np.round(unique)).astype(int) + 1
    else:
        size = np.max(unique) + 1

    arr_zeros = np.zeros((size, size), int)
    for i in range(len(arr) - 1):
       # print(arr[i])
        arr_zeros[arr[i + 1]][arr[i]] += 1

    df = pd.DataFrame(arr_zeros)  # convert to dataframe

    # remove all zero rows and columns
    df = df.loc[~(df == 0).all(axis=1)]
    df = df.loc[:, (df != 0).any(axis=0)]

    # calculate the total frequency of the each column
    df['sum'] = df.sum(axis=1)

    # Calculate the probability of the transition occurring
    df = df.div(df['sum'], axis=0)

    # Drop the sum column
    df = df.drop('sum', 1)
    return df

def get_duration(note):
    vals = duration_df.loc[[note]].values[0]
    amount = len(vals)
    unique, counts = np.unique(vals, return_counts=True)
    probs = counts / amount
    duration_index = np.random.choice(unique.size, p=probs)
    return unique[duration_index]


def generate(df, length=100):
    cur = df.sample()
    notes = [cur.index.values]
    columns = list(df.columns.values)
    for _ in range(length - 1):
        probs = cur.values.flatten().tolist()
        note_index = np.random.choice(cur.size, p=probs)
        note = columns[note_index]
        notes.append(note)
        cur = df.loc[[note]]
    return notes

markov_notes = generate_markov(notes_arr)
notes = generate(markov_notes)

scaled_arr = np.round(duration_arr.astype(float) * 100).astype(int)
markov_duration = generate_markov(scaled_arr)

markov_duration = markov_duration.set_axis(np.unique(duration_arr))
markov_duration = markov_duration.set_axis(np.unique(duration_arr), axis=1)
durations = generate(markov_duration)

from music21.stream import Part
from music21.midi.translate import streamToMidiFile

print('Converting to MIDI')
part = Part()
for i in range(len(notes)):
    note = notes[i]
    duration = durations[i]

    # Repeat each note 4 times.
    for i in range(random.randint(1, 2)):
        part.append(Note(note, quarterLength=float(duration)))

mf = streamToMidiFile(part)

mf.open('chords.mid', 'wb')
mf.write()
mf.close()

# to run midi file use timidity -Os chords.mid from command line
# edit instruments inside of /etc/timidity/timidity.cfg
# soundfont /usr/share/soundfonts/freepats-general-midi.sf2
# todo: rename twice used vars
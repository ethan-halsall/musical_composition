import os

import numpy as np

import midi_helper as helper
from markov import Markov
from scipy.stats import chisquare, chi2_contingency


# Extract the notes from midi file using midi helper
midi_extraction = helper.ExtractMidi("midi/bor_ps3.mid")
midi_extraction.parse_midi()
expected_notes = midi_extraction.get_notes()

length = len(expected_notes)

# Generate markov chain
markov_chain = Markov(1)
markov = markov_chain.transition_matrix(expected_notes)

# Generate a sequence of notes using the markov chain
observed_notes = markov_chain.generate_sequence(markov, length)


new_notes = []
new_chords = []

# Prepare the data by removing occurrences that do not occur in either set
for note in observed_notes:
    if note in expected_notes:
        new_notes.append(note)

for chord in expected_notes:
    if chord in new_notes:
        new_chords.append(chord)


unique_chord, expected = np.unique(new_chords, return_counts=True)
unique_notes, observed = np.unique(new_notes, return_counts=True)

print(expected.tolist())
print(observed.tolist())

data = [expected.tolist(), observed.tolist()]
chi2, p, dof, ex = chi2_contingency(data)

print(chi2)
# interpret p-value
alpha = 0.1
print("p value is " + str(p))
if p <= alpha:
    print('Dependent (reject H0)')
else:
    print('Independent (H0 holds true)')

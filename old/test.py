import os

import midi_helper as helper
from markov import Markov

"""# Get a list of all files in the midi dir with the .mid extension
files = [f for f in os.listdir('./midi') if f.endswith(".mid")]
for count, f in enumerate(files):
    print(f"{count + 1}: {f}")

filename = files[int(input("Select file: ")) - 1]"""

# Extract the notes from midi file using midi helper
midi_extraction = helper.ExtractMidi(f"midi/beethoven_opus10_1.mid")
midi_extraction.parse_midi()
chords = midi_extraction.get_notes()


# Generate markov chain
markov_chain = Markov(3)
#print(midi_extraction.get_durations())
durations_as_str = [str(a) for a in midi_extraction.get_durations()]
markov = markov_chain.transition_matrix(durations_as_str)

# Generate a sequence of notes using the markov chain
notes = markov_chain.generate_sequence(markov)

print(notes)



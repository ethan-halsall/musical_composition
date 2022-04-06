import os
from math import floor
from shutil import move

import numpy as np
from music21 import converter, instrument, note, chord
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.pitch import PitchException
from music21.stream import Part
import string
from random import choice


class Generate:
    def __init__(self, segments, rules):
        self.segments = segments
        self.dict, self.alphabet = self.generate_dict()
        self.rules = rules
        self.axiom = self.alphabet[0]

    def generate_dict(self):
        dict = {}
        alphabet = list(string.ascii_lowercase)
        alphabet_used = []
        for count, segment in enumerate(self.segments):
            alphabet_used.append(alphabet[count])
            dict[alphabet[count]] = segment

        return dict, alphabet_used

    def l_system(self, axiom, n):
        out = ""
        for char in axiom:
            if char in self.rules:
                out += self.rules[char]
            else:
                out += char
        n -= 1
        if n > 0:
            return self.l_system(out, n)
        return out

    def convert_to_sequence(self, melody):
        states = {}
        for key, _ in self.dict.items():
            states[key] = 0

        out = []
        durations = []
        for char in melody:
            if char in self.dict:
                state = states[char]
                curr = self.dict[char].get_notes()
                curr_dur = self.dict[char].get_durations()

                curr_state = 4 * (1 + state)

                # Make sure we round down using floor
                if state < floor(len(curr) / 4):  # use 4 notes for now, since we are generating sequences of 4^n
                    curr_state = 4 * (1 + state)

                    for i in range(curr_state):
                        out.append(curr[i])
                        durations.append(curr_dur[i])

                    states[char] += 1
                else:
                    states[char] = 0

        return out, durations

    # Pretty generic rules - this needs serious work and testing
    def generate_rules(self):
        rules = {}
        num_rules = floor(len(self.alphabet) / 4) + 1
        for i in range(num_rules):
            char = self.alphabet[i]
            if i % 2 == 0 and i + 2 < len(self.alphabet):
                rules[char] = "".join(self.alphabet)
            else:
                rules[char] = f"{char}{choice(self.alphabet)}"

        print(rules)
        self.rules = rules


class Segment:
    def __init__(self, notes, filename, index, durations, key, do_prune, do_quantize):
        self.notes = notes
        self.durations = durations
        self.filename = filename
        self.index = index
        self.key = key
        self.part = self.__to_part()

        if do_prune:
            self.prune()

        if do_quantize:
            self.quantize()

    def __to_part(self):
        part = Part()
        part.append(instrument.Piano())
        for i in range(len(self.notes)):
            note = self.notes[i]
            duration = self.durations[i]

            if note == "rest":
                part.append(Rest(quarterLength=duration))
            else:
                part.append(Chord(note, quarterLength=duration))

        return part

    def write_to_midi(self, export=False, filename=None):
        mf = streamToMidiFile(self.part)
        if export:
            mf.open(filename, 'wb')
        else:
            mf.open(f"tmp/{self.index}_{self.filename}", 'wb')
        mf.write()
        mf.close()

    def play(self):
        # Play midi file using timidity binary
        self.write_to_midi()

        try:
            os.system(f"timidity -Os tmp/{self.index}_{self.filename}")
        except Exception as e:
            print(f"Music could not be played due to: {e}")

        # Remove temporary midi file from /tmp
        os.remove(f"tmp/{self.index}_{self.filename}")

    def prune(self):
        notes = self.notes
        midi = []

        for note in notes:
            try:
                pitches = Chord(note).pitches
                avg = 0
                for pitch in pitches:
                    avg += int(pitch.midi)
                midi.append(avg / len(pitches))
            except PitchException:
                pass

        distances = []
        for (x, y) in zip(midi, midi[1:]):
            distances.append(abs(floor(x - y)))

        std = np.std(distances)
        mean = np.mean(distances)

        for i in range(len(distances)):
            if distances[i] > mean + (2 * std):
                notes[i - 1] = notes[i]
        self.notes = notes

    def quantize(self):
        curr = 0
        for i in range(len(self.durations)):
            if curr % 4 == 0:
                curr = self.durations[i]
            elif ((curr + self.durations[i]) / 4) > 1:
                self.durations[i] = 4 - curr
                curr = 0
            else:
                curr += self.durations[i]

    def get_notes(self):
        return self.notes

    def get_key(self):
        return self.key

    def get_durations(self):
        return self.durations


class Extract:
    def __init__(self, filename):
        self._filename = filename
        self._chords = []
        self._durations = []
        self.stream = converter.parse(self._filename)
        self.instruments = instrument.partitionByInstrument(self.stream).parts

    def write(self):
        conv = converter.subConverters.ConverterLilypond()
        conv.write(self.stream, fmt='lilypond',
                   fp=self._filename, subformats=['pdf'])
        move(f"{self._filename}.pdf", f"pdf/{self._filename[5:]}.pdf")

    def get_key(self):
        return self.stream.analyze('key')

    def get_instruments(self):
        return self.instruments

    def parse_midi(self, inst='Piano'):
        for part in self.instruments:
            # signature = part[meter.TimeSignature][0]
            # select elements of only piano
            if inst in str(part):
                notes_to_parse = part.recurse()
                # finding whether a particular element is note or a chord
                for element in notes_to_parse:
                    # notes
                    if isinstance(element, note.Note):
                        self._chords.append(str(element.pitch))
                        self._durations.append(element.quarterLength)
                    # chords
                    elif isinstance(element, chord.Chord):
                        self._chords.append(' '.join(str(n.pitch)
                                                     for n in element))
                        self._durations.append(element.quarterLength)
                    # rests
                    elif isinstance(element, note.Rest):
                        self._chords.append(element.name)
                        self._durations.append(element.quarterLength)

    def get_chords(self):
        if not self._chords:
            print("Midi has not been parsed")
            return None
        return self._chords

    def get_durations(self):
        if not self._durations:
            print("Midi has not been parsed")
            return None
        return self._durations

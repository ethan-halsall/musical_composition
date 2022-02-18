import os
from shutil import move

from music21 import converter, instrument, note, chord
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.stream import Part
import string
from random import choice


class Generate:
    def __init__(self, segments, rules):
        self.segments = segments
        self.dict, self.axiom = self.generate_dict()
        self.rules = rules

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
        out = []
        for char in melody:
            if char in self.dict:
                out.append(self.dict[char])

        return out

    # Pretty generic rules - todo improve these
    def generate_rules(self):
        rules = {}
        for key, _ in self.dict.items():
            rules[key] = f"{choice(self.axiom)}{choice(self.axiom)}"

        self.rules = rules


class Segment:
    def __init__(self, segment, filename, index, durations):
        self.segment = segment
        self.durations = durations
        self.filename = filename
        self.index = index
        self.part = self.__to_part()

    def __to_part(self):
        part = Part()
        part.append(instrument.Piano())
        for i in range(len(self.segment)):
            note = self.segment[i]
            duration = self.durations[i]

            if note == "rest":
                part.append(Rest(quarterLength=1))
            else:
                part.append(Chord(note, quarterLength=1))

        return part

    def write_to_midi(self, export=False):
        mf = streamToMidiFile(self.part)
        if export:
            mf.open(f"out/{self.index}_{self.filename}", 'wb')
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

    def get_segment(self):
        return self.segment


class Extract:
    def __init__(self, filename):
        self._filename = filename
        self._chords = []
        self._durations = []
        self.stream = converter.parse(self._filename)
        self.instruments = instrument.partitionByInstrument(self.stream).parts

    def write(self):
        conv = converter.subConverters.ConverterLilypond()
        conv.write(self.stream, fmt='lilypond', fp=self._filename, subformats=['pdf'])
        move(f"{self._filename}.pdf", f"pdf/{self._filename[5:]}.pdf")

    def get_key(self):
        self.stream.analyze('key')

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
                        self._chords.append(' '.join(str(n.pitch) for n in element))
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

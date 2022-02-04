import os
from shutil import move

from music21 import converter, instrument, note, chord
from music21.chord import Chord
from music21.midi.translate import streamToMidiFile
from music21.note import Rest
from music21.stream import Part


class Segment:
    def __init__(self, segment, filename, index):
        self.segment = segment
        self.filename = filename
        self.index = index
        self.part = self.__to_part()

    def __to_part(self):
        part = Part()
        part.append(instrument.Piano())
        for i in range(len(self.segment)):
            note = self.segment[i]
            # duration = durations[i]

            if note == "rest":
                part.append(Rest(quarterLength=1))
            else:
                part.append(Chord(note, quarterLength=1))

        return part

    def write_to_midi(self):
        mf = streamToMidiFile(self.part)
        mf.open(f"tmp/{self.filename}_{self.index}", 'wb')
        mf.write()
        mf.close()

    def play(self):
        # Play midi file using timidity binary
        self.write_to_midi()
        os.system(f"timidity -Os tmp/{self.filename}_{self.index}")

        # Remove temporary midi file from /tmp
        os.remove(f"tmp/{self.filename}_{self.index}")


class Extract:
    def __init__(self, filename):
        self._filename = filename
        self._chords = []
        self._durations = []
        self.stream = converter.parse(self._filename)

    def write(self):
        conv = converter.subConverters.ConverterLilypond()
        conv.write(self.stream, fmt='lilypond', fp=self._filename, subformats=['pdf'])
        move(f"{self._filename}.pdf", f"pdf/{self._filename[5:]}.pdf")

    def get_key(self):
        self.stream.analyze('key')

    def parse_midi(self, inst='Piano'):
        music = self.stream

        for part in instrument.partitionByInstrument(music).parts:
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

import sys
import traceback
from random import randint

from PyQt5.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal

import midi_helper as helper
from database import Database
from markov import Markov


class WorkerSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class ProcessMidiWorker(QRunnable):
    def __init__(self, item):
        super().__init__()
        self.signals = WorkerSignals()
        self.filename = item
        self.midi_extraction = None

    @pyqtSlot()
    def run(self):
        try:
            # Extract the notes from midi file using midi helper
            self.midi_extraction = helper.ExtractMidi(f"midi/{self.filename}")
        finally:
            if self.midi_extraction is not None:
                self.signals.result.emit(self.midi_extraction)


class GenerateSegmentsWorker(QRunnable):
    def __init__(self, item, filename, instrument, markov_depth, max_length):
        super().__init__()
        self.signals = WorkerSignals()
        self.filename = filename
        self.instrument = instrument
        self.item = item
        self.order = markov_depth
        self.max_length = max_length

    @pyqtSlot()
    def run(self):
        try:
            database = Database()
            # Extract the notes from midi file using midi helper
            midi_extraction = self.item
            midi_extraction.parse_midi(inst=self.instrument)
            notes = midi_extraction.get_notes()
            key = midi_extraction.get_key()

            # Generate markov chain
            markov_chain = Markov(self.order)
            markov_notes = markov_chain.transition_matrix(notes)
            float_durations = [float(a)
                               for a in midi_extraction.get_durations()]
            durations_as_str = [str(a) for a in float_durations]
            durations_markov = markov_chain.transition_matrix(durations_as_str)

            # Generate 15 sequence of notes using the markov chain
            sequences_notes = []
            sequence_durations = []
            for _ in range(15):
                success = False
                while not success:
                    try:
                        # Generate a segment of length some power 2^n
                        length = 2 ** randint(2, self.max_length)
                        notes = markov_chain.generate_sequence(
                            markov_notes, length=length)
                        durations = markov_chain.generate_sequence(
                            durations_markov, length=length)
                        sequence_durations.append(durations)
                        sequences_notes.append(notes)
                        success = True
                    except Exception as e:
                        print(e)

            database.insert_or_update(self.filename, database.to_json(sequences_notes), database.to_json(sequence_durations),
                                      str(key))
        except Exception as e:
            print(e)
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit(self.filename)


class PlayMidiWorker(QRunnable):
    def __init__(self, segment: helper.Segment):
        super().__init__()
        self.current_segment = segment
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            self.current_segment.play()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit("")


class FetchDataWorker(QRunnable):
    def __init__(self, filename, do_prune, quantize):
        QRunnable.__init__(self)
        self.filename = filename
        self.do_prune = do_prune
        self.do_quantize = quantize
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        current_segments = None
        try:
            database = Database()
            json_sequence = database.get_sequence(self.filename)
            json_durations = database.get_durations(self.filename)
            key = database.get_key(self.filename)

            current_segments = []
            sequences = database.to_lst(json_sequence)
            durations = database.to_lst(json_durations)
            for i in range(len(sequences)):
                duration = [float(a) for a in durations[i]]
                current_segments.append(helper.Segment(
                    sequences[i], self.filename, i, duration, key, self.do_prune, self.do_quantize))
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            if current_segments is not None:
                self.signals.result.emit(current_segments)

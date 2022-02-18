import sys
import sys
import traceback
from random import randint

from PyQt5.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal

import midi_helper as helper
from markov import Markov


class WorkerSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class SequenceWorker(QRunnable):
    def __init__(self, item, database, filename, instrument):
        super().__init__()
        self.signals = WorkerSignals()
        self.database = database
        self.filename = filename
        self.instrument = instrument
        self.item = item

    @pyqtSlot()
    def run(self):
        try:

            # Extract the notes from midi file using midi helper
            midi_extraction = self.item
            midi_extraction.parse_midi(inst=self.instrument)
            chords = midi_extraction.get_chords()
            key = midi_extraction.get_key()

            print(key)

            # Generate markov chain
            markov_chain = Markov(3)
            markov = markov_chain.transition_matrix(chords)
            float_durations = [float(a)
                               for a in midi_extraction.get_durations()]
            durations_as_str = [str(a) for a in float_durations]
            durations_markov = markov_chain.transition_matrix(durations_as_str)

            # Generate 15 sequence of notes using the markov chain
            sequences = []
            durations = []
            for _ in range(15):
                success = False
                while not success:
                    try:
                        # Generate a segment of length some power 2^n
                        length = 2 ** randint(2, 4)
                        notes = markov_chain.generate_sequence(
                            markov, length=length)
                        durations.append(markov_chain.generate_sequence(
                            durations_markov, length=length))
                        # print(durations)
                        sequences.append(notes)
                        success = True
                    except Exception as e:
                        print(e)

            self.database.insert(self.filename, self.database.to_json(sequences), self.database.to_json(durations),
                                 str(key))
        except Exception as e:
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

    def run(self) -> None:
        try:
            self.current_segment.play()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit("")


class DatabaseWorker(QRunnable):
    def __init__(self):
        QRunnable.__init__(self)

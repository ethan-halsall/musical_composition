import os
import traceback

from PyQt5.QtCore import QRunnable, pyqtSlot, QThreadPool, QObject, pyqtSignal
from PyQt5.QtWidgets import *
import sys

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from music21 import instrument
from music21.chord import Chord
from music21.note import Rest
from music21.stream import Part

import midi_helper as helper
from database import DatabaseWorker
from l_system import lsystem, parse_lengths
from markov import Markov
from random import randint, choice
import itertools


class WorkerSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class SequenceWorker(QRunnable):
    def __init__(self, item, database):
        super().__init__()
        self.signals = WorkerSignals()
        self.database = database
        self.item = item
        self.seed = 0

    @pyqtSlot()
    def run(self):
        try:
            filename = self.item.text()

            # Extract the notes from midi file using midi helper
            midi_extraction = helper.Extract(f"midi/{filename}")
            midi_extraction.parse_midi()
            chords = midi_extraction.get_chords()

            # Generate markov chain
            markov_chain = Markov(3)
            markov = markov_chain.transition_matrix(chords)

            # Generate 15 sequence of notes using the markov chain
            sequences = []
            for _ in range(15):
                success = False
                while not success:
                    try:
                        # Generate a segment of length some power 2^n
                        length = 2 ** randint(2, 3)
                        notes = markov_chain.generate_sequence(markov, length=length)
                        sequences.append(notes)
                        success = True
                    except Exception as e:
                        print(e)

            self.database.insert(filename, self.database.to_json(sequences))
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit(filename)  # Done

        # notes = [choice(blocks) for x in range(50)]

        # rules = {"a": "b", "b": "(a)[b]"}
        # rules = {"a": "b[a]b(a)a", "b": "bb"}
        # rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}
        # rules = {"a": "c(ba(b))c[ba[b]]", "b": "c(be)c[bf]", "c": "cgg"}
        # rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cd"}

        # tree = lsystem("a", rules, 8)
        # durations = parse_lengths(tree)
        # print(durations)
        # self.filename = "mozasasaassaas"
        # helper.write_to_midi(f"{self.filename[:-4]}_{self.seed}.mid", list(itertools.chain.from_iterable(notes)),
        #                     durations)

        # Play midi file using timidity binary
        # os.system(f"timidity -Os out/{self.filename[:-4]}_{self.seed}.mid")


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, figure):
        fig = figure
        super(MplCanvas, self).__init__(fig)


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.list_widget = QListWidget()
        self.window().resize(1280, 720)

        self.sequence_generating = False

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # Get a list of all files in the midi dir with the .mid extension
        files = [f for f in os.listdir('./midi') if f.endswith(".mid")]
        self.graph_positions = {}
        for count, file in enumerate(files):
            self.list_widget.insertItem(count, file)
            self.graph_positions[file] = 0
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.clicked.connect(self.clicked)
        self.layout.addWidget(self.list_widget, 0, 0, 1, 2)

        self.button_sequence = QPushButton()
        self.button_sequence.setText("Generate sequences")
        self.button_sequence.clicked.connect(self.on_button_sequence)
        self.layout.addWidget(self.button_sequence, 1, 0)

        self.button_generate = QPushButton()
        self.button_generate.setText("Generate music")
        self.button_generate.clicked.connect(self.on_button_generate)
        self.layout.addWidget(self.button_generate, 1, 1)

        self.button_previous = QPushButton()
        self.button_previous.setText("Prev")
        self.button_previous.clicked.connect(self.prev_graph)
        self.layout.addWidget(self.button_previous, 1, 8)

        self.button_forward = QPushButton()
        self.button_forward.setText("Next")
        self.button_forward.clicked.connect(self.next_graph)
        self.layout.addWidget(self.button_forward, 1, 9)

        # Create a database object on a background thread
        self.database = DatabaseWorker()
        self.threadpool.start(self.database)

    def next_graph(self):
        item = self.list_widget.currentItem().text()
        self.graph_positions[item] += 1
        self.draw_graph(item, pos=self.graph_positions[item])

    def prev_graph(self):
        item = self.list_widget.currentItem().text()
        self.graph_positions[item] -= 1
        self.draw_graph(item, pos=self.graph_positions[item])

    def clicked(self, qmodelindex):
        item = self.list_widget.currentItem()
        self.draw_graph(item.text())

    def draw_graph(self, filename, pos=0):
        database = DatabaseWorker()
        self.threadpool.start(database)
        try:
            json_sequence = database.get_sequence(filename)
        except IndexError as e:
            return
        sequence = database.to_lst(json_sequence)

        block = sequence[pos]
        part = Part()
        part.append(instrument.Piano())
        for i in range(len(block)):
            note = block[i]
            if note == "rest":
                part.append(Rest(quarterLength=1))
            else:
                part.append(Chord(note, quarterLength=1))
        plot = part.plot(doneAction=None)
        sc = MplCanvas(plot.figure)
        self.layout.addWidget(sc, 0, 2, 1, 8)

    def thread_complete(self, filename):
        self.sequence_generating = False
        self.draw_graph(filename)

    def on_button_sequence(self):
        if not self.sequence_generating:
            items = self.list_widget.currentItem()
            worker = SequenceWorker(items, self.database)
            self.threadpool.start(worker)
            worker.signals.finished.connect(self.thread_complete)
            self.sequence_generating = True
        else:
            print("Worker already running")

    def on_button_generate(self):
        print("wew")


app = QApplication(sys.argv)
screen = Window()
screen.show()
sys.exit(app.exec_())

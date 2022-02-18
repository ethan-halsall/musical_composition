import os
import sys

from PyQt5.QtCore import QRunnable, pyqtSlot, QThreadPool, Qt
from PyQt5.QtWidgets import *
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

import midi_helper as helper
import workers
from database import DatabaseWorker


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, figure):
        fig = figure
        super(MplCanvas, self).__init__(fig)


class GeneratorPopup(QWidget):
    def __init__(self, segment, threadpool):
        QWidget.__init__(self)
        self.window().resize(1280, 720)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.threadpool = threadpool

        self.segment = segment
        self.figure = None
        self.now_playing = False

        self.button_play = QPushButton()
        self.button_play.setText("Play")
        self.button_play.clicked.connect(self.play)
        self.layout.addWidget(self.button_play, 1, 7)

        self.button_export = QPushButton()
        self.button_export.setText("Export")
        self.button_export.clicked.connect(self.export)
        self.layout.addWidget(self.button_export, 1, 6)

        self.draw_graph()

    def draw_graph(self):
        part = self.segment.part
        plot = part.plot(doneAction=None)
        self.figure = MplCanvas(plot.figure)
        self.layout.addWidget(self.figure, 0, 0, 1, 8)

    def play(self):
        if not self.now_playing:
            worker = workers.PlayMidiWorker(self.segment)
            self.threadpool.start(worker)
            worker.signals.finished.connect(self.playing_complete)
            self.now_playing = True
        else:
            print("Music already playing")

    def export(self):
        self.segment.write_to_midi(export=True)

    def playing_complete(self):
        self.now_playing = False


class InstrumentSelector(QWidget):
    def __init__(self, filename, threadpool, database):
        QWidget.__init__(self)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.list_widget = QListWidget()
        self.window().resize(500, 500)
        self.filename = filename
        self.layout.addWidget(self.list_widget)
        self.threadpool = threadpool
        self.database = database

        self.midi_extraction = None

        self.signals = workers.WorkerSignals()

        self.button_sequence = QPushButton()
        self.button_sequence.setText("Select instrument")
        self.button_sequence.clicked.connect(self.select_instrument)
        self.layout.addWidget(self.button_sequence, 2, 0)

        worker = ProcessMidiWorker(self.filename)
        self.threadpool.start(worker)
        worker.signals.result.connect(self.display_midi_data)

    def display_midi_data(self, midi_extraction):
        self.midi_extraction = midi_extraction
        # print(self.midi_extraction.get_key())
        for count, inst in enumerate(midi_extraction.get_instruments()):
            self.list_widget.insertItem(count, str(inst))

    def sequence_complete(self, filename):
        self.signals.finished.emit(filename)
        self.destroy()

    def select_instrument(self):
        if self.midi_extraction is None:
            return

        item = self.list_widget.currentItem().text()

        worker = workers.SequenceWorker(
            self.midi_extraction, self.database, self.filename, item)
        self.threadpool.start(worker)
        worker.signals.finished.connect(self.sequence_complete)


class ProcessMidiWorker(QRunnable):
    def __init__(self, item):
        super().__init__()
        self.signals = workers.WorkerSignals()
        self.filename = item
        self.midi_extraction = None

    @pyqtSlot()
    def run(self):
        try:
            # Extract the notes from midi file using midi helper
            self.midi_extraction = helper.Extract(f"midi/{self.filename}")
        finally:
            if self.midi_extraction is not None:
                self.signals.result.emit(self.midi_extraction)


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.selector = None
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.list_widget = QListWidget()
        self.window().resize(1280, 720)

        self.current_segments = None
        self.current_segment = None
        self.current_row = ""
        self.sequence_generating = False
        self.now_playing = False
        self.sequences = []
        self.figure = None

        self.popup = None

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" %
              self.threadpool.maxThreadCount())

        # Get a list of all files in the midi dir with the .mid extension
        files = [f for f in os.listdir('./midi') if f.endswith(".mid")]
        self.graph_positions = {}
        for count, file in enumerate(files):
            self.list_widget.insertItem(count, file)
            self.graph_positions[file] = 0
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.clicked.connect(self.clicked)
        self.list_widget.setCurrentRow(0)
        self.layout.addWidget(self.list_widget, 0, 0, 2, 2)

        self.button_sequence = QPushButton()
        self.button_sequence.setText("Generate sequences")
        self.button_sequence.clicked.connect(self.on_button_sequence)
        self.layout.addWidget(self.button_sequence, 2, 0)

        self.button_generate = QPushButton()
        self.button_generate.setText("Generate music")
        self.button_generate.clicked.connect(self.on_button_generate)
        self.layout.addWidget(self.button_generate, 2, 1)

        # Create button for going to previous graph
        self.button_previous = QPushButton()
        self.button_previous.setText("Prev")
        self.button_previous.clicked.connect(self.prev_graph)
        self.layout.addWidget(self.button_previous, 1, 8)

        # Create button for going to next graph
        self.button_forward = QPushButton()
        self.button_forward.setText("Next")
        self.button_forward.clicked.connect(self.next_graph)
        self.layout.addWidget(self.button_forward, 1, 9)

        # Indicator label
        self.indicator = QLabel()
        self.indicator.setText("0/0")
        self.indicator.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.indicator, 2, 9)

        # Create button for going to next graph
        self.button_play = QPushButton()
        self.button_play.setText("Play")
        self.button_play.clicked.connect(self.play)
        self.layout.addWidget(self.button_play, 1, 7)

        self.click_box = QCheckBox("Include")
        self.click_box.clicked.connect(self.click_box_listener)
        self.layout.addWidget(self.click_box, 2, 8)

        # Key label
        self.key_label = QLabel()
        self.key_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.key_label, 2, 7)

        # Create a database object on a background thread
        self.database = DatabaseWorker()
        self.threadpool.start(self.database)

        # self.draw_graph(files[0], pos=0) this needs to be run after constructor

    def click_box_listener(self):
        segment = self.current_segment
        if self.click_box.isChecked():
            self.sequences.append(segment)
        else:
            self.sequences.remove(segment)

        print(self.sequences)

    def next_graph(self):
        item = self.list_widget.currentItem().text()
        new_pos = self.graph_positions[item] + 1
        if new_pos < len(self.current_segments):
            self.graph_positions[item] += 1
            self.draw_graph(item, pos=self.graph_positions[item])

    def prev_graph(self):
        item = self.list_widget.currentItem().text()
        new_pos = self.graph_positions[item] - 1
        if new_pos >= 0:
            self.graph_positions[item] -= 1
            self.draw_graph(item, pos=self.graph_positions[item])

    def clicked(self):
        item = self.list_widget.currentItem()
        self.draw_graph(item.text())

    def draw_graph(self, filename, pos=0):
        if self.current_segments is None or filename != self.current_row:
            self.current_row = filename
            database = DatabaseWorker()
            self.threadpool.start(database)
            try:
                json_sequence = database.get_sequence(filename)
                json_durations = database.get_durations(filename)
                key = database.get_key(filename)
            except IndexError as e:
                if self.figure is not None:
                    self.figure.close()
                fig = plt.figure()
                self.figure = MplCanvas(fig)
                self.layout.addWidget(self.figure, 0, 2, 1, 8)
                self.click_box.setChecked(False)
                self.indicator.setText("0/0")
                self.key_label.setText("")
                return

            self.current_segments = []
            segments = database.to_lst(json_sequence)
            durations = database.to_lst(json_durations)
            for i in range(len(segments)):
                duration = [float(a) for a in durations[i]]
                self.current_segments.append(helper.Segment(
                    segments[i], filename, pos, duration, key))

        if self.current_segments[pos] in self.sequences:
            self.click_box.setChecked(True)
        else:
            self.click_box.setChecked(False)

        segment = self.current_segments[pos]

        if self.figure is not None:
            self.figure.close()

        self.key_label.setText(segment.get_key()) # bug here does not show after regen
        part = segment.part
        plot = part.plot(doneAction=None)
        self.figure = MplCanvas(plot.figure)
        self.layout.addWidget(self.figure, 0, 2, 1, 8)
        self.indicator.setText(
            f"{self.graph_positions[filename] + 1}/{len(self.current_segments)}")
        self.current_segment = segment

    def play(self):
        if self.current_segment is not None and not self.now_playing:
            worker = workers.PlayMidiWorker(self.current_segment)
            self.threadpool.start(worker)
            worker.signals.finished.connect(self.playing_complete)
            self.now_playing = True
        else:
            print("Music already playing")

    def playing_complete(self):
        self.now_playing = False

    def sequence_complete(self, filename):
        self.sequence_generating = False
        self.draw_graph(filename)

    def on_button_sequence(self):
        if not self.sequence_generating:
            item = self.list_widget.currentItem().text()
            self.selector = InstrumentSelector(
                item, self.threadpool, self.database)
            self.selector.show()
            self.selector.signals.finished.connect(self.sequence_complete)
            self.sequence_generating = True
        else:
            print("Worker already running")

    def on_button_generate(self):
        rules = {"a": "b", "b": "ba", "c": "bc"}
        if self.sequences:
            gen = helper.Generate(self.sequences, rules)
            gen.generate_rules()
            melody = gen.l_system(gen.axiom, 2)
            sequences = gen.convert_to_sequence(melody)

            notes = []
            durations = []
            for sequence in sequences:
                notes += sequence.get_segment()
                durations += sequence.durations

            segment = helper.Segment(
                notes, "test.mid", 0, durations, sequences[0].key)

            self.popup = GeneratorPopup(segment, self.threadpool)
            self.popup.show()


app = QApplication(sys.argv)
screen = Window()
screen.show()
sys.exit(app.exec_())

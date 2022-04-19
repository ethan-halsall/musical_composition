import os
import random
import threading
import tkinter as tk
from tkinter import messagebox

import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from music21 import graph
from scipy.stats import chisquare

import midi_helper as helper
from l_system import lsystem, parse_lengths
from markov import Markov


class Window:
    def __init__(self):
        self.seed = random.randint(0, 2 ** 32 - 1)
        np.random.seed(self.seed)
        self.window = tk.Tk()
        self.window.title('Music')
        self.window.geometry("500x500")
        self.thread = threading.Thread()

        self.frame = tk.Frame(self.window)
        tk.Label(self.frame, text="Midi files").pack(side=tk.TOP)
        self.lb = tk.Listbox(self.frame)
        self.lb.pack(padx=10, fill=tk.BOTH, expand=True)
        tk.Button(self.frame, text='Refresh', command=self.generate_music).pack(pady=10, padx=10, side=tk.RIGHT)
        #tk.Button(self.frame, text='Add', command=self.generate_music).pack(pady=10, padx=10, side=tk.LEFT)
        self.frame.pack(side=tk.LEFT, fill=tk.Y, ipadx=40)

        # Get a list of all files in the midi dir with the .mid extension
        files = [f for f in os.listdir('../midi') if f.endswith(".mid")]
        for count, file in enumerate(files):
            self.lb.insert(count, file)

        self.frame_right = tk.Frame(self.window)
        tk.Button(self.frame_right, text='Generate music', command=self.generate_music).pack(pady=10, padx=10)
        self.show = tk.Label(self.frame_right)
        self.show.pack()
        self.frame_right.pack(pady=50)

        # self.window.bind("<<event-graph>>", self.draw_graph)

        self.current_stream = None
        self.graph_canvas = None
        # self.seed_box = tk.Text(self.frame_right, height=1)
        # tk.Label(self.frame_right, text="Seed").pack(side=tk.LEFT)
        # tk.Button(self.frame_right, text='Update', command=self.update_seed).pack(side=tk.RIGHT)
        # self.seed_box.pack(pady=10, padx=10, fill=tk.X, expand=True)

    def update_seed(self):
        try:
            self.seed = int(self.seed_box.get('1.0', 'end-1c'))
            np.random.seed(self.seed)
            self.seed_box.delete('1.0', tk.END)
        except ValueError:
            self.seed_box.delete('1.0', tk.END)
            self.seed_box.insert(tk.END, "Invalid")

    def draw_graph(self, event):
        if self.graph_canvas is not None:
            self.graph_canvas.get_tk_widget().pack_forget()

        # the figure that will contain the plot
        fig = Figure(figsize=(5, 5),
                     dpi=100)

        # list of squares
        y = [i ** 2 for i in range(101)]

        # adding the subplot
        plot1 = fig.add_subplot(111)

        scatter = graph.plot.HistogramPitchClass(self.current_stream)
        # scatter.title = 'Bach and his notes'
        scatter.run()

        # plotting the graph
        plot1.plot(y)

        # creating the Tkinter canvas
        # containing the Matplotlib figure
        self.graph_canvas = FigureCanvasTkAgg(scatter.figure,
                                              master=self.window)
        self.graph_canvas.draw()

        # creating the Matplotlib toolbar
        # toolbar = NavigationToolbar2Tk(self.graph_canvas,
        #                               self.window)
        # toolbar.update()

        # placing the toolbar on the Tkinter window
        self.graph_canvas.get_tk_widget().pack()

    def gen(self, filename):
        # Extract the notes from midi file using midi helper
        midi_extraction = helper.ExtractMidi(f"midi/{filename}")
        midi_extraction.parse_midi()
        values1, size1 = midi_extraction.get_frequency()
        chords = midi_extraction.get_notes()

        self.current_stream = midi_extraction.stream

        # self.window.event_generate("<<event-graph>>")  # trigger event in main thread

        # Generate markov chain
        markov_chain = Markov(3)
        markov = markov_chain.transition_matrix(chords)

        # Generate a sequence of notes using the markov chain
        notes = markov_chain.generate_sequence(markov)

        # rules = {"a": "b[a]b(a)a", "b": "bb"}
        rules = {"a": "d[dbe](dce)e", "b": "d[daf](dcf)f", "c": "d[dbg](dag)g"}

        rules = {"a": "b[a[ba]]", "b": "b((b)a)c", "c": "cdb"}

        tree = lsystem("abacd", rules, 7)

        durations = parse_lengths(tree)

        helper.write_to_midi(f"{filename[:-4]}_{self.seed}.mid", notes, durations)

        # Play midi file using timidity binary
        os.system(f"timidity -Os out/{filename[:-4]}_{self.seed}.mid")

    def generate_music(self):
        if not self.thread.is_alive():
            filename = self.lb.get(tk.ANCHOR)
            self.show.config(text=f"Generating music based on\n{filename}")
            self.thread = threading.Thread(target=self.gen, args=[filename])
            self.thread.start()
        else:
            messagebox.showerror('Error', 'Cannot do multiple generations at the same time')

    def start(self):
        self.window.mainloop()


gui = Window()
gui.start()

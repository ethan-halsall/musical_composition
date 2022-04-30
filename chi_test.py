import os

import numpy as np
import pandas as pd

import midi_helper as helper
from markov import Markov
from scipy.stats import chi2_contingency
from scipy.stats import chi2


def chi(filename, order):
    # Extract the notes from midi file using midi helper
    midi_extraction = helper.ExtractMidi(f"midi/{filename}")

    midi_extraction.parse_midi()

    expected_notes = midi_extraction.get_notes()
    length = len(expected_notes)

    # Generate markov chain
    markov_chain = Markov(order)
    markov = markov_chain.transition_matrix(expected_notes)

    # Generate a sequence of notes using the markov chain
    observed_notes = markov_chain.generate_sequence(markov, length)

    new_observed = []
    new_expected = []

    # Prepare the data by removing occurrences that do not occur in either set
    for note in observed_notes:
        if note in expected_notes:
            new_observed.append(note)

    for note in expected_notes:
        if note in new_observed:
            new_expected.append(note)

    # Create contingency tables for expected and observed frequencies
    unique_chord, expected = np.unique(new_expected, return_counts=True)
    unique_notes, observed = np.unique(new_observed, return_counts=True)

    table = [expected.tolist(), observed.tolist()]
    chi2_stat, p, dof, expected = chi2_contingency(table)

    prob = 0.95
    # Generate critical value
    critical = chi2.ppf(prob, dof)

    return dof, critical, chi2_stat


# Get a list of all files in the midi dir with the .mid extension and run the chi-squre test
order = 1
data = {"midi file": [], "degrees of freedom": [], "critical": [], "test statistic": [], "reject H0": []}
files = [f for f in os.listdir('./midi') if f.endswith(".mid")]
for file in files:
    try:
        dof, critical, chi2_stat = chi(file, order)
        data['midi file'].append(file)
        data["degrees of freedom"].append(dof)
        data["critical"].append(round(critical, 3))
        data["test statistic"].append(round(chi2_stat, 3))

        if abs(chi2_stat) >= critical:
            data["reject H0"].append(True)
        else:
            data["reject H0"].append(False)

    except Exception:
        pass

# Convert data dictionary to dataframe
df = pd.DataFrame(data)

# Export to csv
df.to_csv('chi_square.csv')


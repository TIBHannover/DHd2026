import zipfile
import argparse
import csv

import numpy as np
import pandas as pd
from scipy.signal import correlate


def parse_args():
    parser = argparse.ArgumentParser(description="Test start and end of zip file")
    parser.add_argument("zip_file", help="Path to the zip file to test")
    return parser.parse_args()


def compute_optimal_shift(seq1, seq2):

    # Assuming seq1 and seq2 are your 1D arrays of data/signals
    # 'full' computes correlation at all possible shifts
    correlation = np.abs(
        np.correlate(seq1 - np.mean(seq1), seq2 - np.mean(seq2), mode="full")
    )

    correlation[: len(seq1)] = -1000
    print(correlation)
    lags = np.arange(-len(seq2) + 1, len(seq1))

    # Find the lag that maximizes the correlation
    optimal_lag = lags[np.argmax(correlation)]

    print(f"{optimal_lag / 1000} {len(seq1) / 1000}")


def main():
    args = parse_args()
    zip_file_path = args.zip_file
    gt_data = None
    data = None
    with zipfile.ZipFile(zip_file_path) as zip_file:
        print("Zip file opened successfully.")
        print("Contents of the zip file:")
        for name in zip_file.namelist():
            print(name)

            if name.startswith("GT: Shots.tsv"):
                with zip_file.open(name) as f:
                    csv_reader = csv.reader(
                        f.read().decode("utf-8").splitlines(), delimiter="\t"
                    )
                    next(csv_reader)  # Skip header
                    starts = []
                    ends = []
                    for row in csv_reader:
                        starts.append(int(float(row[1]) * 1000))
                        ends.append(int((float(row[1]) + float(row[3])) * 1000))

                    print("Start times:", starts)
                    print("End times:", ends)
                    gt_data = np.zeros(max(ends) + 1)
                    skip = False
                    for start, end in zip(starts, ends):
                        if skip:
                            continue
                        else:
                            gt_data[start:end] = 1
                        skip = not skip

            if name.startswith("Shots.tsv"):
                with zip_file.open(name) as f:
                    csv_reader = csv.reader(
                        f.read().decode("utf-8").splitlines(), delimiter="\t"
                    )
                    next(csv_reader)  # Skip header
                    starts = []
                    ends = []
                    for row in csv_reader:
                        starts.append(int(float(row[1]) * 1000))
                        ends.append(int((float(row[1]) + float(row[3])) * 1000))

                    print("Start times:", starts)
                    print("End times:", ends)
                    data = np.zeros(max(ends) + 1)
                    skip = False
                    for start, end in zip(starts, ends):
                        if skip:
                            continue
                        else:
                            data[start:end] = 1
                        skip = not skip

    # Example usage of the function (replace seq1 and seq2 with your actual data)
    compute_optimal_shift(gt_data, data)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Script to analyze and plot encoder results
#
# Copyright (c) 2025, Monocot Limited. All rights reserved
#
# This source code is subject to the terms of the BSD 2 Clause License. If the BSD 2 Clause License
# was not distributed with this source code in the LICENSE file, you can obtain it at
# https://opensource.org/license/bsd-2-clause

import matplotlib.pyplot as plt
import numpy as np
import os
import sqlite3
import sys

from argparse import ArgumentParser
from math import *
from matplotlib import ticker

from common import *

THIS_DIR = os.path.dirname(__file__)

def parse_args(argv):
  parser = ArgumentParser(prog=argv[0])

  parser.add_argument("-d", "--database", default=os.path.join(THIS_DIR, "results.sqlite"),
                      help="Path to database. Defaults to results.sqlite next to avif-comparison scripts")
  parser.add_argument("-s", "--source", action="append", dest="sources", metavar="SOURCE",
                      help="Source file(s) to compare. May be specified multiple times. "
                           "Defaults to all files which were encoded in all of the selected labels")
  parser.add_argument("-t", "--title", help="Title to use for the generated graphs", default="")
  parser.add_argument("-o", "--output-dir", help="Output directory, default results/", default="results/")
  parser.add_argument("-r", "--reference", default=None,
                      help="Encode set to use as a reference. This does not need to be used in the selected curves. "
                           "Defaults to the first point of the first curve")
  parser.add_argument("curves", nargs="+", help="Curves to plot, format is name:encode1:encode2:...", metavar="CURVE")

  return parser.parse_args(argv[1:])

# Custom function to format the log scale ticks nicely
# Based on https://stackoverflow.com/a/17209836
def format_x_tick(value, _):
  exp = int(floor(log10(value)))
  base = int(round(value / 10**exp))

  # Skip labelling the 7 and 9 subdivisions to avoid crowding.
  # These skipped subdivisions still get a tick mark on the axis to indicate
  # where they are
  if base in (7, 9): return ""

  if exp >= 1:
    return f"{value:.0f}x"
  elif exp == 0:
    # In this case the tick values are single-digit integers,
    # but add a decimal place anyway because 0.6, 0.8, 1.0, 2.0, ... looks prettier
    # than 0.6, 0.8, 1, 2, ...
    return f"{value:.1f}x"
  else:
    # For values < 1, display with the minimal number of decimal places
    fmt = f"%.{-exp:d}fx"
    return fmt % value

def format_y_tick(value, _):
  return f"{value:+3.0f}%"

def plot_size_vs_runtime(title, curves, labels, reference_index, representative_log_bpp, representative_log_nspp, filename):
  fig, ax = plt.subplots()
  ax.set(xlabel="Relative runtime", ylabel="BDRATE")
  ax.set_title(title)

  reference_log_nspp = representative_log_nspp[reference_index]
  reference_log_bpp = representative_log_bpp[reference_index]

  num_curves = len(curves)
  for curve_index, (name, label_indices) in enumerate(curves):
    xs = []
    ys = []

    for label_index in label_indices:
      xs.append(exp(representative_log_nspp[label_index] - reference_log_nspp))
      ys.append((exp(representative_log_bpp[label_index] - reference_log_bpp) - 1.0) * 100.0)

    # Distribute curve colours evenly across the rainbow if there are <12 plots
    colour_index = (curve_index * len(CURVE_COLOURS)) // num_curves
    ax.semilogx(xs, ys, color=CURVE_COLOURS[colour_index], marker="x", linestyle="-", label=name)

  ax.xaxis.set_minor_locator(ticker.LogLocator(subs=[1, 2, 3, 4, 5, 6, 7, 8, 9]))
  ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_x_tick))
  ax.xaxis.set_minor_formatter(ticker.FuncFormatter(format_x_tick))
  ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_y_tick))
  ax.yaxis.set_minor_formatter(ticker.FuncFormatter(format_y_tick))

  ax.tick_params(axis="x", which="major", labelsize="small")
  plt.xticks(minor=False, rotation=45, ha="right", rotation_mode="anchor")
  ax.tick_params(axis="x", which="minor", labelsize="small")
  plt.xticks(minor=True, rotation=45, ha="right", rotation_mode="anchor")

  plt.legend()

  # Matplotlib uses a fixed default size of 640x480 pixels @ 96dpi.
  # By asking for a higher DPI, we can double this to 1280x960 pixels,
  # which fits modern screens better
  plt.savefig(filename, dpi=192, bbox_inches="tight")

def main(argv):
  arguments = parse_args(argv)
  sources = arguments.sources

  curves = []
  labels = []
  for curve_spec in arguments.curves:
    if ":" not in curve_spec:
      print(f"Error: Bad curve spec {curve_spec}, should be in the format name:encode1:encode2:...")
    name, encodes = curve_spec.split(":", maxsplit=1)

    label_indices = []
    for encode in encodes.split(":"):
      label_indices.append(len(labels))
      labels.append(encode)

    curves.append((name, label_indices))

  if arguments.reference:
    reference_index = len(labels)
    labels.append(arguments.reference)
  else:
    reference_index = 0

  if len(curves) > len(CURVE_COLOURS):
    print("Error: Too many curves in one graph")
    print("If you want to plot this many, please add more colours to CURVE_COLOURS in plot.py")
    sys.exit(1)

  db = sqlite3.connect(arguments.database)

  if sources:
    # Sources are stored in the database as base names without extensions.
    # Allow the user to specify full paths, and automatically extract the part we need
    flattened_sources = flatten_sources(sources)
    sources = [os.path.splitext(os.path.basename(source))[0] for source in flattened_sources]
  else:
    sources = get_shared_source_list(db, labels)
    print("Auto-selected source list:")
    for source in sources:
      print(source)
    print()

  ssimu_points = np.linspace(SSIMU2_LO, SSIMU2_HI, SSIMU2_STEPS)

  num_sources = len(sources)
  num_labels = len(labels)
  # TODO: Get number of resolution points from the database
  # Hard-code for now
  num_resolution_points = 4
  resolution_labels = ["1080p", "720p", "480p", "360p", "Multires"]

  print("Computing curves...")

  mean_log_bpp = np.zeros((num_resolution_points+1, num_labels, SSIMU2_STEPS))
  mean_log_nspp = np.zeros((num_resolution_points+1, num_labels, SSIMU2_STEPS))

  for source in sources:
    for label_index, label in enumerate(labels):
      for (resolution_index, log_bpp, log_nspp) in interpolate_curves(db, label, source, ssimu_points):
        mean_log_bpp[resolution_index, label_index] += log_bpp
        mean_log_nspp[resolution_index, label_index] += log_nspp

  # Taking the arithmetic mean in log space is equivalent to taking the
  # geometric mean of the "true" values
  mean_log_bpp /= num_sources
  mean_log_nspp /= num_sources

  # Once all curves are generated, we no longer need to keep the database open
  db.close()

  representative_log_bpp = np.zeros((num_resolution_points+1, num_labels))
  representative_log_nspp = np.zeros((num_resolution_points+1, num_labels))

  for (resolution_index, resolution_label) in enumerate(resolution_labels):
    # For each label, average the log_bpp and log_nspp values across the target quality range
    # to derive a representative file size and a representative runtime. As above, the arithmetic
    # mean of log-space values is equivalent to the logarithm of the geometric mean.
    #
    # The advantage of this is that the Bjøntegaard delta between two labels simplifies to
    # (the exponential of) the difference between these representative values
    #
    # TODO: Decide whether to use the trapezoidal rule (almost the same, but halves the
    # contribution of the highest and lowest points)
    for label_index, label in enumerate(labels):
      representative_log_bpp[resolution_index, label_index] = np.mean(mean_log_bpp[resolution_index, label_index])
      representative_log_nspp[resolution_index, label_index] = np.mean(mean_log_nspp[resolution_index, label_index])

  # Plot averaged curves
  print("Generating graphs...")

  os.makedirs(arguments.output_dir, exist_ok=True)

  # Single-res graphs first
  for resolution_index in range(num_resolution_points):
    resolution_label = resolution_labels[resolution_index]

    if arguments.title is None:
      size_vs_runtime_title = f"Size vs. runtime, {resolution_label}"
    else:
      size_vs_runtime_title = f"{arguments.title} - size vs. runtime, {resolution_label}"

    size_vs_runtime_filename = os.path.join(arguments.output_dir, f"size_vs_runtime_{resolution_label}.png")

    plot_size_vs_runtime(size_vs_runtime_title, curves, labels, reference_index,
                         representative_log_bpp[resolution_index], representative_log_nspp[resolution_index],
                         size_vs_runtime_filename)

  # Multires graph
  if arguments.title is None:
    size_vs_runtime_title = f"Size vs. runtime, multires"
  else:
    size_vs_runtime_title = f"{arguments.title} - size vs. runtime, multires"

  size_vs_runtime_filename = os.path.join(arguments.output_dir, "size_vs_runtime_multires.png")

  plot_size_vs_runtime(size_vs_runtime_title, curves, labels, reference_index,
                       representative_log_bpp[num_resolution_points], representative_log_nspp[num_resolution_points],
                       size_vs_runtime_filename)

if __name__ == "__main__":
  main(sys.argv)

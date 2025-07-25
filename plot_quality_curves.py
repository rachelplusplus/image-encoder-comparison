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
                      help="Path to database. Defaults to results.sqlite next to this script file")
  parser.add_argument("-s", "--source", action="append", dest="sources", metavar="SOURCE", required=True,
                      help="Source files/lists to compare. If specified multiple times, each file/list is "
                           "plotted separately")
  parser.add_argument("-t", "--title", help="Title to use for the generated graphs", default="")
  parser.add_argument("-o", "--output-dir", help="Output directory, default results/", default="results/")
  parser.add_argument("--range",
                      help=f"Range of SSIMU2 scores to consider, in the format LO-HI. Default {DEFAULT_SSIMU2_LO}-{DEFAULT_SSIMU2_HI}",
                      default=None)
  parser.add_argument("--step", help=f"SSIMU2 step size used for interpolation, default {DEFAULT_SSIMU2_STEP}",
                      type=float, default=DEFAULT_SSIMU2_STEP)
  parser.add_argument("labels", nargs="+", help="Labels to compare", metavar="LABEL")

  arguments = parser.parse_args(argv[1:])

  if len(arguments.labels) > len(CURVE_COLOURS):
    print("Error: Too many labels in one graph", file=sys.stderr)
    print("If you want to plot this many, please add more colours to CURVE_COLOURS in plot.py", file=sys.stderr)
    sys.exit(1)

  if len(arguments.sources) > len(CURVE_STYLES):
    print("Error: Too many source lists in one graph", file=sys.stderr)
    print("If you want to plot this many, please add more colours to CURVE_STYLES in plot.py", file=sys.stderr)
    sys.exit(1)

  # Load any specified source lists, but keep separate sub-lists for each argument passed on the command line
  arguments.sources = [load_source_list(source) for source in arguments.sources]

  arguments.target_ssimu2_points = calculate_target_ssimu2_points(arguments.range, arguments.step)

  return arguments

# Custom function to format the log scale ticks nicely
# Based on https://stackoverflow.com/a/17209836
def format_tick(value, _):
  exp = int(floor(log10(value)))
  base = int(round(value / 10**exp))

  # Skip labelling the 5, 7, and 9 subdivisions to avoid crowding.
  # These skipped subdivisions still get a tick mark on the axis to indicate
  # where they are
  if base in (5, 7, 9): return ""

  if exp >= 1:
    return f"{value:.0f}"
  elif exp == 0:
    # In this case the tick values are single-digit integers,
    # but add a decimal place anyway because 0.6, 0.8, 1.0, 2.0, ... looks prettier
    # than 0.6, 0.8, 1, 2, ...
    return f"{value:.1f}"
  else:
    # For values < 1, display with the minimal number of decimal places
    fmt = f"%.{-exp:d}f"
    return fmt % value

def plot(title, metric_label, ssimu2_points, labels, num_source_lists, log_metric, filename):
  fig, ax = plt.subplots()
  ax.set(xlabel=metric_label, ylabel="SSIMU2")
  ax.set_title(title)

  num_labels = len(labels)
  for source_list_index in range(num_source_lists):
    for label_index, label in enumerate(labels):
      data = np.exp(log_metric[source_list_index, label_index])
      # Distribute curve colours evenly across the rainbow if there are <12 plots
      colour_index = (label_index * len(CURVE_COLOURS)) // num_labels
      # Only add legend entries once, to avoid duplication
      legend_entry = label if source_list_index == 0 else None
      ax.semilogx(data, ssimu2_points, color=CURVE_COLOURS[colour_index], linestyle=CURVE_STYLES[source_list_index], label=legend_entry)

  ax.xaxis.set_minor_locator(ticker.LogLocator(subs=[1, 2, 3, 4, 5, 6, 7, 8, 9]))
  ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_tick))
  ax.xaxis.set_minor_formatter(ticker.FuncFormatter(format_tick))

  ax.tick_params(axis="x", which="major", labelsize="small")
  plt.xticks(minor=False, rotation=45, ha="right", rotation_mode="anchor")
  ax.tick_params(axis="x", which="minor", labelsize="small")
  plt.xticks(minor=True, rotation=45, ha="right", rotation_mode="anchor")

  plt.legend(loc="upper left")

  # Matplotlib uses a fixed default size of 640x480 pixels @ 96dpi.
  # By asking for a higher DPI, we can double this to 1280x960 pixels,
  # which fits modern screens better
  plt.savefig(filename, dpi=192, bbox_inches="tight")

def plot_multires(title, metric_label, ssimu2_points, labels, num_source_lists, log_metric, log_fullres_metric, filename):
  fig, ax = plt.subplots()
  ax.set(xlabel=metric_label, ylabel="SSIMU2")
  ax.set_title(title)

  num_labels = len(labels)
  for source_list_index in range(num_source_lists):
    for label_index, label in enumerate(labels):
      data = np.exp(log_metric[source_list_index, label_index])
      fullres_data = np.exp(log_fullres_metric[source_list_index, label_index])
      # Distribute curve colours evenly across the rainbow if there are <12 plots
      colour_index = (label_index * len(CURVE_COLOURS)) // num_labels
      # Only add legend entries once, to avoid duplication
      legend_entry = label if source_list_index == 0 else None

      ax.semilogx(data, ssimu2_points, color=CURVE_COLOURS[colour_index], linestyle=CURVE_STYLES[source_list_index], label=legend_entry)
      if num_source_lists == 1:
        # If only plotting a single source list, add a comparison to the non-multires results as a dashed line
        ax.semilogx(fullres_data, ssimu2_points, color=CURVE_COLOURS[colour_index], linestyle="--")

  ax.xaxis.set_minor_locator(ticker.LogLocator(subs=[1, 2, 3, 4, 5, 6, 7, 8, 9]))
  ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_tick))
  ax.xaxis.set_minor_formatter(ticker.FuncFormatter(format_tick))

  ax.tick_params(axis="x", which="major", labelsize="small")
  plt.xticks(minor=False, rotation=45, ha="right", rotation_mode="anchor")
  ax.tick_params(axis="x", which="minor", labelsize="small")
  plt.xticks(minor=True, rotation=45, ha="right", rotation_mode="anchor")

  plt.legend(loc="upper left")

  # Matplotlib uses a fixed default size of 640x480 pixels @ 96dpi.
  # By asking for a higher DPI, we can double this to 1280x960 pixels,
  # which fits modern screens better
  plt.savefig(filename, dpi=192, bbox_inches="tight")

def main(argv):
  arguments = parse_args(argv)

  labels = arguments.labels
  target_ssimu2_points = arguments.target_ssimu2_points

  num_source_lists = len(arguments.sources)
  num_labels = len(labels)
  num_ssimu2_points = len(target_ssimu2_points)

  db = sqlite3.connect(arguments.database)

  # TODO: Get number of resolution points from the database
  # Hard-code for now
  num_resolution_points = 4
  resolution_labels = ["1080p", "720p", "480p", "360p", "Multires"]

  print("Computing curves...")

  mean_log_bpp = np.zeros((num_source_lists, num_resolution_points+1, num_labels, num_ssimu2_points))
  mean_log_nspp = np.zeros((num_source_lists, num_resolution_points+1, num_labels, num_ssimu2_points))

  for source_list_index, source_list in enumerate(arguments.sources):
    for source in source_list:
      source_basename = get_source_basename(source)
      for label_index, label in enumerate(labels):
        for (resolution_index, log_bpp, log_nspp) in interpolate_curves(db, label, source_basename, target_ssimu2_points):
          mean_log_bpp[source_list_index, resolution_index, label_index] += log_bpp
          mean_log_nspp[source_list_index, resolution_index, label_index] += log_nspp

    # Taking the arithmetic mean in log space is equivalent to taking the
    # geometric mean of the "true" values
    mean_log_bpp[source_list_index] /= len(source_list)
    mean_log_nspp[source_list_index] /= len(source_list)

  # Once all curves are generated, we no longer need to keep the database open
  db.close()

  # Print all pairwise Bjøntegaard deltas of size and runtime at the same quality
  # TODO: Decide how to handle multiple source lists here
  # TODO: Move to a new script
  if 0:
    print()
    print("Encoder comparisons (left vs. top; entries are delta rate, delta runtime):")
    print()

    longest_label_len = max(len(label) for label in labels)

    representative_log_bpp = np.zeros((num_resolution_points+1, num_labels))
    representative_log_nspp = np.zeros((num_resolution_points+1, num_labels))

    for (resolution_index, resolution_label) in enumerate(resolution_labels):
      print(resolution_label)
      print("=" * len(resolution_label))
      print()

      header = f"{' ' * longest_label_len}"
      divider = f"{'-' * longest_label_len}"
      for label in labels:
        # Allocate enough space for both the label in the header row and
        # table entries in the format "+xxx.x%, +yyyy.y%"
        padded_len = max(len(label), 17)
        header += " | " + center_text(label, padded_len)
        divider += "-+-" + ("-" * padded_len)

      print(header)
      print(divider)

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

      for (comparison_label_index, comparison_label) in enumerate(labels):
        output_line = center_text(comparison_label, longest_label_len)

        for (reference_label_index, reference_label) in enumerate(labels):
          padded_len = max(len(reference_label), 17)

          if comparison_label == reference_label:
            output_line += " | " + (" " * padded_len)
          else:
            rate_ratio = exp(representative_log_bpp[resolution_index, comparison_label_index] -
                             representative_log_bpp[resolution_index, reference_label_index])
            runtime_ratio = exp(representative_log_nspp[resolution_index, comparison_label_index] -
                                representative_log_nspp[resolution_index, reference_label_index])

            bd_rate = (rate_ratio - 1.0) * 100.0
            bd_runtime = (runtime_ratio - 1.0) * 100.0

            output_line += " | " + center_text(f"{bd_rate:+6.1f}%, {bd_runtime:+7.1f}%", padded_len)
        
        print(output_line)

      print()

  # Plot averaged curves
  print("Generating graphs...")

  os.makedirs(arguments.output_dir, exist_ok=True)

  # Single-res graphs first
  for resolution_index in range(num_resolution_points):
    resolution_label = resolution_labels[resolution_index]

    if arguments.title is None:
      size_title = f"File size, {resolution_label}"
      runtime_title = f"Runtime, {resolution_label}"
    else:
      size_title = f"{arguments.title} - file size, {resolution_label}"
      runtime_title = f"{arguments.title} - runtime, {resolution_label}"

    size_filename = os.path.join(arguments.output_dir, f"sizes_{resolution_label}.png")
    runtime_filename = os.path.join(arguments.output_dir, f"runtimes_{resolution_label}.png")

    plot(size_title, "Size (bits/pixel)",
         target_ssimu2_points, labels, num_source_lists, mean_log_bpp[:, resolution_index], size_filename)
    plot(runtime_title, "Runtime (ns/pixel)",
         target_ssimu2_points, labels, num_source_lists, mean_log_nspp[:, resolution_index], runtime_filename)

  # Multires graph
  if arguments.title is None:
    size_title = f"File size, multires"
    runtime_title = f"Runtime, multires"
  else:
    size_title = f"{arguments.title} - file size, multires"
    runtime_title = f"{arguments.title} - runtime, multires"

  size_filename = os.path.join(arguments.output_dir, "sizes_multires.png")
  runtime_filename = os.path.join(arguments.output_dir, "runtimes_multires.png")

  plot_multires(size_title, "Size (effective bits/pixel)",
                target_ssimu2_points, labels, num_source_lists, mean_log_bpp[:, num_resolution_points], mean_log_bpp[:, 0],
                size_filename)
  plot_multires(runtime_title, "Runtime (effective ns/pixel)",
                target_ssimu2_points, labels, num_source_lists, mean_log_nspp[:, num_resolution_points], mean_log_nspp[:, 0],
                runtime_filename)

if __name__ == "__main__":
  main(sys.argv)

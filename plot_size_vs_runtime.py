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
  parser.add_argument("-s", "--source", action="append", dest="sources", metavar="SOURCE",
                      help="Source files/lists to compare. If specified multiple times, each file/list is "
                           "plotted separately")
  parser.add_argument("-t", "--title", help="Title to use for the generated graphs", default="")
  parser.add_argument("-o", "--output-dir", help="Output directory, default results/", default="results/")
  parser.add_argument("-r", "--reference", default=None, required=True,
                      help="Encode set to use as a reference. This does not need to be used in the selected curves.")
  parser.add_argument("--reference-source", default=None,
                      help="Source list to use for the reference point. Defaults to the first --source parameter")
  parser.add_argument("--range",
                      help=f"Range of SSIMU2 scores to consider, in the format LO-HI. Default {DEFAULT_SSIMU2_LO}-{DEFAULT_SSIMU2_HI}",
                      default=None)
  parser.add_argument("--step", help=f"SSIMU2 step size used for interpolation, default {DEFAULT_SSIMU2_STEP}",
                      type=float, default=DEFAULT_SSIMU2_STEP)
  parser.add_argument("curves", nargs="+", help="Curves to plot, format is name:encode1:encode2:...", metavar="CURVE")

  arguments = parser.parse_args(argv[1:])

  if len(arguments.curves) > len(CURVE_COLOURS):
    print("Error: Too many curves in one graph", file=sys.stderr)
    print("If you want to plot this many, please add more colours to CURVE_COLOURS in plot.py", file=sys.stderr)
    sys.exit(1)

  if len(arguments.sources) > len(CURVE_STYLES):
    print("Error: Too many source lists in one graph", file=sys.stderr)
    print("If you want to plot this many, please add more colours to CURVE_STYLES in plot.py", file=sys.stderr)
    sys.exit(1)

  curves = []
  labels = []
  for curve_spec in arguments.curves:
    if ":" not in curve_spec:
      print(f"Error: Bad curve spec {curve_spec}, should be in the format name:encode1:encode2:...", file=sys.stderr)
    name, encodes = curve_spec.split(":", maxsplit=1)

    label_indices = []
    for encode in encodes.split(":"):
      label_indices.append(len(labels))
      labels.append(encode)

    curves.append((name, label_indices))

  arguments.curves = curves

  arguments.labels = labels

  # Sources are stored in the database as base names without extensions.
  # Allow the user to specify full paths, and automatically extract the part we need
  # Load any specified source lists, but keep separate sub-lists for each argument passed on the command line
  arguments.sources = [load_source_list(source) for source in arguments.sources]

  if arguments.reference_source is None:
    arguments.reference_source = arguments.sources[0]
  else:
    arguments.reference_source = load_source_list(arguments.reference_source)

  arguments.target_ssimu2_points = calculate_target_ssimu2_points(arguments.range, arguments.step)

  return arguments

# Custom function to format the log scale ticks nicely
# Based on https://stackoverflow.com/a/17209836
def format_x_tick(value, _):
  exp = int(floor(log10(value)))
  base = int(round(value / 10**exp))

  # Skip labelling the 5, 7, and 9 subdivisions to avoid crowding.
  # These skipped subdivisions still get a tick mark on the axis to indicate
  # where they are
  if base in (5, 7, 9): return ""

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

def plot_size_vs_runtime(title, curves, labels, num_source_lists,
                         representative_log_bpp, representative_log_nspp,
                         reference_log_bpp, reference_log_nspp,
                         filename):
  fig, ax = plt.subplots()
  ax.set(xlabel="Relative runtime", ylabel="BDRATE")
  ax.set_title(title)

  num_curves = len(curves)
  for source_list_index in range(num_source_lists):
    for curve_index, (name, label_indices) in enumerate(curves):
      xs = []
      ys = []

      for label_index in label_indices:
        xs.append(exp(representative_log_nspp[source_list_index, label_index] - reference_log_nspp))
        ys.append((exp(representative_log_bpp[source_list_index, label_index] - reference_log_bpp) - 1.0) * 100.0)

      # Distribute curve colours evenly across the rainbow if there are <12 plots
      colour_index = (curve_index * len(CURVE_COLOURS)) // num_curves
      # Only add legend entries once, to avoid duplication
      legend_entry = name if source_list_index == 0 else None

      ax.semilogx(xs, ys, color=CURVE_COLOURS[colour_index], marker="x", linestyle=CURVE_STYLES[source_list_index], label=legend_entry)

  ax.xaxis.set_minor_locator(ticker.LogLocator(subs=[1, 2, 3, 4, 5, 6, 7, 8, 9]))
  ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_x_tick))
  ax.xaxis.set_minor_formatter(ticker.FuncFormatter(format_x_tick))
  ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_y_tick))
  ax.yaxis.set_minor_formatter(ticker.FuncFormatter(format_y_tick))

  ax.tick_params(axis="x", which="major", labelsize="small")
  plt.xticks(minor=False, rotation=45, ha="right", rotation_mode="anchor")
  ax.tick_params(axis="x", which="minor", labelsize="small")
  plt.xticks(minor=True, rotation=45, ha="right", rotation_mode="anchor")

  # Place the legend in the upper right on this graph, as the curves tend to go from upper-left to bottom-right
  plt.legend(loc="upper right")

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

  reference_mean_log_bpp = np.zeros((num_resolution_points+1, num_ssimu2_points))
  reference_mean_log_nspp = np.zeros((num_resolution_points+1, num_ssimu2_points))

  for source in arguments.reference_source:
    source_basename = get_source_basename(source)
    for (resolution_index, log_bpp, log_nspp) in interpolate_curves(db, arguments.reference, source_basename, target_ssimu2_points):
      reference_mean_log_bpp[resolution_index] += log_bpp
      reference_mean_log_nspp[resolution_index] += log_nspp

  reference_mean_log_bpp/= len(arguments.reference_source)
  reference_mean_log_nspp /= len(arguments.reference_source)

  # Once all curves are generated, we no longer need to keep the database open
  db.close()

  representative_log_bpp = np.mean(mean_log_bpp, axis=3)
  representative_log_nspp = np.mean(mean_log_nspp, axis=3)
  reference_log_bpp = np.mean(reference_mean_log_bpp, axis=1)
  reference_log_nspp = np.mean(reference_mean_log_nspp, axis=1)

  # Plot averaged curves
  print("Generating graphs...")

  os.makedirs(arguments.output_dir, exist_ok=True)

  # Single-res graphs first
  for resolution_index in range(num_resolution_points):
    resolution_label = resolution_labels[resolution_index]

    if arguments.title is None:
      title = f"Size vs. runtime, {resolution_label}"
    else:
      title = f"{arguments.title} - size vs. runtime, {resolution_label}"

    size_vs_runtime_filename = os.path.join(arguments.output_dir, f"size_vs_runtime_{resolution_label}.png")

    plot_size_vs_runtime(title, arguments.curves, labels, num_source_lists,
                         representative_log_bpp[:, resolution_index], representative_log_nspp[:, resolution_index],
                         reference_log_bpp[resolution_index], reference_log_nspp[resolution_index],
                         size_vs_runtime_filename)

  # Multires graph
  if arguments.title is None:
    title = f"Size vs. runtime, multires"
  else:
    title = f"{arguments.title} - size vs. runtime, multires"

  size_vs_runtime_filename = os.path.join(arguments.output_dir, "size_vs_runtime_multires.png")

  plot_size_vs_runtime(title, arguments.curves, labels, num_source_lists,
                       representative_log_bpp[:, num_resolution_points], representative_log_nspp[:, num_resolution_points],
                       reference_log_bpp[num_resolution_points], reference_log_nspp[num_resolution_points],
                       size_vs_runtime_filename)

if __name__ == "__main__":
  main(sys.argv)

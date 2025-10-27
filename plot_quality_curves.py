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
from collections import namedtuple
from math import *
from matplotlib import ticker

from common import *

SCRIPT_DIR = os.path.dirname(__file__)

def parse_args(argv):
  parser = ArgumentParser(prog=argv[0])

  parser.add_argument("-d", "--database", default=os.path.join(SCRIPT_DIR, "results.sqlite"),
                      help="Path to database. Defaults to results.sqlite next to this script file")
  parser.add_argument("-e", "--encoder", action="append", dest="encoder_lists", metavar="ENCODER", required=True,
                      help="Encoder list file(s) to use")
  parser.add_argument("-s", "--source", action="append", dest="source_lists", metavar="SOURCE", required=True,
                      help="Source lists to compare. If specified multiple times, each list is plotted separately")
  parser.add_argument("-t", "--title", help="Title to use for the generated graphs", default="")
  parser.add_argument("-o", "--output-dir", help="Output directory, default results/", default="results/")
  parser.add_argument("--range",
                      help=f"Range of SSIMU2 scores to consider, in the format LO-HI. Default {DEFAULT_SSIMU2_LO}-{DEFAULT_SSIMU2_HI}",
                      default=None)
  parser.add_argument("--step", help=f"SSIMU2 step size used for interpolation, default {DEFAULT_SSIMU2_STEP}",
                      type=float, default=DEFAULT_SSIMU2_STEP)
  parser.add_argument("--multires-plot-1080p-curves", action="store_true",
                      help="Include 1080p-only results as dashed curves on the multires graphs")
  parser.add_argument("curve_specs", nargs="+",
                      help="Curve (sets) to plot. Each argument can be a single ENCODER, or in the format LABEL:ENCODER1:ENCODER2:... "
                           "In the latter case, up to three encoders can be plotted using the same colour but different line styles, "
                           "under a single legend entry (LABEL)",
                      metavar="CURVE")

  arguments = parser.parse_args(argv[1:])

  if len(arguments.curve_specs) > len(CURVE_COLOURS):
    print_error("Too many curves in one graph\n"
                "If you want to plot this many, please add more colours to CURVE_COLOURS in common.py")
    sys.exit(1)

  # Load any specified source lists, but keep separate sub-lists for each argument passed on the command line
  arguments.encoders = flatten(load_encoder_list(encoder_list) for encoder_list in arguments.encoder_lists)
  arguments.sources = flatten(load_source_list(source_list) for source_list in arguments.source_lists)

  arguments.curves = [parse_curve_spec(curve_spec, arguments.encoders) for curve_spec in arguments.curve_specs]

  for curve in arguments.curves:
    if len(curve.encoder_indices) > len(CURVE_STYLES):
      print_error(f"Curve {curve.label} contains too many encoders\n"
                  f"If you want to plot this many, please add more colours to CURVE_STYLES in common.py")
      sys.exit(2)

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

def plot(title, metric_label, ssimu2_points, curves, log_metric, filename):
  fig, ax = plt.subplots()
  ax.set(xlabel=metric_label, ylabel="SSIMU2")
  ax.set_title(title)

  num_curves = len(curves)

  has_legend = False
  for curve_index, curve in enumerate(curves):
    # Distribute curve colours evenly across the rainbow if there are <12 plots
    colour_index = (curve_index * len(CURVE_COLOURS)) // num_curves
    colour = CURVE_COLOURS[colour_index]

    for (index_in_curve, encoder_index) in enumerate(curve.encoder_indices):
      data = np.exp(log_metric[encoder_index, :])

      style = CURVE_STYLES[index_in_curve]

      # Only add legend entries once, to avoid duplication
      if index_in_curve == 0 and curve.label != "":
        legend_entry = curve.label
        has_legend = True
      else:
        legend_entry = None

      ax.semilogx(data, ssimu2_points, color=colour, linestyle=style, label=legend_entry)

  ax.xaxis.set_minor_locator(ticker.LogLocator(subs=[1, 2, 3, 4, 5, 6, 7, 8, 9]))
  ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_tick))
  ax.xaxis.set_minor_formatter(ticker.FuncFormatter(format_tick))

  ax.tick_params(axis="x", which="major", labelsize="small")
  plt.xticks(minor=False, rotation=45, ha="right", rotation_mode="anchor")
  ax.tick_params(axis="x", which="minor", labelsize="small")
  plt.xticks(minor=True, rotation=45, ha="right", rotation_mode="anchor")

  if has_legend:
    # Place legend in the upper left, as curves on this graph go from lower left to top right
    plt.legend(loc="upper left")

  # Matplotlib uses a fixed default size of 640x480 pixels @ 96dpi.
  # By asking for a higher DPI, we can double this to 1280x960 pixels,
  # which fits modern screens better
  plt.savefig(filename, dpi=192, bbox_inches="tight")

def plot_multires(title, metric_label, ssimu2_points, curves, log_metric, log_fullres_metric,
                  plot_1080p_curves, filename):
  fig, ax = plt.subplots()
  ax.set(xlabel=metric_label, ylabel="SSIMU2")
  ax.set_title(title)

  num_curves = len(curves)

  has_legend = False
  for curve_index, curve in enumerate(curves):
    # Distribute curve colours evenly across the rainbow if there are <12 plots
    colour_index = (curve_index * len(CURVE_COLOURS)) // num_curves
    colour = CURVE_COLOURS[colour_index]

    for (index_in_curve, encoder_index) in enumerate(curve.encoder_indices):
      data = np.exp(log_metric[encoder_index, :])

      style = CURVE_STYLES[index_in_curve]

      # Only add legend entries once, to avoid duplication
      if index_in_curve == 0 and curve.label != "":
        legend_entry = curve.label
        has_legend = True
      else:
        legend_entry = None

      ax.semilogx(data, ssimu2_points, color=colour, linestyle=style, label=legend_entry)
      if plot_1080p_curves:
        fullres_data = np.exp(log_fullres_metric[encoder_index, :])
        ax.semilogx(fullres_data, ssimu2_points, color=colour, linestyle="--")

  ax.xaxis.set_minor_locator(ticker.LogLocator(subs=[1, 2, 3, 4, 5, 6, 7, 8, 9]))
  ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_tick))
  ax.xaxis.set_minor_formatter(ticker.FuncFormatter(format_tick))

  ax.tick_params(axis="x", which="major", labelsize="small")
  plt.xticks(minor=False, rotation=45, ha="right", rotation_mode="anchor")
  ax.tick_params(axis="x", which="minor", labelsize="small")
  plt.xticks(minor=True, rotation=45, ha="right", rotation_mode="anchor")

  if has_legend:
    # Place legend in the upper left, as curves on this graph go from lower left to top right
    plt.legend(loc="upper left")

  # Matplotlib uses a fixed default size of 640x480 pixels @ 96dpi.
  # By asking for a higher DPI, we can double this to 1280x960 pixels,
  # which fits modern screens better
  plt.savefig(filename, dpi=192, bbox_inches="tight")

def main(argv):
  arguments = parse_args(argv)

  target_ssimu2_points = arguments.target_ssimu2_points

  num_encoders = len(arguments.encoders)
  num_sources = len(arguments.sources)
  num_ssimu2_points = len(target_ssimu2_points)

  db = sqlite3.connect(arguments.database)

  # TODO: Get number of resolution points from the database
  # Hard-code for now
  num_resolution_points = 4
  resolution_labels = ["1080p", "720p", "480p", "360p", "Multires"]

  # For simplicity of logic, compute curves for all requested encoders.
  # Then we can pull out the requested ones from this array as-needed
  print("Computing curves...")

  mean_log_bpp = np.zeros((num_encoders, num_resolution_points+1, num_ssimu2_points))
  mean_log_nspp = np.zeros((num_encoders, num_resolution_points+1, num_ssimu2_points))

  for encoder_index, encoder in enumerate(arguments.encoders):
    for source in arguments.sources:
      for resolution_index, log_bpp, log_nspp in interpolate_curves(db, encoder, source, target_ssimu2_points):
        mean_log_bpp[encoder_index, resolution_index] += log_bpp
        mean_log_nspp[encoder_index, resolution_index] += log_nspp

  # Taking the arithmetic mean in log space is equivalent to taking the
  # geometric mean of the "true" values
  mean_log_bpp /= num_sources
  mean_log_nspp /= num_sources

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

    representative_log_bpp = np.zeros((num_resolution_points+1, num_encoders))
    representative_log_nspp = np.zeros((num_resolution_points+1, num_encoders))

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
         target_ssimu2_points, arguments.curves, mean_log_bpp[:, resolution_index, :], size_filename)
    plot(runtime_title, "Runtime (ns/pixel)",
         target_ssimu2_points, arguments.curves, mean_log_nspp[:, resolution_index, :], runtime_filename)

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
                target_ssimu2_points, arguments.curves, mean_log_bpp[:, num_resolution_points, :], mean_log_bpp[:, 0, :],
                arguments.multires_plot_1080p_curves, size_filename)
  plot_multires(runtime_title, "Runtime (effective ns/pixel)",
                target_ssimu2_points, arguments.curves, mean_log_nspp[:, num_resolution_points, :], mean_log_nspp[:, 0, :],
                arguments.multires_plot_1080p_curves, runtime_filename)

if __name__ == "__main__":
  main(sys.argv)

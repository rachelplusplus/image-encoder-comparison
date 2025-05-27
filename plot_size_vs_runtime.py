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
from tempfile import TemporaryDirectory
from math import *
from matplotlib import ticker
from scipy.interpolate import pchip_interpolate

THIS_DIR = os.path.dirname(__file__)

# SSIMU2 range and resolution for the interpolated size vs. quality and runtime vs. quality curves
# With LO = 30, HI = 90, STEPS = 61, the SSIMU2 scores we interpolate to are [30, 31, 32, ..., 89, 90]
SSIMU2_LO = 30
SSIMU2_HI = 90
SSIMU2_STEPS = 61

# Kate Morley's 12-bit rainbow: 12 colours of similar saturation and lightness
# Source: https://iamkate.com/data/12-bit-rainbow/
# This list is rotated by one entry, to place the reddest shade first,
# as that's more pleasing to me.
CURVE_COLOURS = ["#a35", "#c66", "#e94", "#ed0", "#9d5", "#4d8",
                 "#2cb", "#0bc", "#09c", "#36b", "#639", "#817"]

EncodeData = namedtuple("EncodeData", ["size", "runtime", "ssimu2", "fullres_ssimu2"])

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

def flatten_sources(source_args):
  flattened_sources = []

  for path in source_args:
    if path.endswith(".y4m"):
      flattened_sources.append(os.path.abspath(path))
    elif path.endswith(".txt"):
      # Treat all entries in this list file as paths relative to the list itself
      list_file_dir = os.path.dirname(path)

      for line in open(path, "r"):
        # Discard comments
        line = line.split("#", maxsplit=1)[0].strip()
        # Skip lines which are blank or entirely comments
        if not line: continue

        if line.endswith(".y4m"):
          flattened_sources.append(os.path.abspath(os.path.join(list_file_dir, line)))
        elif line.endswith(".txt"):
          print("Error: Recursive source lists are not allowed", file=sys.stderr)
          print(f"Source list {path} references {line}", file=sys.stderr)
          sys.exit(2)
        else:
          print(f"Error: Invalid path {line} in source list {path}", file=sys.stderr)
          sys.exit(2)
    else:
      print(f"Error: Invalid path {path}", file=sys.stderr)
      sys.exit(2)

  return flattened_sources

def get_shared_source_list(db, labels):
  shared_sources = None

  for label in labels:
    query = db.execute("SELECT DISTINCT source FROM results WHERE label = :label", {"label": label})

    # Normally the expression `set(query)` below would return a set of one-element tuples.
    # This line flattens the result to a set of source names
    query.row_factory = lambda _, row: row[0]

    this_sources = set(query)

    if shared_sources is None:
      shared_sources = this_sources
    else:
      shared_sources = shared_sources.intersection(this_sources)

  assert shared_sources is not None
  if not shared_sources:
    print(f"Error: No shared sources between all selected labels {labels}", file=sys.stderr)
    sys.exit(1)

  return shared_sources

def interpolate_curves(db, label, source, target_ssimu2_points):
  curves = []

  resolutions = db.execute("SELECT resolution_index, width, height FROM sources WHERE basename = :basename;",
                           {"basename": source}).fetchall()
  resolutions.sort()
  num_resolutions = len(resolutions)

  fullres_width = resolutions[0][1]
  fullres_height = resolutions[0][2]
  fullres_num_pixels = fullres_width * fullres_height

  num_target_ssimu2_points = len(target_ssimu2_points)
  multires_log_bpp = np.full(num_target_ssimu2_points, np.inf)
  multires_log_nspp = np.full(num_target_ssimu2_points, np.inf)

  for (resolution_index, width, height) in resolutions:
    num_pixels = width * height

    query = db.execute("SELECT size, runtime, ssimu2, fullres_ssimu2 FROM results "
                       "WHERE label = :label AND source = :source AND resolution_index = :resolution_index;",
                       {"label": label, "source": source, "resolution_index": resolution_index})

    # Map result rows to a proper object
    query.row_factory = lambda _, row: EncodeData._make(row)
    results = query.fetchall()

    num_points = len(results)
    if num_points == 0:
      print(f"Error: No encodes found under label {label} for {source}", file=sys.stderr)
      sys.exit(1)

    results.sort(key = lambda row: row.ssimu2) # Sort in ascending order of SSIMU2 scores

    # TODO: Filter to keep only points on the convex hull
    min_ssimu2 = results[0].ssimu2
    max_ssimu2 = results[-1].ssimu2
    if min_ssimu2 > SSIMU2_LO or max_ssimu2 < SSIMU2_HI:
      print(f"Error: SSIMU2 scores for (label={label}, source={source} don't cover a wide enough range",
            file=sys.stderr)
      print(f"SSIMU2 range covered is [{min_ssimu2:.1f}, {max_ssimu2:.1f}] vs. expected [{SSIMU2_LO:.1f}, {SSIMU2_HI:.1f}]",
            file=sys.stderr)
      sys.exit(1)

    # Split results and map to log-space for interpolation
    # (which will make it easier to take geometric means later)
    # Also convert from absolute size (in bytes) and runtime (in seconds)
    # to bits/pixel and ns/pixel respectively
    sameres_log_bpp_points = np.zeros(num_points)
    sameres_log_nspp_points = np.zeros(num_points)
    sameres_ssimu2_points = np.zeros(num_points)
    for row_index, row in enumerate(results):
      sameres_log_bpp_points[row_index] = log(row.size * 8.0 / num_pixels)
      sameres_log_nspp_points[row_index] = log(row.runtime * 1000000000.0 / num_pixels)
      sameres_ssimu2_points[row_index] = row.ssimu2

    # Output same-res curve...
    sameres_log_bpp = pchip_interpolate(sameres_ssimu2_points, sameres_log_bpp_points, target_ssimu2_points)
    sameres_log_nspp = pchip_interpolate(sameres_ssimu2_points, sameres_log_nspp_points, target_ssimu2_points)
    curves.append((resolution_index, sameres_log_bpp, sameres_log_nspp))



    # Re-sort for fullres curve generation
    results.sort(key = lambda row: row.fullres_ssimu2)

    fullres_log_bpp_points = np.zeros(num_points)
    fullres_log_nspp_points = np.zeros(num_points)
    fullres_ssimu2_points = np.zeros(num_points)
    for row_index, row in enumerate(results):
      fullres_log_bpp_points[row_index] = log(row.size * 8.0 / fullres_num_pixels)
      fullres_log_nspp_points[row_index] = log(row.runtime * 1000000000.0 / fullres_num_pixels)
      fullres_ssimu2_points[row_index] = row.fullres_ssimu2

    # For the full-res curve (which gets merged into the multires curve), we might not necessarily
    # have enough data to cover the full target SSIMU2 range. This is okay, we just need to filter
    # the curve so that we have appropriate data
    min_fullres_ssimu2 = results[0].fullres_ssimu2
    max_fullres_ssimu2 = results[-1].fullres_ssimu2

    fullres_target_ssimu2_points = []
    fullres_index_map = []
    for index, target_ssimu2 in enumerate(target_ssimu2_points):
      if min_fullres_ssimu2 <= target_ssimu2 <= max_fullres_ssimu2:
        fullres_target_ssimu2_points.append(target_ssimu2)
        fullres_index_map.append(index)

    # ...and merge fullres curve into multires curve
    fullres_log_bpp = pchip_interpolate(fullres_ssimu2_points, fullres_log_bpp_points, fullres_target_ssimu2_points)
    fullres_log_nspp = pchip_interpolate(fullres_ssimu2_points, fullres_log_nspp_points, fullres_target_ssimu2_points)
    for i in range(len(fullres_target_ssimu2_points)):
      if fullres_log_bpp[i] < multires_log_bpp[fullres_index_map[i]]:
        multires_log_bpp[fullres_index_map[i]] = fullres_log_bpp[i]
        multires_log_nspp[fullres_index_map[i]] = fullres_log_nspp[i]

  # Output multires curve
  # First check that we got data for all points. This should always be the case, because the first
  # resolution point should be the full resolution, and therefore should cover the full SSIMU2 range
  # in order to generate that same-res graph properly. So if we didn't get data for all points here,
  # that's a bug in the logic
  assert np.max(multires_log_bpp) < np.inf
  assert np.max(multires_log_nspp) < np.inf
  curves.append((num_resolutions, multires_log_bpp, multires_log_nspp))

  return curves

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

def center_text(text, length):
  assert length >= len(text)
  left_padding = (length - len(text)) // 2
  right_padding = (length - len(text) + 1) // 2
  result = " " * left_padding + text + " " * right_padding
  assert len(result) == length
  return result

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

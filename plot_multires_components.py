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

SCRIPT_DIR = os.path.dirname(__file__)

def parse_args(argv):
  parser = ArgumentParser(prog=argv[0])

  parser.add_argument("-d", "--database", default=os.path.join(SCRIPT_DIR, "results.sqlite"),
                      help="Path to database. Defaults to results.sqlite next to this script file")
  parser.add_argument("-s", "--source-list", required=True, help="Source list to use")
  parser.add_argument("-e", "--encoder-list", help="Encoder list to use.")
  parser.add_argument("-t", "--title", help="Title to use for the generated graphs", default="")
  parser.add_argument("-o", "--output-dir", help="Output directory, default results/", default="results/")
  parser.add_argument("--range",
                      help=f"Range of SSIMU2 scores to consider, in the format LO-HI. Default {DEFAULT_SSIMU2_LO}-{DEFAULT_SSIMU2_HI}",
                      default=None)
  parser.add_argument("--step", help=f"SSIMU2 step size used for interpolation, default {DEFAULT_SSIMU2_STEP}",
                      type=float, default=DEFAULT_SSIMU2_STEP)
  parser.add_argument("encoder_tag", help="Single encoder to plot. This must be one of the entries in the specified encoder list")
  parser.add_argument("source_tag", help="Single source image to plot. This must be one of the entries in the specified source list")

  arguments = parser.parse_args(argv[1:])

  arguments.target_ssimu2_points = calculate_target_ssimu2_points(arguments.range, arguments.step)

  return arguments

# For this script we need to interpolate the curves differently to the other scripts,
# so use a custom interpolation function
#
# Each curve may span a different subset of SSIMU2 scores, so we return those per-curve
# alongside the log(bpp) and log(nspp) data.
#
# To make things more convenient for the rest of the code, the output of this function
# is transposed into three lists of lists:
# * ssimu2_points[resolution_index][data_index]
# * log_bpp[resolution_index][data_index]
# * log_nspp[resolution_index][data_index]
#
# Note that the number of data points may be different per curve.
def interpolate_fullres_curves(db, encoder, source, target_ssimu2_points):
  ssimu2_points = []
  log_bpp = []
  log_nspp = []

  resolutions = db.execute("SELECT resolution_index, width, height FROM sources WHERE source = :source;",
                           {"source": source.tag}).fetchall()
  resolutions.sort()
  num_resolutions = len(resolutions)

  fullres_width = resolutions[0][1]
  fullres_height = resolutions[0][2]
  fullres_num_pixels = fullres_width * fullres_height

  for (resolution_index, width, height) in resolutions:
    num_pixels = width * height

    query = db.execute("SELECT size, real_runtime, user_runtime, sys_runtime, mem_peak, "
                       "ssimu2, butteraugli, fullres_ssimu2, fullres_butteraugli FROM results "
                       "WHERE encoder = :encoder AND source = :source AND resolution_index = :resolution_index;",
                       {"encoder": encoder.tag, "source": source.tag, "resolution_index": resolution_index})

    # Map result rows to a proper object
    query.row_factory = lambda _, row: EncodeData._make(row)
    results = query.fetchall()

    num_points = len(results)
    if num_points == 0:
      print_error(f"No encodes found for encoder {encoder.tag} and source {source.tag}")
      sys.exit(1)

    # Sort results based on fullres score
    results.sort(key = lambda row: row.fullres_ssimu2)

    fullres_log_bpp_points = np.zeros(num_points)
    fullres_log_nspp_points = np.zeros(num_points)
    fullres_ssimu2_points = np.zeros(num_points)
    for row_index, row in enumerate(results):
      fullres_log_bpp_points[row_index] = log(row.size * 8.0 / fullres_num_pixels)
      fullres_log_nspp_points[row_index] = log(row.real_runtime * 1000000000.0 / fullres_num_pixels)
      fullres_ssimu2_points[row_index] = row.fullres_ssimu2

    # We might not necessarily have enough data to cover the full target SSIMU2 range.
    # This is okay, we just need to filter the curve so that we have appropriate data
    min_fullres_ssimu2 = results[0].fullres_ssimu2
    max_fullres_ssimu2 = results[-1].fullres_ssimu2

    fullres_target_ssimu2_points = []
    for index, target_ssimu2 in enumerate(target_ssimu2_points):
      if min_fullres_ssimu2 <= target_ssimu2 <= max_fullres_ssimu2:
        fullres_target_ssimu2_points.append(target_ssimu2)

    # ...and merge fullres curve into multires curve
    fullres_log_bpp = pchip_interpolate(fullres_ssimu2_points, fullres_log_bpp_points, fullres_target_ssimu2_points)
    fullres_log_nspp = pchip_interpolate(fullres_ssimu2_points, fullres_log_nspp_points, fullres_target_ssimu2_points)
    
    ssimu2_points.append(fullres_target_ssimu2_points)
    log_bpp.append(fullres_log_bpp)
    log_nspp.append(fullres_log_nspp)

  return (ssimu2_points, log_bpp, log_nspp)

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

def plot(title, metric_label, resolution_labels, ssimu2_points, log_metric, filename):
  fig, ax = plt.subplots()
  ax.set(xlabel=metric_label, ylabel="SSIMU2")
  ax.set_title(title)

  num_resolution_labels = len(resolution_labels)
  for resolution_index, resolution_label in enumerate(resolution_labels):
    xs = np.exp(log_metric[resolution_index])
    ys = ssimu2_points[resolution_index]
    # Distribute curve colours evenly across the rainbow if there are <12 plots
    colour_index = (resolution_index * len(CURVE_COLOURS)) // num_resolution_labels
    ax.semilogx(xs, ys, color=CURVE_COLOURS[colour_index], linestyle="-",
                label=f"{resolution_label}")

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

  sources = load_source_list(arguments.source_list)

  selected_source = None
  for source in sources:
    if source.tag == arguments.source_tag:
      selected_source = source

  if selected_source is None:
    print_error(f"Requested source {arguments.source} not found")
    sys.exit(2)

  encoders = load_encoder_list(arguments.encoder_list)

  selected_encoder = None
  for encoder in encoders:
    if encoder.tag == arguments.encoder_tag:
      selected_encoder = encoder

  if selected_encoder is None:
    print_error(f"Requested encoder {arguments.encoder} not found")
    sys.exit(2)

  target_ssimu2_points = arguments.target_ssimu2_points

  num_ssimu2_points = len(target_ssimu2_points)

  db = sqlite3.connect(arguments.database)

  # TODO: Get number of resolution points from the database
  # Hard-code for now
  num_resolution_points = 4
  resolution_labels = ["1080p", "720p", "480p", "360p"]

  print("Computing curves...")
  (ssimu2_points, log_bpp, log_nspp) = interpolate_fullres_curves(db, selected_encoder, selected_source, target_ssimu2_points)

  print("Generating graphs...")

  os.makedirs(arguments.output_dir, exist_ok=True)

  if arguments.title is None:
    size_title = f"File size"
    runtime_title = f"Runtime"
  else:
    size_title = f"{arguments.title} - file size by resolution"
    runtime_title = f"{arguments.title} - runtime by resolution"

  size_filename = os.path.join(arguments.output_dir, f"sizes.png")
  runtime_filename = os.path.join(arguments.output_dir, f"runtimes.png")

  plot(size_title, "Size (effective bits/pixel)", resolution_labels, ssimu2_points, log_bpp, size_filename)
  plot(runtime_title, "Runtime (effective ns/pixel)", resolution_labels, ssimu2_points, log_nspp, runtime_filename)

if __name__ == "__main__":
  main(sys.argv)

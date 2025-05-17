#!/usr/bin/env python3
# Script to analyze and plot encoder results
#
# Copyright (c) 2025, Monocot Limited. All rights reserved
#
# This source code is subject to the terms of the BSD 2 Clause License. If the BSD 2 Clause License
# was not distributed with this source code in the LICENSE file, you can obtain it at
# https://opensource.org/license/bsd-2-clause
#
# TODO:
# * Scale file size and runtime by image dimensions, ie. plot bpp and ns/pixel
#   instead of raw data values
# * Support multi-res encoding, where we compress multiple times at different sizes
#   and pick whichever one gives the smallest file size at each quality point
# * Also support plotting multi-res vs. single-res encodes to show how that works

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

CURVE_COLOURS = ["black", "red", "blue"]

def run(cmd, **kwargs):
  return subprocess.run(cmd, check=True, **kwargs)

def parse_args(argv):
  parser = ArgumentParser(prog=argv[0])

  parser.add_argument("-d", "--database", default=os.path.join(THIS_DIR, "results.sqlite"),
                      help="Path to database. Defaults to results.sqlite next to avif-comparison scripts")
  parser.add_argument("-s", "--source", action="append", dest="sources", metavar="SOURCE",
                      help="Source file(s) to compare. May be specified multiple times. "
                           "Defaults to all files which were encoded in all of the selected labels")
  parser.add_argument("labels", nargs="+", help="Labels to compare", metavar="LABEL")

  return parser.parse_args(argv[1:])

def get_shared_source_list(db, labels):
  shared_sources = None

  for label in labels:
    query = db.execute("SELECT DISTINCT source FROM results WHERE label = :label", {"label": label})
    this_sources = set(row[0] for row in query)

    if shared_sources is None:
      shared_sources = this_sources
    else:
      shared_sources = shared_sources.intersection(this_sources)

  assert shared_sources is not None
  if not shared_sources:
    print(f"Error: No shared sources between all selected labels {labels}", file=sys.stderr)
    sys.exit(1)

  return shared_sources

def interpolate_curve(db, label, source, target_ssimu_points):
  # TODO:
  # * Gather data points for this (label, source) combination
  # * Check that scores cover a suitable range
  # * Interpolate size vs. quality and runtime vs. quality curves
  #   for this specific source
  query = db.execute("SELECT size, runtime, ssimu2 FROM results WHERE label = :label AND source = :source",
                     {"label": label, "source": source})
  results = query.fetchall()
  results.sort(key = lambda row: row[2]) # Sort in ascending order of SSIMU2 scores

  # TODO: Remove duplicate scores if needed
  min_ssimu2 = results[0][2]
  max_ssimu2 = results[-1][2]
  if min_ssimu2 > SSIMU2_LO or max_ssimu2 < SSIMU2_HI:
    print(f"Error: SSIMU2 scores for (label={label}, source={source} don't cover a wide enough range",
          file=sys.stderr)
    print(f"SSIMU2 range covered is [{min_ssimu2:.1f}, {max_ssimu2:.1f}] vs. expected [{SSIMU2_LO:.1f}, {SSIMU2_HI:.1f}]",
          file=sys.stderr)
    sys.exit(1)

  # Split results and map to log-space for interpolation
  # (which will make it easier to take geometric means later)
  log_size_points = [log(row[0]) for row in results]
  log_runtime_points = [log(row[1]) for row in results]
  ssimu2_points = [row[2] for row in results]

  log_sizes = pchip_interpolate(ssimu2_points, log_size_points, target_ssimu_points)
  log_runtimes = pchip_interpolate(ssimu2_points, log_runtime_points, target_ssimu_points)

  return (log_sizes, log_runtimes)

# Custom function to format the log scale ticks nicely
# Based on https://stackoverflow.com/a/17209836
def format_tick(value, _):
  exp = floor(log10(value))
  base = int(round(value / 10**exp))

  # Skip labelling the 7 and 9 subdivisions to avoid crowding.
  # These skipped subdivisions still get a tick mark on the axis to indicate
  # where they are
  if base in (7, 9): return ""

  if exp >= 0:
    # For values >= 1, display with 1 decimal point
    return "%.1f" % int(round(value))
  else:
    # For values < 1, display with the minimal number of decimal places
    fmt = f"%.{-exp:d}f"
    return fmt % value

def plot(title, metric_label, ssimu_points, labels, log_metric, filename):
  fig, ax = plt.subplots()
  ax.set(xlabel=metric_label, ylabel="SSIMU2")
  ax.set_title(title)

  for i in range(len(labels)):
    label = labels[i]
    data = np.exp(log_metric[label])
    ax.semilogx(data, ssimu_points, color=CURVE_COLOURS[i], linestyle="-", label=label)

  ax.xaxis.set_minor_locator(ticker.LogLocator(subs=[1, 2, 3, 4, 5, 6, 7, 8, 9]))
  ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_tick))
  ax.xaxis.set_minor_formatter(ticker.FuncFormatter(format_tick))

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
  print(arguments)
  sources = arguments.sources
  labels = arguments.labels

  db = sqlite3.connect(arguments.database)

  if not sources:
    sources = get_shared_source_list(db, labels)
    print("Auto-selected source list:")
    for source in sources:
      print(source)
    print()

  ssimu_points = np.linspace(SSIMU2_LO, SSIMU2_HI, SSIMU2_STEPS)

  mean_log_sizes = {}
  mean_log_runtimes = {}

  print("Computing curves...")
  for label in labels:
    sum_log_sizes = np.zeros(SSIMU2_STEPS)
    sum_log_runtimes = np.zeros(SSIMU2_STEPS)

    for source in sources:
      (log_sizes, log_runtimes) = interpolate_curve(db, label, source, ssimu_points)
      sum_log_sizes += log_sizes
      sum_log_runtimes += log_runtimes

    # Taking the arithmetic mean in log space is equivalent to taking the
    # geometric mean of the "true" values
    mean_log_sizes[label] = sum_log_sizes / len(sources)
    mean_log_runtimes[label] = sum_log_runtimes / len(sources)

  # Print all pairwise BDRATE comparisons
  print()
  print("Pairwise comparisons:")
  for i in range(1, len(labels)):
    for j in range(i):
      reference_label = labels[i]
      comparison_label = labels[j]

      delta_log_sizes = mean_log_sizes[comparison_label] - mean_log_sizes[reference_label]
      delta_log_runtimes = mean_log_runtimes[comparison_label] - mean_log_runtimes[reference_label]

      # Compute the average of these deltas. Again, taking the arithmetic mean in log space
      # is equivalent to taking the geometric mean of the size or runtime ratios, which is
      # how BDRATE is defined
      #
      # TODO: Decide whether to use the trapezoidal rule (almost the same, but halves the
      # contribution of the highest and lowest points)
      rate_ratio = exp(np.mean(delta_log_sizes))
      runtime_ratio = exp(np.mean(delta_log_runtimes))

      bd_rate = (rate_ratio - 1.0) * 100.0
      bd_runtime = (runtime_ratio - 1.0) * 100.0

      print(f"{comparison_label} vs. {reference_label}: BD-RATE = {bd_rate:+5.1f}%, BD-runtime = {bd_runtime:+5.1f}%")

  # Plot averaged curves
  print()
  print("Generating graphs...")
  plot("File size comparison", "Size (bytes)", ssimu_points, labels, mean_log_sizes, "sizes.png")
  plot("Runtime comparison", "Runtime (s)", ssimu_points, labels, mean_log_runtimes, "runtimes.png")

  db.close()

if __name__ == "__main__":
  main(sys.argv)


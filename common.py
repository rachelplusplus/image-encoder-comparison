# Common functions shared between the scripts in this directory
#
# Copyright (c) 2025, Monocot Limited. All rights reserved
#
# This source code is subject to the terms of the BSD 2 Clause License. If the BSD 2 Clause License
# was not distributed with this source code in the LICENSE file, you can obtain it at
# https://opensource.org/license/bsd-2-clause

import numpy as np
import os
import sys

from collections import namedtuple
from math import *
from scipy.interpolate import pchip_interpolate

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

def center_text(text, length):
  assert length >= len(text)
  left_padding = (length - len(text)) // 2
  right_padding = (length - len(text) + 1) // 2
  result = " " * left_padding + text + " " * right_padding
  assert len(result) == length
  return result

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

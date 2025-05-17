#!/usr/bin/env python3
# Script to run various encodes and record the results to a database
#
# Copyright (c) 2025, Monocot Limited. All rights reserved
#
# This source code is subject to the terms of the BSD 2 Clause License. If the BSD 2 Clause License
# was not distributed with this source code in the LICENSE file, you can obtain it at
# https://opensource.org/license/bsd-2-clause

# Database design:
#
# * Encoder table: Stores {label, date, encoder, build flats, runtime flags}, so that we can recover
#   the settings used for any particular encode.
#   A date stamp is included to allow for deleting old encodes.
#   This is left out for now - TODO add this
#
# * Result table: {label, input, res, quality, size, runtime, same-res SSIMU2, full-res SSIMU2}
#   We'll likely query various combinations of the first four columns here
#
# We don't store aggregated results (things like quality vs. size curves) in the database.
# This removes the potential for gnarly data synchronization issues, and they aren't particularly
# expensive to recompute as-needed, especially compared to the encodes themselves.
#
# TODO:
# * Support encoding multiple sources at once
# * Support encoding multiple resolutions at once
# * Find a better way to measure child process runtime
# * Run encodes in parallel

import os
import resource
import sqlite3
import subprocess
import sys

from argparse import ArgumentParser
from tempfile import TemporaryDirectory

THIS_DIR = os.path.dirname(__file__)
TINYAVIF_DIR = os.path.join(THIS_DIR, "..", "tinyavif")
TINYAVIF = os.path.join(TINYAVIF_DIR, "target", "release", "tinyavif")

QUALITIES = {
  # Note: tinyavif takes a qindex value, not a quality.
  # This goes in the opposite direction to quality. So to compensate, and bring
  # it in line with the other encoders, quality = 255 - qindex
  "tinyavif": [90, 100, 110, 120, 135, 150, 165, 190, 215, 240, 247],
  "libaom": [98, 93, 88, 81, 74, 65, 56, 49, 42, 37, 32],
  "jpegli": [100, 95, 85, 75, 65, 55, 45, 35, 25, 15, 10],
}

ENCODERS = list(QUALITIES.keys())

def run(cmd, **kwargs):
  return subprocess.run(cmd, check=True, **kwargs)

def parse_args(argv):
  parser = ArgumentParser(prog=argv[0])

  parser.add_argument("-d", "--database", default=os.path.join(THIS_DIR, "results.sqlite"),
                      help="Path to database. Defaults to results.sqlite next to avif-comparison scripts")
  parser.add_argument("label", help="Label for this encode set")
  parser.add_argument("encoder", choices=ENCODERS, help="Which encoder to use")
  parser.add_argument("source", help="Source file (must be in Y4M format)")

  return parser.parse_args(argv[1:])

def prepare_database(db):
  with db:
    db.execute("CREATE TABLE IF NOT EXISTS \
               results(label TEXT, source TEXT, quality INT, size INT, runtime REAL, ssimu2 REAL)")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS results_index ON results(label, source, quality)")

# Fetch a list of which qualities have already been done for the given label and input file
def get_qualities_done(db, label, source_basename):
  query = db.execute("SELECT quality FROM results WHERE label = :label AND source = :source",
                     {"label": label, "source": source_basename})

  return [row[0] for row in query]

def setup_encoder(encoder):
  if encoder == "tinyavif":
    print("Building tinyavif...")
    run(["cargo", "build", "--release", "--quiet"], cwd=TINYAVIF_DIR)

def run_encode(encoder, source_path, source_png_path, quality, tmpdir):
  # TODO: Keep output files in memory only

  # Record child process runtime
  t0 = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime

  if encoder == "tinyavif":
    compressed_path = os.path.join(tmpdir.name, f"out_q{quality}.avif")
    run([TINYAVIF, source_path, "--qindex", str(255 - quality), "-o", compressed_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  elif encoder == "libaom":
    compressed_path = os.path.join(tmpdir.name, f"out_q{quality}.avif")
    run(["avifenc", source_path, "-o", compressed_path, "-c", "aom", "-q", str(quality)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  elif encoder == "jpegli":
    # Note: jpegli can't currently parse Y4M format inputs, so pass it the source PNG instead
    # This PNG has been upsampled to 4:4:4, so technically jpegli is trying to compress twice
    # as much input data.
    # In theory we could tell jpegli to subsample back down to 4:2:0, but (until we can
    # feed 4:2:0 input into ssimulacra2_rs) this causes an additional conversion round-trip
    # of 4:4:4 rgb -> 4:2:0 yuv -> 4:4:4 rgb, which hurts quality more. So not subsampling
    # is fairer to jpegli for now.
    # It would be better if we can figure out how to pass the original 4:2:0 content in though.
    compressed_path = os.path.join(tmpdir.name, f"out_q{quality}.jpeg")
    run(["cjpegli", source_png_path, compressed_path, "-q", str(quality)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  else:
    raise NotImplemented

  t1 = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime

  size = os.stat(compressed_path).st_size
  runtime = t1 - t0

  # Convert output to a PNG so that ssimulacra2_rs can process it
  # TODO: Install the lsmash plugin for vapoursynth from the AUR, so I can use the
  # video comparison feature to directly compare y4m files
  compressed_png_path = os.path.join(tmpdir.name, f"out_q{quality}.png")
  run(["ffmpeg", "-i", compressed_path,
       "-loglevel", "error", # Suppress log spam
       "-update", "1", # Suppress warning about output filename not containing a frame number
       compressed_png_path])

  # Compute SSIMULACRA2 score
  # We expect the output from ssimulacra2_rs to be a single line containing "Score: ..."
  ssimu2_proc = run(["ssimulacra2_rs", "image", source_png_path, compressed_png_path], capture_output=True)
  line = ssimu2_proc.stdout.strip()
  if (b"\n" in line) or (not line.startswith(b"Score: ")):
    print("Error: Unexpected output from ssimulacra2_rs:", file=sys.stderr)
    print(line, file=sys.stderr)
    sys.exit(1)

  ssimu2 = float(line[7:])

  return (size, runtime, ssimu2)

def main(argv):
  arguments = parse_args(argv)
  label = arguments.label
  encoder = arguments.encoder
  source_path = arguments.source
  source_basename = os.path.basename(source_path)

  db = sqlite3.connect(arguments.database)

  prepare_database(db)

  # Check which encodes have already been done
  qualities_done = get_qualities_done(db, label, source_basename)
  if qualities_done != []:
    print(f"Already done qualities {', '.join(map(str, qualities_done))}")

  # Only set up the encoding environment if we really need to
  encoder_setup = False
  tmpdir = None
  source_png_path = None

  for quality in QUALITIES[encoder]:
    if quality not in qualities_done:
      # Prepare encoder environment if needed
      if not encoder_setup:
        setup_encoder(encoder)

        tmpdir = TemporaryDirectory()

        source_png_path = os.path.join(tmpdir.name, os.path.splitext(source_basename)[0] + ".png")
        run(["ffmpeg", "-i", source_path,
             "-loglevel", "error", # Suppress log spam
             "-update", "1", # Suppress warning about output filename not containing a frame number
             source_png_path])

        encoder_setup = True

      # Run encode and record results
      print(f"Encoding {source_basename} with {encoder} at quality {quality}...")
      (size, runtime, ssimu2) = run_encode(encoder, source_path, source_png_path, quality, tmpdir)
      with db:
        db.execute("INSERT INTO results VALUES (:label, :source, :quality, :size, :runtime, :ssimu2)",
                   {"label": label, "source": source_basename, "quality": quality,
                    "size": size, "runtime": runtime, "ssimu2": ssimu2})

  # If we get here without setting up the encoder, there was nothing to do
  # Print a helpful message so the user knows why we exited immediately
  if not encoder_setup:
    print("Nothing to do")

  db.close()

if __name__ == "__main__":
  main(sys.argv)

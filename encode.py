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

import multiprocessing
import os
import sqlite3
import subprocess
import sys
import time

from argparse import ArgumentParser
from collections import namedtuple
from math import *
from collections import namedtuple
from tempfile import TemporaryDirectory

from common import *

THIS_DIR = os.path.dirname(__file__)
TINYAVIF_DIR = os.path.join(THIS_DIR, "..", "tinyavif")
TINYAVIF = os.path.join(TINYAVIF_DIR, "target", "release", "tinyavif")

QUALITIES = {
  # Note: tinyavif takes a qindex value, not a quality.
  # This goes in the opposite direction to quality. So to compensate, and bring
  # it in line with the other encoders, quality = 255 - qindex
  #
  # Note also that tinyavif quality=255 (qindex=0) and aom/svt quality=100 are lossless,
  # while jpegli quality=100 is not. Lossless mode in AV1 is different in some key ways
  # to lossy mode, and tinyavif doesn't support it anyway. So we avoid the lossless
  # qualities and stick to the highest lossy quality for each encoder.
  "aom": [99, 95, 85, 75, 65, 55, 45, 35, 25, 15, 5],
  "svt": [99, 95, 85, 75, 65, 55, 45, 35, 25, 15, 5, 0],
  "rav1e": [99, 95, 85, 75, 65, 55, 45, 35, 25, 15],
  "tinyavif": [254, 240, 215, 190, 165, 140, 115, 90, 65],
  "jpegxl": [99, 95, 85, 75, 65, 55, 45, 35, 25, 15, 5, 0],
  "jpegli": [100, 95, 85, 75, 65, 55, 45, 35, 25, 15, 5],
  "webp": [100, 95, 85, 75, 65, 55, 45, 35, 25, 15, 5],
}

# Sizes to scale to along the longest axis
# The shortest axis length is then determined by the source's aspect ratio
# If the aspect ratio is 16:9, these are 2160p, 1440p, 1080p, 720p, 480p, 360p
MULTIRES_SIZES = [3840, 2560, 1920, 1280, 853, 640]

Encode = namedtuple("Encode", ["resolution_index", "quality"])
Image = namedtuple("Image", ["basename", "y4m_path", "png_path", "width", "height"])
Job = namedtuple("Job", ["encoder", "fullres_source", "scaled_source", "resolution_index", "quality"])

def run(cmd, **kwargs):
  return subprocess.run(cmd, check=True, **kwargs)

def parse_args(argv):
  parser = ArgumentParser(prog=argv[0])

  parser.add_argument("-d", "--database", default=os.path.join(THIS_DIR, "results.sqlite"),
                      help="Path to database. Defaults to results.sqlite next to this script file")
  parser.add_argument("-j", "--jobs", type=int, default=None,
                      help="Number of encode jobs to run in parallel. Default to #CPUs")
  parser.add_argument("-e", "--encoder-list", dest="encoder_lists", action="append", required=True,
                      help=f"Encoder list file(s), in TOML format")
  parser.add_argument("-s", "--source-list", dest="source_lists", action="append", required=True,
                      help="Source list file(s), in TOML format")

  return parser.parse_args(argv[1:])

def prepare_database(db):
  db.execute("CREATE TABLE IF NOT EXISTS "
             "sources(source TEXT, resolution_index INT, width INT, height INT)")
  db.execute("CREATE UNIQUE INDEX IF NOT EXISTS sources_index "
             "ON sources(source, resolution_index)")
  db.execute("CREATE TABLE IF NOT EXISTS "
             "results(encoder TEXT, source TEXT, resolution_index INT, quality INT, "
                     "size INT, runtime REAL, ssimu2 REAL, fullres_ssimu2 REAL)")
  db.execute("CREATE UNIQUE INDEX IF NOT EXISTS results_index "
             "ON results(encoder, source, resolution_index, quality)")
  db.commit()

# Calculate all of the downsampled sizes for a given source, and insert them into
# the source table. Returns a list of (index, width, height) tuples, with the full-res source
# being the first entry
def prepare_source(db, source):
  query = db.execute("SELECT resolution_index, width, height FROM sources WHERE source = :source "
                     "ORDER BY resolution_index",
                     {"source": source.tag})
  results = query.fetchall()
  if len(results) > 0:
    # Values have already been computed, so just return those
    return results

  fullres_width, fullres_height = get_image_size(source.path)
  longest_length = max(fullres_width, fullres_height)

  sizes = [(0, fullres_width, fullres_height)]
 
  resolution_index = 1
  for size in MULTIRES_SIZES:
    if size >= 0.8 * longest_length:
      # Don't scale to sizes which are too close to the original, or larger
      # Not scaling to sizes near the original is useful for 4K inputs, because
      # sometimes 4K means 3840x2160 and sometimes it means 4096x2304, and there's
      # no point scaling a source between these two sizes.
      continue

    scale_factor = size / longest_length
    scaled_width = int(round(fullres_width * scale_factor))
    scaled_height = int(round(fullres_height * scale_factor))

    sizes.append((resolution_index, scaled_width, scaled_height))
    resolution_index += 1

  for (resolution_index, width, height) in sizes:
    db.execute("INSERT INTO sources VALUES (:source, :index, :width, :height)",
               {"source": source.tag, "index": resolution_index,
                "width": width, "height": height})

  # Commit all resolutions to the database at once
  # This makes sure that, if the above logic is interrupted for any reason, we won't
  # end up with a broken setup where this source is considered prepared but doesn't
  # have the full set of intended resolutions.
  db.commit()

  return sizes

def prepare_source_images(source, sizes, tmpdir):
  fullres_width, fullres_height = get_image_size(source.path)
  fullres_png_path = os.path.join(tmpdir, f"{source.tag}.png")

  run(["ffmpeg", "-i", source.path,
       "-loglevel", "error", # Suppress log spam
       "-update", "1", # Suppress warning about output filename not containing a frame number
       fullres_png_path])

  images = [Image(source.tag, source.path, fullres_png_path, fullres_width, fullres_height)]

  for (resolution_index, width, height) in sizes[1:]:
    print(f"Scaling {source.tag} from {fullres_width}x{fullres_height} to {width}x{height}")
    assert width < fullres_width and height < fullres_height

    scaled_basename = f"{source.tag}_{width}x{height}"
    scaled_y4m_path = os.path.join(tmpdir, f"{scaled_basename}.y4m")
    scaled_png_path = os.path.join(tmpdir, f"{scaled_basename}.png")

    run(["ffmpeg", "-i", source.path,
         "-vf", f"scale={width}:{height}:lanczos",
         "-loglevel", "error", # Suppress log spam
         "-strict", "-1", # Prevent error when scaling 10-bit files
         scaled_y4m_path])
    run(["ffmpeg", "-i", scaled_y4m_path,
         "-loglevel", "error", # Suppress log spam
         "-update", "1", # Suppress warning about output filename not containing a frame number
         scaled_png_path])

    images.append(Image(scaled_basename, scaled_y4m_path, scaled_png_path, width, height))

  return images

def get_image_size(path):
  width=None
  height=None
  ffprobe_result = run(["ffprobe", "-hide_banner", "-show_streams", path],
                       capture_output=True)
  for line in ffprobe_result.stdout.split(b"\n"):
    if line.startswith(b"width="):
      width = int(line[6:])
    elif line.startswith(b"height="):
      height = int(line[7:])

  assert width is not None and height is not None
  return (width, height)

# Function to handle a single encode (one encoder, one resolution, one quality value).
# This function is run in parallel when the `--jobs` argument is greater than 1
def run_encode(encoder, tmpdir, fullres_source, scaled_source, quality):
  # Build command line
  if encoder.encoder == "tinyavif":
    compressed_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}.avif")
    cmd = [TINYAVIF,
           scaled_source.y4m_path, "-o", compressed_path,
           "--qindex", str(255 - quality)
          ]
  elif encoder.encoder == "aom":
    compressed_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}.avif")
    cmd = ["avifenc",
           scaled_source.y4m_path, "-o", compressed_path,
           "-c", "aom", "-s", str(encoder.settings["speed"]),
           "-j", "1",
           "-q", str(quality)
          ]
    if encoder.settings["tune"] is not None:
      cmd += ["-a", f"tune={encoder.settings["tune"]}"]
  elif encoder.encoder == "svt":
    compressed_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}.avif")
    cmd = ["avifenc",
           scaled_source.y4m_path, "-o", compressed_path,
           "-c", "svt", "-s", str(encoder.settings["speed"]),
           "-j", "1",
           "-q", str(quality)
          ]
    if encoder.settings["tune"] is not None:
      cmd += ["-a", f"tune={encoder.settings["tune"]}"]
  elif encoder.encoder == "rav1e":
    compressed_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}.avif")
    cmd = ["avifenc",
           scaled_source.y4m_path, "-o", compressed_path,
           "-c", "rav1e", "-s", str(encoder.settings["speed"]),
           "-j", "1",
           "-q", str(quality)
          ]
  elif encoder.encoder == "jpegli":
    # Note: jpegli can't currently parse Y4M format inputs, so pass it the source PNG instead
    # This PNG has been upsampled to 4:4:4, so technically jpegli is trying to compress twice
    # as much input data.
    # In theory we could tell jpegli to subsample back down to 4:2:0, but (until we can
    # feed 4:2:0 input into ssimulacra2_rs) this causes an additional conversion round-trip
    # of 4:4:4 rgb -> 4:2:0 yuv -> 4:4:4 rgb, which hurts quality more. So not subsampling
    # is fairer to jpegli for now.
    # It would be better if we can figure out how to pass the original 4:2:0 content in though.
    compressed_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}.jpeg")
    cmd = ["cjpegli",
           scaled_source.png_path, compressed_path,
           "-q", str(quality)
          ]
  elif encoder.encoder == "jpegxl":
    compressed_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}.jxl")
    cmd = ["cjxl", "-e", str(encoder.settings["speed"]),
           scaled_source.png_path, compressed_path,
           "--num_threads", "1",
           "-q", str(quality)
          ]
  elif encoder.encoder == "webp":
    # Similar to jpegli, webp can currently only accept 4:4:4 inputs
    compressed_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}.webp")
    cmd = ["cwebp", "-m", str(encoder.settings["speed"]),
           scaled_source.png_path, "-o", compressed_path,
           "-q", str(quality)
          ]
  else:
    raise NotImplemented

  # Do the encode and gather stats
  t0 = time.monotonic()
  run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  t1 = time.monotonic()

  size = os.stat(compressed_path).st_size
  runtime = t1 - t0

  # Convert output to a PNG so that ssimulacra2_rs can process it
  # TODO: Install the lsmash plugin for vapoursynth from the AUR, so I can use the
  # video comparison feature to directly compare y4m files
  compressed_png_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}.png")
  run(["ffmpeg", "-i", compressed_path,
       "-loglevel", "error", # Suppress log spam
       "-update", "1", # Suppress warning about output filename not containing a frame number
       "-threads", "1",
       compressed_png_path])

  # Compute same-res SSIMULACRA2 score
  # We expect the output from ssimulacra2_rs to be a single line containing "Score: ..."
  sameres_ssimu2_proc = run(["ssimulacra2_rs", "image", scaled_source.png_path, compressed_png_path], capture_output=True)
  line = sameres_ssimu2_proc.stdout.strip()
  if (b"\n" in line) or (not line.startswith(b"Score: ")):
    print_error(f"Unexpected output from ssimulacra2_rs: {line}")
    sys.exit(1)

  sameres_ssimu2 = float(line[7:])

  if scaled_source is fullres_source:
    # No need to compute SSIMU2 score twice
    fullres_ssimu2 = sameres_ssimu2
  else:
    # Compute full-res SSIMU2 score
    upscaled_png_path = os.path.join(tmpdir, encoder.tag, f"{scaled_source.basename}_q{quality}_upscaled.png")

    run(["ffmpeg", "-i", compressed_path,
         "-vf", f"scale={fullres_source.width}:{fullres_source.height}:lanczos",
         "-loglevel", "error", # Suppress log spam
         "-threads", "1",
         upscaled_png_path])

    fullres_ssimu2_proc = run(["ssimulacra2_rs", "image", fullres_source.png_path, upscaled_png_path], capture_output=True)
    line = fullres_ssimu2_proc.stdout.strip()
    if (b"\n" in line) or (not line.startswith(b"Score: ")):
      print_error(f"Unexpected output from ssimulacra2_rs: {line}")
      sys.exit(1)

    fullres_ssimu2 = float(line[7:])

    # Clean up
    os.remove(upscaled_png_path)

  # Clean up after ourselves
  os.remove(compressed_png_path)
  os.remove(compressed_path)

  return (size, runtime, sameres_ssimu2, fullres_ssimu2)

def worker_main(db, tmpdir, total_jobs, queue):
  total_jobs_digits = floor(log10(total_jobs)) + 1
  status_format = f"[%{total_jobs_digits}d/%{total_jobs_digits}d] %s: Encoding %s at size %4dx%4d, quality %3d"

  while 1:
    job_number, job = queue.get()

    try:
      print(status_format % (job_number + 1, total_jobs,
                             job.encoder.tag, job.fullres_source.basename,
                             job.scaled_source.width, job.scaled_source.height, job.quality))

      size, runtime, sameres_ssimu2, fullres_ssimu2 = \
        run_encode(job.encoder, tmpdir, job.fullres_source, job.scaled_source, job.quality)

      # TODO: Plumb the source tag through more explicitly. For now, we rely on this being true:
      source_tag = job.fullres_source.basename

      db.execute("INSERT INTO results VALUES (:encoder, :source, :resolution_index, :quality, "
                                             ":size, :runtime, :ssimu2, :fullres_ssimu2)",
                 {"encoder": job.encoder.tag, "source": source_tag,
                  "resolution_index": job.resolution_index, "quality": job.quality,
                  "size": size, "runtime": runtime,
                  "ssimu2": sameres_ssimu2, "fullres_ssimu2": fullres_ssimu2})
      db.commit()

    finally:
      # Always mark tasks as done, even if they fail, so that the main process
      # doesn't get blocked waiting on us
      queue.task_done()

def main(argv):
  arguments = parse_args(argv)
  
  encoders = flatten(load_encoder_list(encoder) for encoder in arguments.encoder_lists)
  sources = flatten(load_source_list(source) for source in arguments.source_lists)

  db = sqlite3.connect(arguments.database)

  prepare_database(db)

  tmpdir = TemporaryDirectory()

  jobs = []

  for encoder in encoders:
    for source in sources:
      sizes = prepare_source(db, source)

      # Check which encodes have already been done for this source
      query = db.execute("SELECT resolution_index, quality FROM results "
                         "WHERE encoder = :encoder AND source = :source",
                         {"encoder": encoder.tag, "source": source.tag})
      encodes_done = set(query.fetchall())

      images_prepared = False
      fullres_image = None
      for (resolution_index, width, height) in sizes:
        for quality in QUALITIES[encoder.encoder]:
          if (resolution_index, quality) in encodes_done:
            continue

          if not images_prepared:
            # TODO: Generate only the resolutions we need
            source_images = prepare_source_images(source, sizes, tmpdir.name)
            fullres_image = source_images[0]
            images_prepared = True

          jobs.append(Job(encoder, fullres_image, source_images[resolution_index], resolution_index, quality))

  if jobs == []:
    print("Nothing to do - all encodes already in database")
    db.close()
    return

  # Prepare encoder environment if needed
  for encoder in encoders:
    if encoder.encoder == "tinyavif":
      print("Building tinyavif...")
      run(["cargo", "build", "--release", "--quiet"], cwd=TINYAVIF_DIR)
      break

  # Pre-generate output directories
  for encoder in encoders:
    os.makedirs(os.path.join(tmpdir.name, encoder.tag), mode=0o755, exist_ok=True)

  # Sort encodes so that we launch the higher-resolution (lower resolution index)
  # and higher-quality (higher `quality` parameter) first. This helps reduce the
  # tail latency of the batch of encodes
  jobs.sort(key = lambda job: (job.resolution_index, -job.quality))

  total_jobs = len(jobs)

  # Run encodes
  task_queue = multiprocessing.JoinableQueue()

  if arguments.jobs is None:
    num_workers = os.process_cpu_count()
  else:
    num_workers = arguments.jobs

  workers = []
  for _ in range(num_workers):
    worker = multiprocessing.Process(target=worker_main, args=(db, tmpdir.name, total_jobs, task_queue))
    worker.start()
    workers.append(worker)

  for job_number, job in enumerate(jobs):
    task_queue.put((job_number, job))

  task_queue.join()

  for worker in workers:
    worker.terminate()

  db.close()

  print("Done")

if __name__ == "__main__":
  main(sys.argv)

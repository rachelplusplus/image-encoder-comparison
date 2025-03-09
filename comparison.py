#!/usr/bin/env python3
# Image compression comparison script
#
# Compares tinyavif against libaom speed 6 (the default for libavif) and jpegli,
# for a given input file, and plots a graph of the results
#
# TODO: Measure and plot runtimes
# TODO: Compute BDRATEs (== average % filesize reduction)
#       Can use the same logic to plot average % runtime differences too

import os
import subprocess
import sys

from argparse import ArgumentParser
from math import *

import matplotlib.pyplot as plt
from matplotlib import ticker

DEBUG_COMMANDS=False
DEBUG_SEARCH=False

THIS_DIR = os.path.dirname(__file__)
TINYAVIF = os.path.abspath(os.path.join(THIS_DIR, "../tinyavif/target/release/tinyavif"))

# List of SSIMU2 values to target
# Note: Per https://github.com/cloudinary/ssimulacra2, the quality boundaries are:
# 30 => low quality
# 50 => medium quality
# 70 => high quality
# 90 => visually lossless
TARGET_SSIMU2 = [
  # Extra point below 30, so we can use cubic interpolation in the target range
  25,
  # Evenly spaced set within the target range
  30,
  40,
  50,
  60,
  70,
  80,
  90,
  # Extra point above 90, so we can use cubic interpolation in the target range
  95,
]

# (lo, hi) quality inputs for different codecs
# The hi value is treated as exclusive
QUALITY_RANGES = {
  # tinyavif takes a direct qindex value, which is remapped by qindex = 255 - quality
  # We need to disallow quality=255, as this translates to lossless mode, which tinyavif does not support
  "tinyavif": (0, 255),

  # libaom and jpegli both take quality values in [0, 100] inclusive
  # For libaom, quality=100 is lossless, but in this case that's okay
  "libaom": (0, 101),
  "jpegli": (0, 101)
}

def run(cmd, **kwargs):
  if DEBUG_COMMANDS:
    print(cmd)
  return subprocess.run(cmd, check=True, **kwargs)

# Encode, then decode and compare to source file
# Notes:
#
# 1) As of the time of writing, ssimulacra2_rs seems to only support PNG input,
#   so we have to convert the encoded output to a PNG first before we can compute the score
#
# 2) This function takes a quality value, which can have a different range per codec but
#    which is always arranged so that a higher value means better quality.
#    This function takes care of remapping that to the appropriate per-codec parameter,
#    which may have the opposite sense (eg, qindex, where higher means worse).
def calc_ssimu2(codec, quality, source, tmpdir, width, height):
  source_basename = os.path.splitext(os.path.basename(source))[0]
  source_png = os.path.join(tmpdir, "source.png")

  if codec == "tinyavif" or codec == "libaom":
    compressed_ext = "avif"
  elif codec == "jpegli":
    compressed_ext = "jpeg"
  else:
    raise ValueError("Unknown codec %s" % codec)

  compressed_path = os.path.join(tmpdir, f"{codec}_{quality}.{compressed_ext}")

  # TODO: Record runtime here
  if not os.path.exists(compressed_path):
    if codec == "tinyavif":
      run([TINYAVIF, source, "--qindex", str(255 - quality), "-o", compressed_path],
           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif codec == "libaom":
      run(["avifenc", source, "-q", str(quality), "-o", compressed_path],
           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif codec == "jpegli":
      # JPEGli can't currently parse Y4M format inputs, so pass it the PNG instead
      run(["cjpegli", source_png, compressed_path, "-q", str(quality)],
           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
      raise ValueError("Unknown codec %s" % codec)

  png_path = os.path.join(tmpdir, f"{codec}_{quality}.png")
  if not os.path.exists(png_path):
    run(["ffmpeg", "-i", compressed_path, "-loglevel", "quiet", "-y", png_path])

  output = run(["ssimulacra2_rs", "image", source_png, png_path], capture_output=True)

  # Expect a single line of output saying "Score: [...]"
  line = output.stdout.strip()
  if b"\n" in line:
    print("Error: Unexpected output from ssimulacra2_rs:")
    print(line)
    sys.exit(1)
  
  (label, ssimu2) = line.split()
  if label != b"Score:":
    print("Error: Unexpected output from ssimulacra2_rs:")
    print(line)
    sys.exit(1)
  
  bpp = os.stat(compressed_path).st_size * 8.0 / (width * height)

  return (bpp, float(ssimu2))

# Search for the quality setting which is closest to a given SSIMU2 value
# Results are cached in the provided cache (which should start be an empty dict
# on the first call) to avoid recomputation
# TODO: Use cache
def search_ssimu2(codec, target_ssimu2, source, tmpdir, width, height, cache):
  (q_lo, q_hi) = QUALITY_RANGES[codec]

  # Track the closest SSIMU2 to the target that we've found so far
  best_delta_ssimu2 = 100
  best_quality = None

  while q_hi - q_lo > 1:
    q_mid = (q_hi + q_lo) // 2

    if (codec, q_mid) in cache:
      (bpp, ssimu2) = cache[(codec, q_mid)]
      if DEBUG_SEARCH:
        print(f"Search: quality = {q_mid} => ssimu2 = {ssimu2:.2f}, bpp = {bpp:.3f} [cached]")
    else:
      (bpp, ssimu2) = calc_ssimu2(codec, q_mid, source, tmpdir, width, height)
      cache[(codec, q_mid)] = (bpp, ssimu2)
      if DEBUG_SEARCH:
        print(f"Search: quality = {q_mid} => ssimu2 = {ssimu2:.2f}, bpp = {bpp:.3f}")

    delta_ssimu2 = abs(ssimu2 - target_ssimu2)
    if delta_ssimu2 < best_delta_ssimu2:
      best_delta_ssimu2 = delta_ssimu2
      best_quality = q_mid

    # Continue binary search until we run out of options
    if ssimu2 > target_ssimu2:
      # Above target quality, so search lower half
      q_hi = q_mid
    else:
      # Below target quality, so search upper half
      q_lo = q_mid

  assert q_hi - q_lo == 1

  (best_bpp, best_ssimu2) = cache[(codec, best_quality)]
  return (best_quality, best_bpp, best_ssimu2)

# Custom function to format the log scale ticks nicely
# Based on https://stackoverflow.com/a/17209836
def format_tick(value, _):
  exp = floor(log10(value))
  base = int(round(value / 10**exp))

  # Skip labelling the 7 and 9 subdivisions to prevent overlapping labels
  # These skipped subdivisions still get a tick mark on the axis to indicate
  # where they are
  #if base not in (1, 2, 3, 4, 6, 8): return ""

  if exp >= 0:
    # For values >= 1, display with 1 decimal point
    return "%.1f" % int(round(value))
  else:
    # For values < 1, display with the minimal number of decimal places
    fmt = f"%.{-exp:d}f"
    return fmt % value

def main(argv):
  parser = ArgumentParser()
  parser.add_argument("source")
  parser.add_argument("-t", "--tmpdir")
  arguments = parser.parse_args(argv[1:])

  source = arguments.source
  source_basename = os.path.splitext(os.path.basename(source))[0]
  plot_name = source_basename + ".plot.png"

  tmpdir = arguments.tmpdir
  if tmpdir is None:
    tmpdir = source_basename + ".tmp"

  if not source.endswith(".y4m"):
    print("Error: Only .y4m format source files are supported")
    sys.exit(2)

  if not os.path.exists(tmpdir):
    os.makedirs(tmpdir)

  # Convert to PNG for compatibility with ssimulacra2_rs
  source_png = os.path.join(tmpdir, "source.png")
  if not os.path.exists(source_png):
    run(["ffmpeg", "-i", source, "-frames:v", "1", "-y", source_png],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  # Extract image size
  width=None
  height=None
  ffprobe_result = run(["ffprobe", "-hide_banner", "-show_streams", source],
                       capture_output=True)
  for line in ffprobe_result.stdout.split(b"\n"):
    if line.startswith(b"width="):
      width = int(line[6:])
    elif line.startswith(b"height="):
      height = int(line[7:])

  assert width is not None and height is not None

  data = {}

  cache = {}
  for codec in ("tinyavif", "libaom", "jpegli"):
    print(f"Searching {codec}...")
    codec_data = {"bpp": [], "ssimu2": []}

    for target_ssimu2 in TARGET_SSIMU2:
      (quality, bpp, ssimu2) = search_ssimu2(codec, target_ssimu2, source, tmpdir, width, height, cache)
      codec_data["bpp"].append(bpp)
      codec_data["ssimu2"].append(ssimu2)
      print(f"  Target = {target_ssimu2}: closest ssimu2 = {ssimu2:.2f}, bpp = {bpp:.3f}, quality = {quality}")

    data[codec] = codec_data
    print()

  print("Plotting results...")
  fig, ax = plt.subplots()
  ax.set(xlabel="Bits per pixel", ylabel="SSIMU2")
  ax.set_title(f"Big Buck Bunny, Frame 232, {width}x{height}")

  ax.axhline(y=30, color="gray")
  ax.axhline(y=50, color="gray")
  ax.axhline(y=70, color="gray")
  ax.axhline(y=90, color="gray")

  ax.semilogx(data["tinyavif"]["bpp"], data["tinyavif"]["ssimu2"],
              color="black", marker="x", linestyle="-", label="tinyavif")
  ax.semilogx(data["libaom"]["bpp"], data["libaom"]["ssimu2"],
              color="blue", marker="x", linestyle="-", label="libaom")
  ax.semilogx(data["jpegli"]["bpp"], data["jpegli"]["ssimu2"],
              color="red", marker="x", linestyle="-", label="jpegli")

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
  plt.savefig(plot_name, dpi=192)

if __name__ == "__main__":
  main(sys.argv)

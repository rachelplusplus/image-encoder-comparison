#!/usr/bin/env python3

import os
import subprocess
import sys

from argparse import ArgumentParser

SCRIPT_DIR = os.path.dirname(__file__)

VERBOSE = False


def run(cmd, **kwargs):
  if VERBOSE:
    print(f"Running `{" ".join(map(shlex.quote, cmd))}`")
  return subprocess.run(cmd, check=True, **kwargs)



def parse_args(argv):
  global VERBOSE

  parser = ArgumentParser(prog=argv[0])

  parser.add_argument("-b", "--build-root", default="./build",
                      help="Directory to build tools under. Defaults to build/ in the current directory")
  parser.add_argument("-v", "--verbose", action="store_true",
                      help=f"Print more status messages")

  parsed_args = parser.parse_args(argv[1:])

  VERBOSE = parsed_args.verbose

  return parsed_args



def build_tinyavif(build_root):
  src_dir = os.path.join(SCRIPT_DIR, "tinyavif")
  build_dir = os.path.join(build_root, "tinyavif")

  print("Building tinyavif...")
  # TODO: Capture output and only print on error
  run(["cargo", "build",
       "--release",
       "--target-dir", os.path.relpath(build_dir, src_dir),
      ], cwd=src_dir)



def build_jxl_tools(build_root):
  src_dir = os.path.join(SCRIPT_DIR, "libjxl")
  build_dir = os.path.join(build_root, "libjxl")

  os.makedirs(build_dir, mode=0o755, exist_ok=True)

  print("Configuring libjxl tools...")
  # TODO: Capture output and only print on error
  run(["cmake", "-DCMAKE_BUILD_TYPE=Release",
       "-DBUILD_TESTING=off",
       "-DJPEGXL_ENABLE_DEVTOOLS=ON",
       "-DCMAKE_POLICY_VERSION_MINIMUM=3.5", # Work around an error message with libjxl 0.11.1 + cmake 4.1.2
       os.path.relpath(src_dir, build_dir)
      ], cwd=build_dir)

  print("Building libjxl tools...")
  # TODO: Capture output and only print on error
  run(["make", "-j", "ssimulacra2", "butteraugli_main"], cwd=build_dir)



def main(argv):
  arguments = parse_args(argv)

  # Fetch submodules
  # libjxl in particular has a *lot* of recursive submodules, so this ensures everything is fetched properly.
  run(["git", "submodule", "update", "--init", "--recursive"], cwd=SCRIPT_DIR)

  build_tinyavif(arguments.build_root)
  build_jxl_tools(arguments.build_root)


if __name__ == "__main__":
  main(sys.argv)

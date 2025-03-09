#!/usr/bin/env python3
# Script to set up reproducible test inputs
# This must be run on a 1080p24 copy of the short film Big Buck Bunny - this can be
# freely acquired from media.xiph.org
#
# Expected SHA256 hashes can be found in inputs.sha256sum

import os
import subprocess
import sys

DEBUG_COMMANDS = True

def run(cmd, **kwargs):
  if DEBUG_COMMANDS:
    print(cmd)
  return subprocess.run(cmd, check=True, **kwargs)

def main(argv):
  if len(argv) != 2:
    print(f"Usage: {argv[0]} PATH")
    sys.exit(2)

  # Extract target frame
  run(["ffmpeg", "-i", argv[1], "-y",
       "-vf", "select=eq(n\\,232)", "-fps_mode", "passthrough", "-frames:v", "1",
       "big_buck_bunny_f232_1080.y4m"
  ])

  # Then create reduced-size versions
  run(["ffmpeg", "-i", "big_buck_bunny_f232_1080.y4m", "-y",
       "-vf", "scale=1280:720",
       "big_buck_bunny_f232_720.y4m"
  ])

  run(["ffmpeg", "-i", "big_buck_bunny_f232_1080.y4m", "-y",
       "-vf", "scale=640:360",
       "big_buck_bunny_f232_360.y4m"
  ])

  run(["ffmpeg", "-i", "big_buck_bunny_f232_1080.y4m", "-y",
       "-vf", "scale=427:240",
       "big_buck_bunny_f232_240.y4m"
  ])

if __name__ == "__main__":
  main(sys.argv)

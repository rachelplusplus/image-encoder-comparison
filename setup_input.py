#!/usr/bin/env python3
# Script to set up reproducible test inputs
# This must be run on a 1080p24 copy of the short film Big Buck Bunny - this can be
# freely acquired from media.xiph.org
#
# Copyright (c) 2025, Monocot Limited. All rights reserved
#
# This source code is subject to the terms of the BSD 2 Clause License. If the BSD 2 Clause License
# was not distributed with this source code in the LICENSE file, you can obtain it at
# https://opensource.org/license/bsd-2-clause

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
       "-vf", "select=eq(n\\,231)", "-fps_mode", "passthrough", "-frames:v", "1",
       "big_buck_bunny_f231_1080.y4m"
  ])

  # Then create reduced-size versions
  run(["ffmpeg", "-i", "big_buck_bunny_f231_1080.y4m", "-y",
       "-vf", "scale=1280:720",
       "big_buck_bunny_f231_720.y4m"
  ])

  run(["ffmpeg", "-i", "big_buck_bunny_f231_1080.y4m", "-y",
       "-vf", "scale=640:360",
       "big_buck_bunny_f231_360.y4m"
  ])

  run(["ffmpeg", "-i", "big_buck_bunny_f231_1080.y4m", "-y",
       "-vf", "scale=427:240",
       "big_buck_bunny_f231_240.y4m"
  ])

if __name__ == "__main__":
  main(sys.argv)

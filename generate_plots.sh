#!/bin/bash
set -eux

SOURCE_DIR=../test-videos

if ! [ -e big_buck_bunny_f231.y4m ]; then
  # TODO: Check SHA256 checksum of the resulting file?
  ffmpeg -i $SOURCE_DIR/big_buck_bunny_1080p24.y4m \
         -vf 'select=eq(n\,231)' -fps_mode passthrough -frames:v 1 \
         -loglevel warning \
         big_buck_bunny_f231.y4m
fi

./encode.py tinyavif-1.1 tinyavif big_buck_bunny_f231.y4m
./encode.py jpegli-0.11.1 jpegli big_buck_bunny_f231.y4m
./encode.py aom-3.12.1 libaom big_buck_bunny_f231.y4m

./plot.py -s big_buck_bunny_f231.y4m aom-3.12.1 jpegli-0.11.1  tinyavif-1.1

#!/bin/bash
set -eux

SOURCE_DIR=../test-videos

# Update to old blog post
./encode.py "libaom-3.12.1, speed 6" libaom "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py jpegli-0.11.1 jpegli "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py tinyavif-1.1 tinyavif "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"

./plot.py -t "Big Buck Bunny, frame 231" -o big_buck_bunny -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
          "libaom-3.12.1, speed 6" jpegli-0.11.1 tinyavif-1.1

# New results across a wider range of sources
./encode.py "libaom-3.12.1, speed 6" libaom photography-sources.txt
./encode.py jpegli-0.11.1 jpegli photography-sources.txt
./encode.py tinyavif-1.1 tinyavif photography-sources.txt

./plot.py -t "Mixed photography" -o photography -s photography-sources.txt \
          "libaom-3.12.1, speed 6" jpegli-0.11.1 tinyavif-1.1

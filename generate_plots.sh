#!/bin/bash
set -eux

SOURCE_DIR=../test-videos

if false; then
# Update to old blog post
./encode.py "libaom-3.12.1, speed 6" aom "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom-3.12.1, speed 8" aom:speed=8 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom-3.12.1, speed 10" aom:speed=10 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py jpegli-0.11.1 jpegli "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py tinyavif-1.1 tinyavif "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"

./plot.py -t "Big Buck Bunny, frame 231" -o big_buck_bunny -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
          "libaom-3.12.1, speed 6" jpegli-0.11.1 tinyavif-1.1
./plot.py -t "Big Buck Bunny, frame 231" -o big_buck_bunny_s8 -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
          "libaom-3.12.1, speed 8" jpegli-0.11.1 tinyavif-1.1
./plot.py -t "Big Buck Bunny, frame 231" -o big_buck_bunny_s10 -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
          "libaom-3.12.1, speed 10" jpegli-0.11.1 tinyavif-1.1

# New results across a wider range of sources
./encode.py "libaom-3.12.1, speed 6" aom photography-sources.txt
./encode.py "libaom-3.12.1, speed 8" aom:speed=8 photography-sources.txt
./encode.py "libaom-3.12.1, speed 10" aom:speed=10 photography-sources.txt
./encode.py jpegli-0.11.1 jpegli photography-sources.txt
./encode.py tinyavif-1.1 tinyavif photography-sources.txt

./plot.py -t "Mixed photography" -o photography -s photography-sources.txt \
          "libaom-3.12.1, speed 6" jpegli-0.11.1 tinyavif-1.1
./plot.py -t "Mixed photography" -o photography_s8 -s photography-sources.txt \
          "libaom-3.12.1, speed 8" jpegli-0.11.1 tinyavif-1.1
./plot.py -t "Mixed photography" -o photography_s10 -s photography-sources.txt \
          "libaom-3.12.1, speed 10" jpegli-0.11.1 tinyavif-1.1
fi

# Generate results so we can compare existing encoders.
# These take a long time, so are skipped by default
if false; then
./encode.py "libaom-3.12.1, speed 2" aom:speed=2 photography-sources.txt
./encode.py "libaom-3.12.1, speed 4" aom:speed=4 photography-sources.txt
./encode.py "libaom-3.12.1, speed 8" aom:speed=8 photography-sources.txt
./encode.py "libaom-3.12.1, speed 10" aom:speed=10 photography-sources.txt

./encode.py "svt-av1-3.0.2, speed 2" svt:speed=2 photography-sources.txt
./encode.py "svt-av1-3.0.2, speed 4" svt:speed=4 photography-sources.txt
./encode.py "svt-av1-3.0.2, speed 6" svt:speed=6 photography-sources.txt
./encode.py "svt-av1-3.0.2, speed 8" svt:speed=8 photography-sources.txt
./encode.py "svt-av1-3.0.2, speed 10" svt:speed=10 photography-sources.txt

./encode.py "rav1e-0.7.1, speed 2" rav1e:speed=2 photography-sources.txt
./encode.py "rav1e-0.7.1, speed 4" rav1e:speed=4 photography-sources.txt
./encode.py "rav1e-0.7.1, speed 6" rav1e:speed=6 photography-sources.txt
./encode.py "rav1e-0.7.1, speed 8" rav1e:speed=8 photography-sources.txt
./encode.py "rav1e-0.7.1, speed 10" rav1e:speed=10 photography-sources.txt

./plot.py -t "Libaom comparison" -o libaom -s photography-sources.txt \
         "libaom-3.12.1, speed 2" "libaom-3.12.1, speed 4" "libaom-3.12.1, speed 6" "libaom-3.12.1, speed 8" "libaom-3.12.1, speed 10"

./plot.py -t "SVT-AV1 comparison" -o svt-av1 -s photography-sources.txt \
         "svt-av1-3.0.2, speed 2" "svt-av1-3.0.2, speed 4" "svt-av1-3.0.2, speed 6" "svt-av1-3.0.2, speed 8" "svt-av1-3.0.2, speed 10"

./plot.py -t "Rav1e comparison" -o rav1e -s photography-sources.txt \
         "rav1e-0.7.1, speed 2" "rav1e-0.7.1, speed 4" "rav1e-0.7.1, speed 6" "rav1e-0.7.1, speed 8" "rav1e-0.7.1, speed 10"
fi

./plot_size_vs_runtime.py -t "Image compression comparison" -o comparison -s photography-sources.txt -r "libaom-3.12.1, speed 6" \
  "libaom 3.12.1:libaom-3.12.1, speed 2:libaom-3.12.1, speed 4:libaom-3.12.1, speed 6:libaom-3.12.1, speed 8:libaom-3.12.1, speed 10" \
  "SVT-AV1 3.0.2:svt-av1-3.0.2, speed 2:svt-av1-3.0.2, speed 4:svt-av1-3.0.2, speed 6:svt-av1-3.0.2, speed 8:svt-av1-3.0.2, speed 10" \
  "rav1e 0.7.1:rav1e-0.7.1, speed 2:rav1e-0.7.1, speed 4:rav1e-0.7.1, speed 6:rav1e-0.7.1, speed 8:rav1e-0.7.1, speed 10"

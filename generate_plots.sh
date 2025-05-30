#!/bin/bash
set -eux

SOURCE_DIR=../test-videos

if false; then
# Update to old blog post
./encode.py "libaom 3.12.1, speed 6" aom "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom 3.12.1, speed 8" aom:speed=8 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom 3.12.1, speed 10" aom:speed=10 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "JPEGli 0.11.1" jpegli "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "tinyavif 1.1" tinyavif "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"

./plot_quality_curves.py -t "Big Buck Bunny, frame 231" -o big_buck_bunny -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
          "libaom 3.12.1, speed 6" "JPEGli 0.11.1" "tinyavif 1.1"
./plot_quality_curves.py -t "Big Buck Bunny, frame 231" -o big_buck_bunny_s8 -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
          "libaom 3.12.1, speed 8" "JPEGli 0.11.1" "tinyavif 1.1"
./plot_quality_curves.py -t "Big Buck Bunny, frame 231" -o big_buck_bunny_s10 -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
          "libaom 3.12.1, speed 10" "JPEGli 0.11.1" "tinyavif 1.1"
fi

if true; then
# New results across a wider range of sources
# Run lots of encodes so that we can do a full BDRATE vs. speed comparison
./encode.py "JPEGli 0.11.1" jpegli photography-sources.txt
./encode.py "tinyavif 1.1" tinyavif photography-sources.txt

./encode.py "libaom 3.12.1, speed 1" aom:speed=1 photography-sources.txt
./encode.py "libaom 3.12.1, speed 2" aom:speed=2 photography-sources.txt
./encode.py "libaom 3.12.1, speed 3" aom:speed=3 photography-sources.txt
./encode.py "libaom 3.12.1, speed 4" aom:speed=4 photography-sources.txt
./encode.py "libaom 3.12.1, speed 5" aom:speed=5 photography-sources.txt
./encode.py "libaom 3.12.1, speed 6" aom:speed=6 photography-sources.txt
./encode.py "libaom 3.12.1, speed 7" aom:speed=7 photography-sources.txt
./encode.py "libaom 3.12.1, speed 8" aom:speed=8 photography-sources.txt
./encode.py "libaom 3.12.1, speed 9" aom:speed=9 photography-sources.txt
# libaom does not have a speed 10

./encode.py "SVT-AV1 3.0.2, speed 1" svt:speed=1 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 2" svt:speed=2 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 3" svt:speed=3 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 4" svt:speed=4 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 5" svt:speed=5 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 6" svt:speed=6 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 7" svt:speed=7 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 8" svt:speed=8 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 9" svt:speed=9 photography-sources.txt
./encode.py "SVT-AV1 3.0.2, speed 10" svt:speed=10 photography-sources.txt
# SVT-AV1 supports speeds up to 13, but libavif does not allow access to speeds > 10

./encode.py "rav1e 0.7.1, speed 1" rav1e:speed=1 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 2" rav1e:speed=2 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 3" rav1e:speed=3 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 4" rav1e:speed=4 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 5" rav1e:speed=5 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 6" rav1e:speed=6 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 7" rav1e:speed=7 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 8" rav1e:speed=8 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 9" rav1e:speed=9 photography-sources.txt
./encode.py "rav1e 0.7.1, speed 10" rav1e:speed=10 photography-sources.txt

./encode.py "JPEG-XL 0.11.1, speed 1" jpegxl:speed=1 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 2" jpegxl:speed=2 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 3" jpegxl:speed=3 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 4" jpegxl:speed=4 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 5" jpegxl:speed=5 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 6" jpegxl:speed=6 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 7" jpegxl:speed=7 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 8" jpegxl:speed=8 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 9" jpegxl:speed=9 photography-sources.txt
./encode.py "JPEG-XL 0.11.1, speed 10" jpegxl:speed=10 photography-sources.txt

# Skip WebP - it doesn't manage to reach SSIMU2=90 on a lot of the test images, even
# with its quality parameter set to 100
#./encode.py "WebP 1.5.0, speed 0" webp:speed=0 photography-sources.txt
#./encode.py "WebP 1.5.0, speed 1" webp:speed=1 photography-sources.txt
#./encode.py "WebP 1.5.0, speed 2" webp:speed=2 photography-sources.txt
#./encode.py "WebP 1.5.0, speed 3" webp:speed=3 photography-sources.txt
#./encode.py "WebP 1.5.0, speed 4" webp:speed=4 photography-sources.txt
#./encode.py "WebP 1.5.0, speed 5" webp:speed=5 photography-sources.txt
#./encode.py "WebP 1.5.0, speed 6" webp:speed=6 photography-sources.txt

#./plot_quality_curves.py -t "Mixed photography" -o photography -s photography-sources.txt \
#          "libaom 3.12.1, speed 6" "JPEGli 0.11.1" "tinyavif 1.1"
#./plot_quality_curves.py -t "Mixed photography" -o photography_s8 -s photography-sources.txt \
#          "libaom 3.12.1, speed 8" "JPEGli 0.11.1" "tinyavif 1.1"
#./plot_quality_curves.py -t "Mixed photography" -o photography_s10 -s photography-sources.txt \
#          "libaom 3.12.1, speed 10" "JPEGli 0.11.1" "tinyavif 1.1"

./plot_size_vs_runtime.py -t "Tinyavif comparison" -o tinyavif-comparison-alt -s photography-sources.txt -r "libaom 3.12.1, speed 6" \
  "libaom 3.12.1:libaom 3.12.1, speed 1:libaom 3.12.1, speed 2:libaom 3.12.1, speed 3:libaom 3.12.1, speed 4:libaom 3.12.1, speed 5:libaom 3.12.1, speed 6:libaom 3.12.1, speed 7:libaom 3.12.1, speed 8:libaom 3.12.1, speed 9" \
  "JPEGli 0.11.1:JPEGli 0.11.1" \
  "tinyavif 1.1:tinyavif 1.1"

./plot_size_vs_runtime.py -t "Image compression comparison" -o comparison-alt -s photography-sources.txt -r "libaom 3.12.1, speed 6" \
  "libaom 3.12.1:libaom 3.12.1, speed 1:libaom 3.12.1, speed 2:libaom 3.12.1, speed 3:libaom 3.12.1, speed 4:libaom 3.12.1, speed 5:libaom 3.12.1, speed 6:libaom 3.12.1, speed 7:libaom 3.12.1, speed 8:libaom 3.12.1, speed 9" \
  "SVT-AV1 3.0.2:SVT-AV1 3.0.2, speed 1:SVT-AV1 3.0.2, speed 2:SVT-AV1 3.0.2, speed 3:SVT-AV1 3.0.2, speed 4:SVT-AV1 3.0.2, speed 5:SVT-AV1 3.0.2, speed 6:SVT-AV1 3.0.2, speed 7:SVT-AV1 3.0.2, speed 8:SVT-AV1 3.0.2, speed 9:SVT-AV1 3.0.2, speed 10" \
  "rav1e 0.7.1:rav1e 0.7.1, speed 1:rav1e 0.7.1, speed 2:rav1e 0.7.1, speed 3:rav1e 0.7.1, speed 4:rav1e 0.7.1, speed 5:rav1e 0.7.1, speed 6:rav1e 0.7.1, speed 7:rav1e 0.7.1, speed 8:rav1e 0.7.1, speed 9:rav1e 0.7.1, speed 10" \
  "JPEG-XL 0.11.1:JPEG-XL 0.11.1, speed 1:JPEG-XL 0.11.1, speed 2:JPEG-XL 0.11.1, speed 3:JPEG-XL 0.11.1, speed 4:JPEG-XL 0.11.1, speed 5:JPEG-XL 0.11.1, speed 6:JPEG-XL 0.11.1, speed 7:JPEG-XL 0.11.1, speed 8:JPEG-XL 0.11.1, speed 9:JPEG-XL 0.11.1, speed 10" \
  "JPEGli 0.11.1:JPEGli 0.11.1"
fi

#!/bin/bash
set -eux

SOURCE_DIR=../test-videos

RUN_ENCODES=0
GENERATE_GRAPHS=0

# Skip WebP for now - it doesn't manage to reach SSIMU2=90 on a lot of the test images,
# even with its quality parameter set to 100
RUN_WEBP=0

# Only one of SVT-AVT or SVT-AV1-PSY can be installed at one time.
# So to generate the full set of encodes, please do the following:
# * Install SVT-AV1, set HAVE_SVT_AV1_PSY=0 and run this script
# * Install SVT-AV1-PSY, set HAVE_SVT_AV1_PSY=1 and run this script again
HAVE_SVT_AV1_PSY=0

if [ "$RUN_ENCODES" -eq "1" ]; then
# Update to old blog post
# We only need 8-bit versions of these for the blog post
./encode.py "libaom 3.12.1, speed 6" aom "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom 3.12.1, speed 7" aom:speed=7 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom 3.12.1, speed 8" aom:speed=8 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom 3.12.1, speed 9" aom:speed=9 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "JPEGli 0.11.1" jpegli "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "tinyavif 1.1" tinyavif "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"

./encode.py "JPEGli 0.11.1" jpegli testset-8bit.txt testset-10bit.txt testset-12bit.txt

# tinyavif does not support 10-bit encoding
./encode.py "tinyavif 1.1" tinyavif testset-8bit.txt

./encode.py "libaom 3.12.1, speed 1" aom:speed=1 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 2" aom:speed=2 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 3" aom:speed=3 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 4" aom:speed=4 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 5" aom:speed=5 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 6" aom:speed=6 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 7" aom:speed=7 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 8" aom:speed=8 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 9" aom:speed=9 testset-8bit.txt testset-10bit.txt testset-12bit.txt
# libaom does not have a speed 10

./encode.py "libaom 3.12.1, speed 1, tune=iq" aom:speed=1:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 2, tune=iq" aom:speed=2:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 3, tune=iq" aom:speed=3:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 4, tune=iq" aom:speed=4:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 5, tune=iq" aom:speed=5:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 6, tune=iq" aom:speed=6:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 7, tune=iq" aom:speed=7:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 8, tune=iq" aom:speed=8:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "libaom 3.12.1, speed 9, tune=iq" aom:speed=9:tune=iq testset-8bit.txt testset-10bit.txt testset-12bit.txt
# libaom does not have a speed 10

# Note: SVT-AV1 doesn't support 12-bit input
if [ "$HAVE_SVT_AV1_PSY" -eq "1" ]; then
./encode.py "SVT-AV1-PSY 3.0.2, speed 1" svt:speed=1:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 2" svt:speed=2:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 3" svt:speed=3:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 4" svt:speed=4:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 5" svt:speed=5:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 6" svt:speed=6:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 7" svt:speed=7:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 8" svt:speed=8:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 9" svt:speed=9:tune=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1-PSY 3.0.2, speed 10" svt:speed=10:tune=4 testset-8bit.txt testset-10bit.txt
else
./encode.py "SVT-AV1 3.0.2, speed 1" svt:speed=1 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 2" svt:speed=2 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 3" svt:speed=3 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 4" svt:speed=4 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 5" svt:speed=5 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 6" svt:speed=6 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 7" svt:speed=7 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 8" svt:speed=8 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 9" svt:speed=9 testset-8bit.txt testset-10bit.txt
./encode.py "SVT-AV1 3.0.2, speed 10" svt:speed=10 testset-8bit.txt testset-10bit.txt
fi

./encode.py "rav1e 0.7.1, speed 1" rav1e:speed=1 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 2" rav1e:speed=2 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 3" rav1e:speed=3 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 4" rav1e:speed=4 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 5" rav1e:speed=5 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 6" rav1e:speed=6 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 7" rav1e:speed=7 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 8" rav1e:speed=8 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 9" rav1e:speed=9 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "rav1e 0.7.1, speed 10" rav1e:speed=10 testset-8bit.txt testset-10bit.txt testset-12bit.txt

./encode.py "JPEG-XL 0.11.1, speed 1" jpegxl:speed=1 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 2" jpegxl:speed=2 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 3" jpegxl:speed=3 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 4" jpegxl:speed=4 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 5" jpegxl:speed=5 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 6" jpegxl:speed=6 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 7" jpegxl:speed=7 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 8" jpegxl:speed=8 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 9" jpegxl:speed=9 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "JPEG-XL 0.11.1, speed 10" jpegxl:speed=10 testset-8bit.txt testset-10bit.txt testset-12bit.txt

if [ "$RUN_WEBP" -eq "1" ]; then
# TODO: Does WebP support 10-bit input?
./encode.py "WebP 1.5.0, speed 0" webp:speed=0 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "WebP 1.5.0, speed 1" webp:speed=1 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "WebP 1.5.0, speed 2" webp:speed=2 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "WebP 1.5.0, speed 3" webp:speed=3 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "WebP 1.5.0, speed 4" webp:speed=4 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "WebP 1.5.0, speed 5" webp:speed=5 testset-8bit.txt testset-10bit.txt testset-12bit.txt
./encode.py "WebP 1.5.0, speed 6" webp:speed=6 testset-8bit.txt testset-10bit.txt testset-12bit.txt
fi
fi

if [ "$GENERATE_GRAPHS" -eq "1" ]; then
# Now plot the graphs used in the "Evaluating image compression tools" blog post...
./plot_quality_curves.py -t "Big Buck Bunny" -o libaom_bbb -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
  "libaom 3.12.1, speed 6" "libaom 3.12.1, speed 7" "libaom 3.12.1, speed 8" "libaom 3.12.1, speed 9"

./plot_quality_curves.py -t "Full test set" -o libaom_full -s testset-8bit.txt \
  "libaom 3.12.1, speed 6" "libaom 3.12.1, speed 7" "libaom 3.12.1, speed 8" "libaom 3.12.1, speed 9"

# Use a wider range than the other plots, as this makes it easier to fit the 360p component into context
./plot_multires_components.py -t "Big Buck Bunny" -o components_tinyavif --range 20-100 \
  -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" "tinyavif 1.1"

./plot_quality_curves.py -t "Big Buck Bunny" -o multires_tinyavif -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
  "tinyavif 1.1"

# Use a wider range than the other scripts, as this makes it easier to fit the 360p component into context
./plot_multires_components.py -t "Big Buck Bunny" -o components_libaom --range 20-100 \
  -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" "libaom 3.12.1, speed 6"

./plot_quality_curves.py -t "Big Buck Bunny" -o multires_libaom -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
  "libaom 3.12.1, speed 6"

./plot_quality_curves.py -t "Full test set" -o fullset -s testset-8bit.txt \
  "libaom 3.12.1, speed 6" "JPEGli 0.11.1" "tinyavif 1.1"

./plot_size_vs_runtime.py -t "Full test set" -o comparison -s testset-8bit.txt -r "libaom 3.12.1, speed 6" \
  "libaom 3.12.1:libaom 3.12.1, speed 1:libaom 3.12.1, speed 2:libaom 3.12.1, speed 3:libaom 3.12.1, speed 4:libaom 3.12.1, speed 5:libaom 3.12.1, speed 6:libaom 3.12.1, speed 7:libaom 3.12.1, speed 8:libaom 3.12.1, speed 9" \
  "SVT-AV1 3.0.2:SVT-AV1 3.0.2, speed 1:SVT-AV1 3.0.2, speed 2:SVT-AV1 3.0.2, speed 3:SVT-AV1 3.0.2, speed 4:SVT-AV1 3.0.2, speed 5:SVT-AV1 3.0.2, speed 6:SVT-AV1 3.0.2, speed 7:SVT-AV1 3.0.2, speed 8:SVT-AV1 3.0.2, speed 9:SVT-AV1 3.0.2, speed 10" \
  "rav1e 0.7.1:rav1e 0.7.1, speed 1:rav1e 0.7.1, speed 2:rav1e 0.7.1, speed 3:rav1e 0.7.1, speed 4:rav1e 0.7.1, speed 5:rav1e 0.7.1, speed 6:rav1e 0.7.1, speed 7:rav1e 0.7.1, speed 8:rav1e 0.7.1, speed 9:rav1e 0.7.1, speed 10" \
  "JPEG-XL 0.11.1:JPEG-XL 0.11.1, speed 1:JPEG-XL 0.11.1, speed 2:JPEG-XL 0.11.1, speed 3:JPEG-XL 0.11.1, speed 4:JPEG-XL 0.11.1, speed 5:JPEG-XL 0.11.1, speed 6:JPEG-XL 0.11.1, speed 7:JPEG-XL 0.11.1, speed 8:JPEG-XL 0.11.1, speed 9:JPEG-XL 0.11.1, speed 10" \
  "JPEGli 0.11.1:JPEGli 0.11.1" \
  "tinyavif 1.1:tinyavif 1.1"

# ...and pick out the ones we actually need

mkdir -p graphs/

cp libaom_bbb/sizes_1080p.png                             graphs/libaom_bbb.png
cp libaom_full/sizes_1080p.png                            graphs/libaom_full.png

cp components_tinyavif/sizes.png                          graphs/components_tinyavif.png
cp multires_tinyavif/sizes_multires.png                   graphs/multires_tinyavif.png
cp components_libaom/sizes.png                            graphs/components_libaom.png
cp multires_libaom/sizes_multires.png                     graphs/multires_libaom.png

cp fullset/sizes_1080p.png                                graphs/fullset_sizes_1080p.png
cp fullset/runtimes_1080p.png                             graphs/fullset_runtimes_1080p.png
cp fullset/sizes_multires.png                             graphs/fullset_sizes_multires.png
cp fullset/runtimes_multires.png                          graphs/fullset_runtimes_multires.png

cp comparison/size_vs_runtime_1080p.png                   graphs/comparison_1080p.png
cp comparison/size_vs_runtime_multires.png                graphs/comparison_multires.png

# TODO: Plot the graphs for the follow-up post
fi

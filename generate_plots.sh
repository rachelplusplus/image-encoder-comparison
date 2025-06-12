#!/bin/bash
set -eux

SOURCE_DIR=../test-videos

RUN_ENCODES=0

# Skip WebP for now - it doesn't manage to reach SSIMU2=90 on a lot of the test images,
# even with its quality parameter set to 100
RUN_WEBP=0

if [ "$RUN_ENCODES" -eq "1" ]; then
# Update to old blog post
./encode.py "libaom 3.12.1, speed 6" aom "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom 3.12.1, speed 7" aom:speed=7 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom 3.12.1, speed 8" aom:speed=8 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "libaom 3.12.1, speed 9" aom:speed=9 "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "JPEGli 0.11.1" jpegli "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"
./encode.py "tinyavif 1.1" tinyavif "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m"

# New results across a wider range of sources
# Run lots of encodes so that we can do a full BDRATE vs. speed comparison
./encode.py "JPEGli 0.11.1" jpegli testset.txt
./encode.py "tinyavif 1.1" tinyavif testset.txt

./encode.py "libaom 3.12.1, speed 1" aom:speed=1 testset.txt
./encode.py "libaom 3.12.1, speed 2" aom:speed=2 testset.txt
./encode.py "libaom 3.12.1, speed 3" aom:speed=3 testset.txt
./encode.py "libaom 3.12.1, speed 4" aom:speed=4 testset.txt
./encode.py "libaom 3.12.1, speed 5" aom:speed=5 testset.txt
./encode.py "libaom 3.12.1, speed 6" aom:speed=6 testset.txt
./encode.py "libaom 3.12.1, speed 7" aom:speed=7 testset.txt
./encode.py "libaom 3.12.1, speed 8" aom:speed=8 testset.txt
./encode.py "libaom 3.12.1, speed 9" aom:speed=9 testset.txt
# libaom does not have a speed 10

./encode.py "SVT-AV1 3.0.2, speed 1" svt:speed=1 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 2" svt:speed=2 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 3" svt:speed=3 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 4" svt:speed=4 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 5" svt:speed=5 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 6" svt:speed=6 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 7" svt:speed=7 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 8" svt:speed=8 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 9" svt:speed=9 testset.txt
./encode.py "SVT-AV1 3.0.2, speed 10" svt:speed=10 testset.txt
# SVT-AV1 supports speeds up to 13, but libavif does not allow access to speeds > 10

./encode.py "rav1e 0.7.1, speed 1" rav1e:speed=1 testset.txt
./encode.py "rav1e 0.7.1, speed 2" rav1e:speed=2 testset.txt
./encode.py "rav1e 0.7.1, speed 3" rav1e:speed=3 testset.txt
./encode.py "rav1e 0.7.1, speed 4" rav1e:speed=4 testset.txt
./encode.py "rav1e 0.7.1, speed 5" rav1e:speed=5 testset.txt
./encode.py "rav1e 0.7.1, speed 6" rav1e:speed=6 testset.txt
./encode.py "rav1e 0.7.1, speed 7" rav1e:speed=7 testset.txt
./encode.py "rav1e 0.7.1, speed 8" rav1e:speed=8 testset.txt
./encode.py "rav1e 0.7.1, speed 9" rav1e:speed=9 testset.txt
./encode.py "rav1e 0.7.1, speed 10" rav1e:speed=10 testset.txt

./encode.py "JPEG-XL 0.11.1, speed 1" jpegxl:speed=1 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 2" jpegxl:speed=2 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 3" jpegxl:speed=3 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 4" jpegxl:speed=4 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 5" jpegxl:speed=5 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 6" jpegxl:speed=6 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 7" jpegxl:speed=7 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 8" jpegxl:speed=8 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 9" jpegxl:speed=9 testset.txt
./encode.py "JPEG-XL 0.11.1, speed 10" jpegxl:speed=10 testset.txt

if [ "$RUN_WEBP" -eq "1" ]; then
./encode.py "WebP 1.5.0, speed 0" webp:speed=0 testset.txt
./encode.py "WebP 1.5.0, speed 1" webp:speed=1 testset.txt
./encode.py "WebP 1.5.0, speed 2" webp:speed=2 testset.txt
./encode.py "WebP 1.5.0, speed 3" webp:speed=3 testset.txt
./encode.py "WebP 1.5.0, speed 4" webp:speed=4 testset.txt
./encode.py "WebP 1.5.0, speed 5" webp:speed=5 testset.txt
./encode.py "WebP 1.5.0, speed 6" webp:speed=6 testset.txt
fi

./plot_quality_curves.py -t "Full test set" -o photography -s testset.txt \
  "libaom 3.12.1, speed 6" "JPEGli 0.11.1" "tinyavif 1.1"
./plot_quality_curves.py -t "Full test set" -o photography_s7 -s testset.txt \
  "libaom 3.12.1, speed 7" "JPEGli 0.11.1" "tinyavif 1.1"
./plot_quality_curves.py -t "Full test set" -o photography_s8 -s testset.txt \
  "libaom 3.12.1, speed 8" "JPEGli 0.11.1" "tinyavif 1.1"
./plot_quality_curves.py -t "Full test set" -o photography_s9 -s testset.txt \
  "libaom 3.12.1, speed 9" "JPEGli 0.11.1" "tinyavif 1.1"
fi

# Now plot the graphs used in the "Evaluating image compression tools" blog post...
./plot_quality_curves.py -t "Big Buck Bunny" -o libaom_bbb -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
  "libaom 3.12.1, speed 6" "libaom 3.12.1, speed 7" "libaom 3.12.1, speed 8" "libaom 3.12.1, speed 9"

./plot_quality_curves.py -t "Full test set" -o libaom_full -s testset.txt \
  "libaom 3.12.1, speed 6" "libaom 3.12.1, speed 7" "libaom 3.12.1, speed 8" "libaom 3.12.1, speed 9"

./plot_multires_components.py -t "Big Buck Bunny" -o components_tinyavif \
  -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" "tinyavif 1.1"

./plot_quality_curves.py -t "Big Buck Bunny" -o multires_tinyavif -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
  "tinyavif 1.1"

./plot_multires_components.py -t "Big Buck Bunny" -o components_libaom \
  -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" "libaom 3.12.1, speed 6"

./plot_quality_curves.py -t "Big Buck Bunny" -o multires_libaom -s "../test-videos/Big Buck Bunny/big_buck_bunny_f231.y4m" \
  "libaom 3.12.1, speed 6"

./plot_quality_curves.py -t "Full test set" -o fullset -s testset.txt \
  "libaom 3.12.1, speed 6" "JPEGli 0.11.1" "tinyavif 1.1"

./plot_size_vs_runtime.py -t "Full test set" -o comparison -s testset.txt -r "libaom 3.12.1, speed 6" \
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

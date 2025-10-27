#!/bin/bash
set -eux

RUN_ENCODES=0
GENERATE_GRAPHS=1

if [ "$RUN_ENCODES" -eq "1" ]; then
# Generate single-file results, using a still frame from Big Buck Bunny
./encode.py -e encoders/big_buck_bunny.toml -s sources/big_buck_bunny.toml

# Then generate a more complete test set for the remaining graphs
./encode.py -e encoders/fullset.toml -s sources/fullset.toml

# Split off SVT-AV1-HDR encodes into their own script
# As mainline SVT-AVT and SVT-AV1-HDR cannot be installed simultaneously, this needs to
# be run separately after installing SVT-AV1-HDR over the mainline version
#./encode.py -e encoders/svt-av1-hdr.toml -s sources/fullset.toml
fi

if [ "$GENERATE_GRAPHS" -eq "1" ]; then
# Now plot the graphs used in the "Evaluating image compression tools" blog post:

./plot_quality_curves.py -t "Big Buck Bunny, libaom 3.13.1" -o libaom_bbb -e encoders/big_buck_bunny.toml -s sources/big_buck_bunny.toml \
  "Speed 6:libaom-s6" "Speed 7:libaom-s7" "Speed 8:libaom-s8" "Speed 9:libaom-s9"

./plot_quality_curves.py -t "Full test set, libaom 3.13.1" -o libaom_full -e encoders/fullset.toml -s sources/fullset.toml \
  "Speed 6:libaom-s6" "Speed 7:libaom-s7" "Speed 8:libaom-s8" "Speed 9:libaom-s9"

# Use a wider range than the other plots, as this makes it easier to fit the 360p component into context
./plot_multires_components.py -t "Big Buck Bunny, tinyavif 1.1" -o components_tinyavif --range 20-100 \
  -e encoders/big_buck_bunny.toml -s sources/big_buck_bunny.toml \
  tinyavif big_buck_bunny

./plot_quality_curves.py -t "Big Buck Bunny, tinyavif 1.1" -o multires_tinyavif -e encoders/big_buck_bunny.toml -s sources/big_buck_bunny.toml \
  --multires-plot-1080p-curves \
  "tinyavif 1.1:tinyavif"

# Use a wider range than the other scripts, as this makes it easier to fit the 360p component into context
./plot_multires_components.py -t "Big Buck Bunny, libaom 3.13.1" -o components_libaom --range 20-100 \
  -e encoders/big_buck_bunny.toml -s sources/big_buck_bunny.toml \
  libaom-s6 big_buck_bunny

./plot_quality_curves.py -t "Big Buck Bunny, libaom 3.13.1" -o multires_libaom -e encoders/big_buck_bunny.toml -s sources/big_buck_bunny.toml \
  --multires-plot-1080p-curves \
  ":libaom-s6"

./plot_quality_curves.py -t "Full test set, stock settings" -o fullset-part1 -e encoders/fullset.toml -s sources/fullset.toml \
  --multires-plot-1080p-curves \
  "libaom 3.13.1:libaom-s6" "JPEGli 0.11.1:jpegli" "tinyavif 1.1:tinyavif"



# ... and the follow-up post:

# Skip the 1080p curve for this one to reduce crowding
./plot_quality_curves.py -t "Full test set, stock settings" -o fullset-part2 -e encoders/fullset.toml -s sources/fullset.toml \
  "libaom 3.13.1:libaom-s6" "SVT-AV1 3.1.2:svt-av1-s6" "rav1e 0.8.1:rav1e-s6" \
  "JPEG-XL 0.11.1:jxl-e7" "JPEGli 0.11.1:jpegli" "tinyavif 1.1:tinyavif"

./plot_size_vs_runtime.py -t "Full test set, stock settings" -o comparison -e encoders/fullset.toml -s sources/fullset.toml -r "libaom-s6" \
  "libaom 3.13.1:libaom-s2:libaom-s3:libaom-s4:libaom-s5:libaom-s6:libaom-s7:libaom-s8:libaom-s9" \
  "SVT-AV1 3.1.2:svt-av1-s2:svt-av1-s3:svt-av1-s4:svt-av1-s5:svt-av1-s6:svt-av1-s7:svt-av1-s8:svt-av1-s9:svt-av1-s10" \
  "rav1e 0.8.1:rav1e-s2:rav1e-s3:rav1e-s4:rav1e-s5:rav1e-s6:rav1e-s7:rav1e-s8:rav1e-s9:rav1e-s10" \
  "JPEG-XL 0.11.1:jxl-e2:jxl-e3:jxl-e4:jxl-e5:jxl-e6:jxl-e7:jxl-e8:jxl-e9:jxl-e10" \
  "JPEGli 0.11.1:jpegli" \
  "tinyavif 1.1:tinyavif"

# Optimizing settings for individual encoders
./plot_size_vs_runtime.py -t "Libaom settings" -o part2-libaom -e encoders/fullset.toml -s sources/fullset.toml -r "libaom-s6" --range 30-89 \
  "Stock, 8-bit:libaom-s2:libaom-s3:libaom-s4:libaom-s5:libaom-s6:libaom-s7:libaom-s8:libaom-s9" \
  "Stock, 10-bit:libaom-10bit-s2:libaom-10bit-s3:libaom-10bit-s4:libaom-10bit-s5:libaom-10bit-s6:libaom-10bit-s7:libaom-10bit-s8:libaom-10bit-s9" \
  "Stock, 12-bit:libaom-12bit-s2:libaom-12bit-s3:libaom-12bit-s4:libaom-12bit-s5:libaom-12bit-s6:libaom-12bit-s7:libaom-12bit-s8:libaom-12bit-s9" \
  "Tune=iq, 8-bit:libaom-iq-s2:libaom-iq-s3:libaom-iq-s4:libaom-iq-s5:libaom-iq-s6:libaom-iq-s7:libaom-iq-s8:libaom-iq-s9" \
  "Tune=iq, 10-bit:libaom-10bit-iq-s2:libaom-10bit-iq-s3:libaom-10bit-iq-s4:libaom-10bit-iq-s5:libaom-10bit-iq-s6:libaom-10bit-iq-s7:libaom-10bit-iq-s8:libaom-10bit-iq-s9" \
  "Tune=iq, 12-bit:libaom-12bit-iq-s2:libaom-12bit-iq-s3:libaom-12bit-iq-s4:libaom-12bit-iq-s5:libaom-12bit-iq-s6:libaom-12bit-iq-s7:libaom-12bit-iq-s8:libaom-12bit-iq-s9"

./plot_size_vs_runtime.py -t "SVT-AV1 settings" -o part2-svt-av1 -e encoders/fullset.toml -e encoders/svt-av1-hdr.toml -s sources/fullset.toml -r "svt-av1-s6" \
  "Stock, 8-bit:svt-av1-s2:svt-av1-s3:svt-av1-s4:svt-av1-s5:svt-av1-s6:svt-av1-s7:svt-av1-s8:svt-av1-s9:svt-av1-s10" \
  "Stock, 10-bit:svt-av1-10bit-s2:svt-av1-10bit-s3:svt-av1-10bit-s4:svt-av1-10bit-s5:svt-av1-10bit-s6:svt-av1-10bit-s7:svt-av1-10bit-s8:svt-av1-10bit-s9:svt-av1-10bit-s10" \
  "SVT-AV1-HDR, 8-bit:svt-av1-hdr-s2:svt-av1-hdr-s3:svt-av1-hdr-s4:svt-av1-hdr-s5:svt-av1-hdr-s6:svt-av1-hdr-s7:svt-av1-hdr-s8:svt-av1-hdr-s9:svt-av1-hdr-s10" \
  "SVT-AV1-HDR, 10-bit:svt-av1-hdr-10bit-s2:svt-av1-hdr-10bit-s3:svt-av1-hdr-10bit-s4:svt-av1-hdr-10bit-s5:svt-av1-hdr-10bit-s6:svt-av1-hdr-10bit-s7:svt-av1-hdr-10bit-s8:svt-av1-hdr-10bit-s9:svt-av1-hdr-10bit-s10"

./plot_size_vs_runtime.py -t "Rav1e settings" -o part2-rav1e -e encoders/fullset.toml -s sources/fullset.toml -r "rav1e-s6" \
  "Stock, 8-bit:rav1e-s2:rav1e-s3:rav1e-s4:rav1e-s5:rav1e-s6:rav1e-s7:rav1e-s8:rav1e-s9:rav1e-s10" \
  "Stock, 10-bit:rav1e-10bit-s2:rav1e-10bit-s3:rav1e-10bit-s4:rav1e-10bit-s5:rav1e-10bit-s6:rav1e-10bit-s7:rav1e-10bit-s8:rav1e-10bit-s9:rav1e-10bit-s10" \
  "Stock, 12-bit:rav1e-12bit-s2:rav1e-12bit-s3:rav1e-12bit-s4:rav1e-12bit-s5:rav1e-12bit-s6:rav1e-12bit-s7:rav1e-12bit-s8:rav1e-12bit-s9:rav1e-12bit-s10" \

# Skip the 1080p curve for this one to reduce crowding
./plot_size_vs_runtime.py -t "JPEGli/JPEG-XL settings" -o part2-jxl -e encoders/fullset.toml -s sources/fullset.toml -r "jxl-e7" \
  "JPEGli 0.11.1, 8-bit:jpegli" \
  "JPEGli 0.11.1, 16-bit:jpegli-16bit" \
  "JPEG-XL 0.11.1, 8-bit:jxl-e2:jxl-e3:jxl-e4:jxl-e5:jxl-e6:jxl-e7:jxl-e8:jxl-e9:jxl-e10" \
  "JPEG-XL 0.11.1, 16-bit:jxl-16bit-e2:jxl-16bit-e3:jxl-16bit-e4:jxl-16bit-e5:jxl-16bit-e6:jxl-16bit-e7:jxl-16bit-e8:jxl-16bit-e9:jxl-16bit-e10"

# Compare stock vs. optimized settings
./plot_size_vs_runtime.py -t "Stock settings" -o part2-results-stock -e encoders/fullset.toml -s sources/fullset.toml -r "libaom-s6" \
  "libaom 3.13.1:libaom-s2:libaom-s3:libaom-s4:libaom-s5:libaom-s6:libaom-s7:libaom-s8:libaom-s9" \
  "SVT-AV1 3.1.2:svt-av1-s2:svt-av1-s3:svt-av1-s4:svt-av1-s5:svt-av1-s6:svt-av1-s7:svt-av1-s8:svt-av1-s9:svt-av1-s10" \
  "rav1e 0.8.1:rav1e-s2:rav1e-s3:rav1e-s4:rav1e-s5:rav1e-s6:rav1e-s7:rav1e-s8:rav1e-s9:rav1e-s10" \
  "JPEG-XL 0.11.1:jxl-e2:jxl-e3:jxl-e4:jxl-e5:jxl-e6:jxl-e7:jxl-e8:jxl-e9:jxl-e10"

./plot_size_vs_runtime.py -t "Optimized settings" -o part2-results-optimized -e encoders/fullset.toml -e encoders/svt-av1-hdr.toml -s sources/fullset.toml \
                          -r "libaom-s6" \
  "libaom 3.13.1, tune=iq:libaom-10bit-iq-s2:libaom-10bit-iq-s3:libaom-10bit-iq-s4:libaom-10bit-iq-s5:libaom-10bit-iq-s6:libaom-10bit-iq-s7:libaom-10bit-iq-s8:libaom-10bit-iq-s9" \
  "SVT-AV1-HDR 3.1.2:svt-av1-hdr-10bit-s2:svt-av1-hdr-10bit-s3:svt-av1-hdr-10bit-s4:svt-av1-hdr-10bit-s5:svt-av1-hdr-10bit-s6:svt-av1-hdr-10bit-s7:svt-av1-hdr-10bit-s8:svt-av1-hdr-10bit-s9:svt-av1-hdr-10bit-s10" \
  "rav1e 0.8.1:rav1e-10bit-s2:rav1e-10bit-s3:rav1e-10bit-s4:rav1e-10bit-s5:rav1e-10bit-s6:rav1e-10bit-s7:rav1e-10bit-s8:rav1e-10bit-s9:rav1e-10bit-s10" \
  "JPEG-XL 0.11.1:jxl-e2:jxl-e3:jxl-e4:jxl-e5:jxl-e6:jxl-e7:jxl-e8:jxl-e9:jxl-e10"

# and gather up the graphs which were actually used in the blog posts
mkdir -p graphs/part1/ graphs/part2/

cp libaom_bbb/sizes_1080p.png                             graphs/part1/libaom_bbb.png
cp libaom_full/sizes_1080p.png                            graphs/part1/libaom_full.png

cp components_tinyavif/sizes.png                          graphs/part1/components_tinyavif.png
cp multires_tinyavif/sizes_multires.png                   graphs/part1/multires_tinyavif.png
cp components_libaom/sizes.png                            graphs/part1/components_libaom.png
cp multires_libaom/sizes_multires.png                     graphs/part1/multires_libaom.png

cp fullset-part1/sizes_1080p.png                          graphs/part1/fullset_sizes_1080p.png
cp fullset-part1/runtimes_1080p.png                       graphs/part1/fullset_runtimes_1080p.png
cp fullset-part1/sizes_multires.png                       graphs/part1/fullset_sizes_multires.png
cp fullset-part1/runtimes_multires.png                    graphs/part1/fullset_runtimes_multires.png

cp fullset-part2/sizes_multires.png                       graphs/part2/fullset_sizes_multires.png

cp comparison/size_vs_runtime_1080p.png                   graphs/part2/comparison_1080p.png
cp comparison/size_vs_runtime_multires.png                graphs/part2/comparison_multires.png

cp part2-libaom/size_vs_runtime_multires.png              graphs/part2/libaom.png
cp part2-svt-av1/size_vs_runtime_multires.png             graphs/part2/svt-av1.png
cp part2-rav1e/size_vs_runtime_multires.png               graphs/part2/rav1e.png
cp part2-jxl/size_vs_runtime_multires.png                 graphs/part2/jxl.png

cp part2-results-stock/size_vs_runtime_multires.png       graphs/part2/results-stock.png
cp part2-results-optimized/size_vs_runtime_multires.png   graphs/part2/results-optimized.png

fi

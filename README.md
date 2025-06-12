# Image compression comparison script

This script is a comparison to my blog posts on
[tinyavif](https://www.rachelplusplus.me.uk/blog/2025/03/lets-build-an-avif-encoder-part-3/)
and
[image compression more broadly](https://www.rachelplusplus.me.uk/blog/2025/03/blog/2025/06/evaluating-image-compression-tools/).
Its job is to compare a variety of image compression programs and plot various graphs.
For more details on the methodology, please see those two blog posts.

## Requirements

This script currently only works on Linux.

To run the `encode.py` and `plot_*.py` scripts, you will need to have `scipy` and `matplotlib`
installed. You will also of course need to install whichever encoders you want to compare.

To run the `generate_plots.sh` script, you will also need:
* A copy of tinyavif, version 1.1, checked out adjacent to this repository
* JPEGli and JPEG-XL versions 0.11.1
* libaom version 3.12.1
* SVT-AV1 version 3.0.2
* rav1e version 0.7.1
* libavif version 1.3.0
* Copies of all of the relevant input files (see below)

## Reproducing the blog posts

To reproduce the graphs used in the "Let's Build an AVIF Encoder" series, you will want to check out
the v1.0 tag, and follow the README in that version.

To reproduce the graphs used in the "Evaluating Image Compression Tools" blog post, you will need to
install all of the requirements listed above and then run `./generate_plots.sh`. This will generate
all of the relevant graphs in a directory called `graphs/`.

## Using individual scripts

The individual `encode.py` and `plot_*.py` can be run without arguments to see what arguments they
take; you can also look at `generate_plots.sh` to see how they're used in practice. But to
summarize, the overall process is:

* Run `encode.py` multiple times to run the encodes and store the results in an SQLite database, by
  default called `results.sqlite`. This should be done under standard benchmarking conditions, ie.
  with as little else running on the same machine as possible, and with Turbo Boost or equivalent
  disabled, to minimize noise in the runtime measurements.

* `plot_multires_components.py` plots the individual components which make up a single multires
  curve. It needs to be given a single encode set and a single input file, which must already be in
  the results database.

* `plot_quality_curves.py` plots size vs. quality and runtime vs. quality curves for any number of
  encode sets on a single graph, generating separate graphs for each individual resolution plus one
  combined multires graph.

* `plot_size_vs_runtime.py` plots size vs. runtime graphs for a potentially large number of encoder
  configurations. This takes a list of curves to plot, each in the format `name:label1:label2:...`.
  The specified encode labels are joined into a single curve, which is assigned the specified name
  in the graph legend.

## Input files

The input files used in the blog post are listed in `inputs.sha256sum`, along with their SHA256
checksums. These can be verified by running `sha256sum -c inputs.sha256sum`.

The original input files are:

* The short film Big Buck Bunny - the particular frame used is frame 231, which can be extracted
  using
  `ffmpeg -i <full video>.y4m -y -vf select=eq(n\\,231) -fps_mode passthrough -frames:v 1 big_buck_bunny_f231.y4m`

* The videos "aspen", "controlled_burn", "red_kayak", "rush_field_cuts", "speed_bag", "touchdown_pass", and "west_wind_easy"
  from the US NTIA, in 1080p resolution. These files use 4:2:2 subsampling, but the first frame was extracted and converted
  to 4:2:0 for use in this comparison. This can be reproduced as follows:
  `ffmpeg -i <original video>.y4m -y -vf format=yuv420p -frames:v 1 <name>_f0_420.y4m`

* The videos "crowd_run", "ducks_take_off", "in_to_tree", "old_town_cross", and "park_joy" from Sveriges Television AB,
  in 1080p resolution. The first frame from each file was extracted as follows:
  `ffmpeg -i <original video>.y4m -y -frames:v 1 <name>_f0_420.y4m`

* The videos "blue_sky", "pedestrian_area", "riverbed", "rush_hour", "station2", "sunflower", and "tractor" from Taurus Media Technik,
  in 1080p resolution. The first frame was extracted like for the previous group.

All of these files can be found on media.xiph.org.

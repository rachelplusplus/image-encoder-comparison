# General

* Explore different degrees of internal threading

* Find some animated content to add to the source list

* Decide whether to prune the source list to a smaller subset

* Set multires resolutions in the source list files

* Allow each encoder specification to set min/max qindex and #steps in between
  * Experiment with allowing non-linear point distributions, eg. biased toward the higher-quality end,
    and see how that affects the statistical quality of our results (once I implement that)

* Allow setting quality offsets (or even a full alternate list) per source file,
  to account for the fact that the quality parameter -> actual image quality mapping
  can vary depending on the input file

* Currently we can end up with inconsistent results if some encodes haven't been entered
  into the database (or if more than we need have been entered!).

  To fix this, the plot scripts need to explicitly determine which encodes they need, just like
  the encode script does now.

* Move BDRATE table printing into a separate script. Support all of:
  * Comparing multiple encoders on the same source files
  * Compare different test sets (for 8-bit vs. 10-bit comparisons)
  * Compare multires vs. full-res-only encoding

* Add encoder templates, or something along those lines, to simplify the encoder list

* Automatically extract required frames from source videos, instead of requiring the user to do it.

# Encode script

* Parallelize source scaling

* Save information about each encode set to the database, eg. when it was started and
  what parameters were used

* Switch to async in a single process, instead of using multiprocessing

* Work out exactly which versions of each source file we need, and only generate those

* Debug why WebP can't generate SSIMU2 > 60 with our current setup

# Plot scripts

* Include full-res-only curve as dotted lines on the multires size vs. runtime graph,
  like we do for the multires quality curve graphs?

* Calculate some kind of error bars for our curves
  Current idea: For each encoder, look at all of the (quality, size) pairs, for all of our encodes
  Fit some kind of piecewise curve, and measure the RMS error (~= standard deviation) relative to that curve

* Move to a more generic framework:
  * Modify plot_quality_curves.py and plot_multires_components.py to be able to plot several metrics vs. quality
    ({quality setting, clock/user/system runtime, memory usage, size, runtime} vs. {SSIMU2, Butteraugli})
  * Modify plot_size_vs_runtime.py to be able to plot other combinations of metrics

  As one example of how this is useful, plotting the input quality setting vs. output quality
  can help check things like monotonicity, linearity, and consistency of the quality parameter.
  See for example https://halide.cx/blog/consistency/

# Suggestions from other people

* Include JPEG-2000 in comparisons
  (inspired by https://www.youtube.com/watch?v=UGXeRx0Tic4)

* Read error bars paper: https://doi.org/10.1186/s13640-024-00630-7

# General

* Explore different degrees of internal threading

* Find some animated content to add to the source list

* Decide whether to prune the source list to a smaller subset

* Rename 'labels' to 'encode sets', as that's a clearer term for what they are

* Expand source definition files into a full config format (TOML?)
  * Set resolutions and quality values to use in this file. This will ensure that
    the scripts have a consistent idea of what parameters to use, rather than
    trying to infer things in a roundabout way

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

# Encode script

* Parallelize source scaling

* Cache scaled sources across multiple encode sets

* Save information about each encode set to the database, eg. when it was started and
  what parameters were used

* Allow specifying a quality offset as an extra parameter, to account for the fact that
  the quality parameter -> actual image quality mapping can vary depending on other encoder
  parameters, especially speed

* Switch to async in a single process, instead of using multiprocessing

# Plot scripts

* Include full-res-only curve as dotted lines on the multires size vs. runtime graph,
  like we do for the multires quality curve graphs?

* Calculate some kind of error bars for our curves
  One option: Use "jackknife resampling" (https://en.wikipedia.org/wiki/Jackknife_resampling),
  where we compute a bunch of curves with one sample point missed out, and calculate the variance
  of the resulting set of curves to estimate how sensitive our sample is to each point.

  This may need to be done on two levels: skipping individual encodes from the curve for one file,
  and skipping individual files when aggregating results

  Note: We'll either need to pin the two anchors just outside the quality range of interest,
  or have doubled anchors on each side so that we can skip either and still be able to
  interpolate across the full range of interest.

  This can be used to investigate the following:

  * Given two anchor points, ie. known quality parameters which result in scores just
    above and below the range of interest, how many in-between values do we need to
    get results which are stable enough to use for encoder development? (eg, +/- 0.1% BDRATE)

  * Some people have suggested biasing the intermediate quality parameters, so that we
    run more encodes at the high-quality end and fewer at the low-quality end
    (eg, https://giannirosato.com/blog/post/comparing-encoders/).
    Test to see if this helps, and what bias exponent is best.

# Suggestions from other people

* Include JPEG-2000 in comparisons
  (inspired by https://www.youtube.com/watch?v=UGXeRx0Tic4)

* Read error bars paper: https://doi.org/10.1186/s13640-024-00630-7

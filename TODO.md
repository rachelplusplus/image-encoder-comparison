* Encode script: Warn/error if different sources result in different numbers of resolutions

* Plot script: Work out the common set of sizes between all inputs
  * Warn if we don't have all sizes for all files

* Plot script: Add some way to plot a graph of all the individual curves which go into
  a single multires curve. This will only make sense to do for a single source at a time.

* Plot script: Write BDRATE tables to output files
  * Option to output as HTML tables?

* Plot script: Compute BDRATE of multires vs. single-res encodes for each label
  (BD-runtime is not particularly relevant in this case)

* Plot script: Allow chaining multiple sets of labelled encodes into a collection of
  BDRATE vs. speed curves? Would need to figure out a good command line syntax for
  specifying this

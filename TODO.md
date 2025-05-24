# General

* Find some animated content to add to the source list

* Decide whether to prune the source list to a smaller subset

# Encode script

* Parallelize the source scaling at the beginning

* Cache scaled sources?

* Check for each rescaled entry in the source table separately,
  so that we don't end up with a borked database if the script is aborted
  during source resizing

* Warn/error if different sources result in different numbers of resolutions

* Allow setting different quality ranges per input file
  Seems like some need higher/lower qualities than others to get the right SSIMU2 range

# Plot script

* Work out the common set of sizes between all inputs
  * Warn if we don't have all sizes for all files

* Add some way to plot a graph of all the individual curves which go into
  a single multires curve. This will only make sense to do for a single source at a time.

* Write BDRATE tables to output files
  * Option to output as HTML tables?

* Compute BDRATE of multires vs. single-res encodes for each label
  (BD-runtime is not particularly relevant in this case)

* Allow chaining multiple sets of labelled encodes into a collection of
  BDRATE vs. speed curves? Would need to figure out a good command line syntax for
  specifying this

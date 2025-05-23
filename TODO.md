* Encode script: Warn/error if different sources result in different numbers of resolutions

* Encode script: Support running encodes in parallel
  This will require either a better way of measuring child process runtime, to pick out
  the runtime of a single subprocess, or using the multiprocessing module so that we
  have one Python process overseeing each enocde

  * Start all of the highest-quality encodes first, then all of the next-highest quality
    encodes, and so on. This is because higher qualities generally take longer to encode, especially
    for encoders using RD optimization, and biasing toward starting the longest encodes first
    reduces the average amount of time where we're waiting for the last few encodes to finish,
    leading to a lower tail latency.

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

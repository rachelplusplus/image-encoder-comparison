# General

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

* Fold scripts together:
  Reason: Currently we can end up with inconsistent results if some encodes haven't been entered
  into the database (or if more than we need have been entered!).

  To fix this, the plot scripts need to explicitly determine which encodes they need, just like
  the encode script does now. At which point, we might as well have the plot script automatically
  launch any missing encodes, and do away with the separate encode script.

# Encode script

* Parallelize source scaling

* Cache scaled sources across multiple encode sets

* Check for each rescaled entry in the source table separately,
  so that we don't end up with a borked database if the script is aborted
  during source resizing

* Save information about each encode set to the database, eg. when it was started and
  what parameters were used

* Allow specifying a quality offset as an extra parameter, to account for the fact that
  the quality parameter -> actual image quality mapping can vary depending on other encoder
  parameters, especially speed

# Plot scripts

* Write BDRATE tables to output files
  * Option to output as HTML tables?

* Compute BDRATE of multires vs. single full-res encodes for each label

* Improve size vs. runtime curves:
  * Include full-res-only curve as dotted lines on the multires graph, like we do for the others

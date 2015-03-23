movie-thumbnails
================

The search for the most meaningful, crisp and clear thumbnail for a video using ffmpeg and OpenCV

# Installation

`brew tap homebrew/science`

`brew install opencv`

`pip install -r requirements.txt`


# How it Works

This script extracts a configurable amount of thumbnails from a movie source
with a high regard for scene-changes and then rates these on a number of
properties which can then be weighted to calculate an overall score by which
the thumbnails are sorted for relevance.

These propertes are:
* does the image contain a forward facing face as determined by a haar classification
algorithmn using opencv
* perceived brightness as detected by a luma transformation of the mean brightness
* color saturation as determined by the saturation and brightness values of three
dominant colors, determined by k-mean-clustering
* sharpness as determined by the standard-deviation of brighntess in an edge detected
version of the thumbnail
* contrast as determined by the range of the luminance extrema and their standard
deviation

## Pitfalls
This is a proof of concept and not optimized for speed or prettyness. Do not use
in production

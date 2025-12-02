# IIIF Downgrade

A super basic library for converting IIIF v3 manifests to v2.

## Why on earth would one do such a thing?

Certain applications ([Spotlight](https://github.com/projectblacklight/spotlight) until very recently) expect a v2 
manifest. This lets someone easily take a v3 manifest from elsewhere and convert it to v2.

## Warnings and Other Notes

This only handles the simplest of use cases like images or compound works of images.  IIIF Presentation v2 has a much more limited set of applications than v3.
This will likely create v2 manifests that are often invalid if you give it things it can't handle.
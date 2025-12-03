# IIIF Downgrade

A basic library for converting IIIF v3 manifests to v2.

## Why on earth would one do such a thing?

Certain applications ([Spotlight](https://github.com/projectblacklight/spotlight) until very recently) expect a v2 
manifest. This lets someone easily take a v3 manifest from elsewhere and convert it to v2.

## Warnings and Other Notes

This only handles the simplest of use cases like images or compound works of images.  IIIF Presentation v2 has a much more limited set of applications than v3.
This will likely create v2 manifests that are often invalid if you give it things it can't handle.

## How to Use

As a library:

```python
from iiif_downgrade import IIIFv3toV2Converter
import json

with open("fixtures/0e9016f7-f9dd-413f-b671-f75d181cbb5e.json") as f:
    data = json.load(f)

converter = IIIFv3toV2Converter(
    manifest=data,
    manifest_id="https://example.org/manifest/v2/123.json"
)

converter.convert()
converter.save("manifest-v2.json")
```

As a command line utility:

```
iiif_downgrade convert_directory -i fixtures
```

You can also find and replace ids and write to a specific directory:

```
iiif_downgrade convert_directory -i fixtures -o output --id_find "/manifest/" --id_replace "/v2_manifest/" 
```

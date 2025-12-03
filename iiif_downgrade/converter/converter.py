import json
from pathlib import Path


class IIIFv3toV2Converter:
    """
    Converts IIIF v3 manifest dictionaries to IIIF v2 format.
    Optionally accepts a new manifest ID.
    """

    def __init__(self, manifest: dict, manifest_id: str | None = None):
        """
        Parameters:
            manifest (dict): The IIIF v3 manifest as a Python dict.
            manifest_id (str | None): Optional ID to override v3 manifest['id'].
        """
        if not isinstance(manifest, dict):
            raise TypeError("manifest must be a dictionary")

        self.v3_manifest = manifest
        self.override_id = manifest_id
        self.v2_manifest = None

    def convert(self):
        """Convert the loaded IIIF v3 manifest to IIIF v2."""
        v3 = self.v3_manifest

        manifest_id = self.override_id or v3.get("id")

        self.v2_manifest = {
            "@context": "http://iiif.io/api/presentation/2/context.json",
            "@type": "sc:Manifest",
            "@id": manifest_id,
            "label": self._label_to_v2(v3.get("label")),
            "metadata": self._metadata_to_v2(v3.get("metadata", [])),
            "sequences": [
                {
                    "@type": "sc:Sequence",
                    "canvases": self._canvases_to_v2(v3.get("items", [])),
                }
            ],
        }
        if "structures" in v3 and v3["structures"]:
            ranges = self._structures_to_v2(v3["structures"])
            if ranges:
                self.v2_manifest["structures"] = ranges

        first_canvas = v3.get("items", [None])[0]
        if first_canvas and "thumbnail" in first_canvas:
            thumb = self._thumbnail_to_v2(first_canvas["thumbnail"])
            if thumb:
                self.v2_manifest["thumbnail"] = thumb

        if v3.get("behavior", "") != "":
            self.v2_manifest["viewingHint"] = v3.get("behavior")[0]

        return self.v2_manifest

    def save(self, output_path: str):
        """Save the IIIF v2 manifest to disk."""
        if not self.v2_manifest:
            raise RuntimeError("No v2 manifest to save. Run convert() first.")

        path = Path(output_path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.v2_manifest, f, indent=2, ensure_ascii=False)

    def _label_to_v2(self, label_obj):
        """Convert a v3-language map label to a v2-language string."""
        if isinstance(label_obj, dict):
            for lang, values in label_obj.items():
                if values:
                    return values[0]
        return ""

    def _metadata_to_v2(self, metadata_list):
        out = []
        for entry in metadata_list:
            label = self._label_to_v2(entry.get("label"))
            value = self._label_to_v2(entry.get("value"))
            out.append({"label": label, "value": value})
        return out

    def _canvases_to_v2(self, items):
        canvases = []
        for canvas in items:
            c = {
                "@id": canvas.get("id"),
                "@type": "sc:Canvas",
                "label": self._label_to_v2(canvas.get("label")),
                "height": canvas.get("height"),
                "width": canvas.get("width"),
                "images": self._annotations_to_v2(canvas),
            }
            canvases.append(c)
        return canvases

    def _annotations_to_v2(self, canvas):
        images = []
        for annotation_page in canvas.get("items", []):
            for anno in annotation_page.get("items", []):
                body = anno.get("body", {})
                images.append(
                    {
                        "@type": "oa:Annotation",
                        "motivation": "sc:painting",
                        "resource": {
                            "@id": body.get("id"),
                            "@type": "dctypes:Image",
                            "format": body.get("format"),
                            "height": body.get("height"),
                            "width": body.get("width"),
                        },
                        "on": canvas.get("id"),
                    }
                )
        return images

    def _thumbnail_to_v2(self, v3_thumbnail):
        """
        Convert a IIIF v3 thumbnail object to IIIF v2 format.

        Example v3 format:
        {
          "id": ".../full/!200,200/0/default.jpg",
          "type": "Image",
          "format": "image/jpeg",
          "service": [{
             "id": "...",
             "type": "ImageService3",
             "profile": "level1"
          }]
        }
        """
        if not v3_thumbnail:
            return None

        if isinstance(v3_thumbnail, list):
            v3_thumbnail = v3_thumbnail[0]

        service = None
        if "service" in v3_thumbnail and v3_thumbnail["service"]:
            svc = v3_thumbnail["service"][0]
            service = {
                "label": svc.get("label", "IIIF Image Service"),
                "profile": "http://iiif.io/api/image/2/level0.json",
                "@context": "http://iiif.io/api/image/2/context.json",
                "@id": svc.get("id")
            }

        return {
            "@id": v3_thumbnail.get("id"),
            "service": service
        }

    def _structures_to_v2(self, structures):
        """
        Convert IIIF v3 structures to IIIF v2 ranges.

        v3 structures are Range objects that organize canvases hierarchically.
        v2 uses the 'structures' property with sc:Range type.
        """
        if not structures:
            return []

        ranges = []
        for structure in structures:
            range_obj = self._convert_single_range(structure)
            if range_obj:
                ranges.append(range_obj)

        return ranges

    def _convert_single_range(self, structure):
        """
        Recursively convert a single Range object from v3 to v2.
        """
        range_obj = {
            "@id": structure.get("id"),
            "@type": "sc:Range",
            "label": self._label_to_v2(structure.get("label")),
        }

        if "behavior" in structure:
            behaviors = structure["behavior"]
            if isinstance(behaviors, list) and behaviors:
                range_obj["viewingHint"] = behaviors[0]

        if "items" in structure:
            canvases = []
            nested_ranges = []

            for item in structure["items"]:
                item_type = item.get("type", "")

                if item_type == "Canvas":
                    canvases.append(item.get("id"))
                elif item_type == "Range":
                    nested_range = self._convert_single_range(item)
                    if nested_range:
                        nested_ranges.append(nested_range)
                elif item_type == "SpecificResource":
                    source = item.get("source", {})
                    if source.get("type") == "Canvas":
                        canvases.append(source.get("id"))

            if canvases:
                range_obj["canvases"] = canvases
            if nested_ranges:
                range_obj["ranges"] = nested_ranges

        return range_obj


if __name__ == "__main__":
    with open("fixtures/with_ranges.json") as f:
        data = json.load(f)

    converter = IIIFv3toV2Converter(
        manifest=data,
        manifest_id="https://example.org/manifest/v2/123.json"
    )

    converter.convert()
    converter.save("manifest-v2-with-ranges.json")

    print("Done!")
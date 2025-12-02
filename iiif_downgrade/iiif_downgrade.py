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


if __name__ == "__main__":
    with open("fixtures/0e9016f7-f9dd-413f-b671-f75d181cbb5e.json") as f:
        data = json.load(f)

    converter = IIIFv3toV2Converter(
        manifest=data,
        manifest_id="https://example.org/manifest/v2/123.json"
    )

    v2 = converter.convert()
    converter.save("manifest-v2.json")

    print("Done!")
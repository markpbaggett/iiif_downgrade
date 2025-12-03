import click
from iiif_downgrade import IIIFv3toV2Converter
import os
import json


@click.group()
def cli() -> None:
    pass

@cli.command(
    "convert_directory", help="Convert a directory of manifests from v3 to v2"
)
@click.option(
    "--input_directory",
    "-i",
    help="The directory containing v3 manifests",
)
@click.option(
"--output_directory",
    "-o",
    help="The directory to write v2 manifests",
    default="output",
)
@click.option(
"--id_find",
    "-if",
    help="The pattern to find in the manifest id",
    default="",
)
@click.option(
"--id_replace",
    "-ir",
    help="The pattern to replace in the manifest id",
    default="",
)
def convert_directory(
        input_directory: str,
        output_directory: str,
        id_find: str,
        id_replace: str,
):
    for path, dirs, files in os.walk(input_directory):
        for filename in files:
            filepath = os.path.join(path, filename)
            with open(filepath, "rb") as f:
                data = json.load(f)
            current_manifest_id = data.get("id")
            new_manifest_id = current_manifest_id.replace(id_find, id_replace)
            converter = IIIFv3toV2Converter(
                manifest=data,
                manifest_id=new_manifest_id,
            )
            converter.convert()
            os.makedirs(output_directory, exist_ok=True)
            converter.save(f"{output_directory}/{new_manifest_id.split('/')[-1]}")

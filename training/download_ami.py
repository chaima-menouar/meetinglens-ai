from __future__ import annotations

import argparse
import shutil
import urllib.request
import zipfile
from pathlib import Path

AMI_MANUAL_URL = "https://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip"


def download_annotations(output_dir: str | Path = "data/raw/ami") -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "ami_public_manual_1.6.2.zip"
    extracted = output / "ami_public_manual_1.6.2"

    if extracted.exists() and any(extracted.iterdir()):
        print(f"AMI annotations already extracted at {extracted}")
        return extracted

    if not archive.exists():
        print(f"Downloading AMI manual annotations from {AMI_MANUAL_URL}")
        with urllib.request.urlopen(AMI_MANUAL_URL) as response, archive.open("wb") as handle:
            shutil.copyfileobj(response, handle)

    print(f"Extracting {archive}")
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(extracted)

    print(f"Ready: {extracted}")
    return extracted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download the official AMI manual annotations archive")
    parser.add_argument("--output", default="data/raw/ami")
    args = parser.parse_args()
    download_annotations(args.output)

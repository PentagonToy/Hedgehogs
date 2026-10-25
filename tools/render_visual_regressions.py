"""Render reference figures for visual inspection; tests never replace baselines."""
import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='Parent of the environment-specific image directory.')
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / 'src'))
    cases = runpy.run_path(str(ROOT / 'tests/visual/cases.py'))
    output = args.output.resolve() / cases['environment_key']()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f'Use a fresh output directory; references already exist: {output}')
    checksums = {}
    for name in cases['CASES']:
        image = output / f'{name}.png'
        cases['render'](name, image)
        checksums[name] = sha256(image.read_bytes()).hexdigest()
    digest = sha256()
    for source in sorted((ROOT / 'src/hedgehogs').rglob('*.py')):
        digest.update(source.relative_to(ROOT).as_posix().encode())
        digest.update(source.read_bytes())
    metadata = {'environment': cases['environment'](), 'dpi': cases['DPI'],
                'source_sha256': digest.hexdigest(), 'images': checksums}
    (output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    images = ''.join(f'<figure><figcaption>{escape(name)}</figcaption><img src="{name}.png" alt="{escape(name)}"></figure>' for name in checksums)
    (output / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Hedgehogs visual references</title><style>body{font:16px sans-serif}figure{display:inline-block;vertical-align:top}img{max-width:560px}</style>' + images)
    print(output)


if __name__ == '__main__':
    main()

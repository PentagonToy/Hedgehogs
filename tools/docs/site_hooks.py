"""Publish existing documents and artwork without duplicating their sources."""
import hashlib
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from mkdocs.structure.files import File

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/docs'))
from notebooks import render_notebook
from portable_markdown import enhance

REPOSITORY = 'https://github.com/PentagonToy/Hedgehogs'
ROUTES = {}
SOURCES = {}


def on_files(files, config):
    ROUTES.clear()
    SOURCES.clear()
    for file in list(files):
        if not file.is_documentation_page():
            continue
        source = (ROOT / 'docs' / file.src_uri).resolve()
        name = {'home.md': 'index.md', 'README.md': 'overview.md'}.get(file.src_uri, file.src_uri)
        if name != file.src_uri:
            files.remove(file)
            files.append(File.generated(config, name, abs_src_path=str(source)))
        ROUTES[source] = name
        SOURCES[name] = source
    for source in sorted((ROOT / 'others').rglob('*.svg')):
        name = 'assets/artwork/' + source.relative_to(ROOT / 'others').as_posix()
        ROUTES[source.resolve()] = name
        files.append(File.generated(config, name, abs_src_path=str(source)))
    for stem, title in [('plots', 'Plot examples'), ('tables', 'Table examples'), ('cli', 'Progress and terminal examples')]:
        source = ROOT / 'tutorials' / f'{stem}.ipynb'
        name = f'tutorials/{stem}.md'
        introduction = f'Run the cells in order after [installation](../installation.md). Code comes from [the original notebook]({REPOSITORY}/blob/main/tutorials/{stem}.ipynb); saved outputs are historical previews. Output paths are relative to the working directory.'
        if stem == 'tables':
            introduction += ' This example also requires pandas.'
        content = render_notebook(source, title, introduction, config, files)
        files.append(File.generated(config, name, content=content))
        SOURCES[name] = source
    ref = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    content = f'# Documentation source\n\nThis site was built from [{ref}]({REPOSITORY}/commit/{ref}). The PyPI release can differ from this source revision.\n'
    files.append(File.generated(config, 'versions.md', content=content))
    return files


def on_page_markdown(markdown, page, config, files):
    markdown = enhance(markdown)
    source = SOURCES.get(page.file.src_uri, ROOT / 'docs' / page.file.src_uri)

    def resolve(target, html=False):
        url = urlsplit(target)
        if url.scheme or url.netloc or not url.path:
            return target
        local = posixpath.normpath(posixpath.join(posixpath.dirname(page.file.src_uri), unquote(url.path)))
        if files.get_file_from_path(local) is None:
            destination = (source.parent / unquote(url.path)).resolve()
            local = ROUTES.get(destination)
            if local is None:
                if destination.is_relative_to(ROOT) and destination.exists():
                    kind = 'tree' if destination.is_dir() else 'blob'
                    return f'{REPOSITORY}/{kind}/main/{quote(destination.relative_to(ROOT).as_posix())}' + (f'#{url.fragment}' if url.fragment else '')
                raise ValueError(f'Unresolved repository link in {source}: {target}')
        target_file = files.get_file_from_path(local)
        query = url.query
        if local.endswith('.svg') and not query:
            query = 'revision=' + hashlib.sha256(Path(target_file.abs_src_path).read_bytes()).hexdigest()[:12]
        result = target_file.url_relative_to(page.file) if html else posixpath.relpath(local, posixpath.dirname(page.file.src_uri) or '.')
        return result + (f'?{query}' if query else '') + (f'#{url.fragment}' if url.fragment else '')

    markdown = re.sub(r'(\]\()([^\s)]+)(\))', lambda m: m[1] + resolve(m[2]) + m[3], markdown)
    return re.sub(r'(\b(?:src|href)=["\'])([^"\']+)(["\'])', lambda m: m[1] + resolve(m[2], html=True) + m[3], markdown)

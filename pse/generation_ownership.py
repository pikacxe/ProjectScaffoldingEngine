import hashlib
import json
import os
import shutil
import tempfile


MANIFEST_NAME = ".pse-generated.json"
IGNORED_PARTS = {"bin", "obj", ".git"}
IGNORED_FILES = {MANIFEST_NAME, "pse.manifest.json"}


def publish_generated_tree(staging_dir: str, output_dir: str, overwrite: bool):
    os.makedirs(output_dir, exist_ok=True)
    previous = load_manifest(output_dir)
    generated = collect_files(staging_dir)
    next_files = {}

    remove_stale_files(output_dir, previous, generated, overwrite)

    for relative_path, source_path in generated.items():
        destination = os.path.join(output_dir, relative_path)
        previous_hash = previous.get(relative_path)
        source_hash = file_hash(source_path)

        if should_replace(destination, previous_hash, source_hash, overwrite):
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(source_path, destination)
            next_files[relative_path] = source_hash
        elif os.path.exists(destination) and file_hash(destination) == source_hash:
            next_files[relative_path] = source_hash

    write_manifest(output_dir, next_files)


def collect_files(root):
    files = {}
    for current_root, directories, names in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_PARTS]
        for name in names:
            if name in IGNORED_FILES:
                continue
            path = os.path.join(current_root, name)
            relative_path = os.path.relpath(path, root)
            files[relative_path] = path
    return files


def should_replace(destination, previous_hash, source_hash, overwrite):
    if not os.path.exists(destination):
        return True
    if overwrite:
        return True
    if previous_hash and file_hash(destination) == previous_hash:
        return True
    return file_hash(destination) == source_hash


def remove_stale_files(output_dir, previous, generated, overwrite):
    for relative_path, previous_hash in previous.items():
        if relative_path in generated:
            continue
        path = os.path.join(output_dir, relative_path)
        if not os.path.exists(path):
            continue
        if overwrite or file_hash(path) == previous_hash:
            os.remove(path)
            remove_empty_parents(os.path.dirname(path), output_dir)


def remove_empty_parents(path, boundary):
    boundary = os.path.abspath(boundary)
    current = os.path.abspath(path)
    while current.startswith(boundary + os.sep) and current != boundary:
        if os.listdir(current):
            return
        os.rmdir(current)
        current = os.path.dirname(current)


def load_manifest(output_dir):
    path = os.path.join(output_dir, MANIFEST_NAME)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}
    return data.get("files", {})


def write_manifest(output_dir, files):
    path = os.path.join(output_dir, MANIFEST_NAME)
    data = {"version": 1, "files": dict(sorted(files.items()))}
    fd, temporary_path = tempfile.mkstemp(prefix=".pse-generated-", dir=output_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=True)
            handle.write("\n")
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()

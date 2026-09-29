import hashlib
import json
import os
import sys


def walk(root):
    result = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            with open(full, "rb") as handle:
                result[rel] = hashlib.sha256(handle.read()).hexdigest()
    return result


if __name__ == "__main__":
    root = sys.argv[1]
    json.dump(walk(root), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")

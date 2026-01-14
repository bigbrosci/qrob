#!/usr/bin/env python3
import os
import re
import sys
import shutil
from shutil import move
import tempfile
import subprocess

def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def main():
    # Make sure nebmake.pl is available
    if shutil.which("nebmake.pl") is None:
        die("nebmake.pl not found in PATH. Install VTST tools or add to PATH.")

    # List 2-digit directories in CWD
    pat = re.compile(r"^\d\d$")
    dirs = [d for d in os.listdir(".") if os.path.isdir(d) and pat.match(d)]
    if not dirs:
        die("No 2-digit image directories (00–99) found in current directory.")

    # Sort numerically ascending (00, 01, 02, ...)
    dirs = sorted(dirs, key=lambda s: int(s))

    # Basic sanity: expect at least two images for interpolation
    if len(dirs) < 2:
        die("Need at least two images to interpolate.")

    # Guardrail: if current images > 44, doubling risks > 88 (close to 100)
    if len(dirs) > 44:
        die("Bands more than 100 images are not supported at the moment.")

    # Ensure they’re contiguous starting from 00 (optional but helpful)
    first = int(dirs[0])
    last  = int(dirs[-1])
    expected = [f"{i:02d}" for i in range(first, last + 1)]
    if dirs != expected:
        print("Warning: directories are not contiguous; proceeding with the ones found.")

    # Step 1: rename existing images to even indices (reverse order to avoid clobbering)
    # e.g., '07' -> '14', '06' -> '12', ...
    for d in sorted(dirs, key=lambda s: int(s), reverse=True):
        newname = f"{int(d)*2:02d}"
        if newname != d:
            if os.path.exists(newname):
                die(f"Target directory '{newname}' already exists; aborting to avoid overwrite.")
            os.rename(d, newname)

    # After renaming, our even directories are:
    even_dirs = [f"{int(d)*2:02d}" for d in dirs]
    even_dirs = sorted(even_dirs, key=lambda s: int(s))

    # Step 2: create odd directories and fill with midpoints via nebmake.pl
    for i in range(len(even_dirs) - 1):
        left  = even_dirs[i]
        right = even_dirs[i + 1]
        mid   = f"{(int(left) + int(right)) // 2:02d}"  # odd index between them
        left_poscar  = os.path.abspath(os.path.join(left,  "POSCAR"))
        right_poscar = os.path.abspath(os.path.join(right, "POSCAR"))

        if not os.path.isfile(left_poscar):
            die(f"Missing {left_poscar}")
        if not os.path.isfile(right_poscar):
            die(f"Missing {right_poscar}")


        # Use nebmake.pl to generate 3 images (00, 01, 02) where 01 is the midpoint
        with tempfile.TemporaryDirectory() as td:
            # Run: nebmake.pl <POSCAR_A> <POSCAR_B> 3   → produces td/00, td/01, td/02
            try:
                subprocess.run(
                    ["nebmake.pl", left_poscar, right_poscar, "1"],
                    cwd=td,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                die(f"nebmake.pl failed between {left} and {right}:\n{e.stderr}")

            mid_src_dir = os.path.join(td, "01")
            move(mid_src_dir, mid)
        print(f"Created midpoint {mid}/POSCAR from {left}/POSCAR and {right}/POSCAR")

    print("Done. Doubled the number of images using nebmake.pl.")

if __name__ == "__main__":
    main()


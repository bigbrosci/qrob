#!/usr/bin/env python3
import os
import re
import sys
import shutil
from shutil import move
import tempfile
import subprocess

#usage: nebinsert.py img
#example:  nebinsert.py  04
#this will add one extra image between 03 and 04 as the new 04, while the old 04 becomes 05 and every image afterwards becomes 1 larger


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def main():
    ins = sys.argv[1] #insertion point
    
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

    # Step 1: rename existing images that's larger than argument to be one number higher
    for d in reversed(dirs):
      if int(d) >= int(ins):
        newname = f"{int(d)+1:02d}"
        if newname != d:
            if os.path.exists(newname):
                die(f"Target directory '{newname}' already exists; aborting to avoid overwrite.")
            os.rename(d, newname)
      # step 2: make the new image
      if int(d) == int(ins):
        left = f"{int(ins)-1:02d}"
        right = f"{int(ins)+1:02d}"
        mid = f"{int(ins):02d}"
        left_poscar  = os.path.abspath(os.path.join(left,  "POSCAR"))
        right_poscar = os.path.abspath(os.path.join(right, "POSCAR"))
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

    print("Done.")

if __name__ == "__main__":
    main()


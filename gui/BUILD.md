# Build Setup for Q-robot INCAR Generator

This directory contains the configuration files for building standalone executables.

## Files

- **build_spec.spec** - PyInstaller configuration file that defines how to bundle the Flask app
- **build.sh** - Local build script for creating executables on your machine

## GitHub Actions Workflow

The `.github/workflows/build.yml` file automatically:
1. Builds Windows executable on Windows runner
2. Builds macOS app on macOS runner  
3. Builds Linux executable on Ubuntu runner
4. Uploads all builds as artifacts
5. Creates releases with executables when you tag a version

## Building Locally

### Option 1: Using the build script (Linux/macOS)
```bash
cd gui
chmod +x build.sh
./build.sh all          # Build all three
# or
./build.sh linux        # Build only Linux
./build.sh macos        # Build only macOS
./build.sh windows      # Build only Windows
```

### Option 2: Manual build with PyInstaller
```bash
cd gui
pip install pyinstaller
pyinstaller build_spec.spec
```

The executables will be in the `dist/` folder.

## GitHub Actions Setup

1. Push your code to GitHub
2. The workflow automatically runs on every push to `main` or `develop` branches
3. Check the "Actions" tab in your GitHub repo to see build progress
4. Downloaded built executables from the "Artifacts" section

## Creating a Release

Tag your code and GitHub Actions will automatically create a release with all three executables:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

Then download the executables from the GitHub Release page.

## Distribution

Users can download:
- **Windows users**: `INCAR_Generator.exe` - Just run it, no installation needed
- **macOS users**: `INCAR_Generator.app` - Drag to Applications or run directly
- **Linux users**: `INCAR_Generator` - Run from terminal or add to PATH

No Python installation required for end users!

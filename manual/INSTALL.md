# q-robot Installation Instructions

This document provides step-by-step instructions to manually install q-robot. Follow these steps in order.

## Step 1: Download the Repository

Clone the q-robot repository from GitHub:

```bash
git clone https://github.com/bigbrosci/qrob.git
```

Alternatively, if you already have a local copy, you can pull the latest changes:

```bash
cd /path/to/qrob
git pull
```

## Step 2: Move the Folder to Your Desired Location

Move the cloned repository to your preferred installation path. We recommend placing it in one of the following locations:

- **Option A (Recommended):** `$HOME/Dropbox/bin/qrob`
- **Option B:** `$HOME/bin/qrob`  
- **Option C:** Any custom location of your choice

Example (using Option A):

```bash
# If you cloned to a temporary location, move it:
mv ~/Downloads/qrob ~/Dropbox/bin/qrob

# Or if it's already in the right place, you can skip this step
```

## Step 3: Update Your Shell Configuration File

Add the q-robot environment variables to your shell profile. Choose the appropriate file for your operating system:

- **Linux (Bash):** `~/.bashrc`
- **macOS (Zsh):** `~/.zshrc`
- **macOS (Bash):** `~/.bash_profile`
- **Windows (Git Bash):** `~/.bashrc`

### For Linux/macOS Bash/Zsh:

Open your shell profile file in a text editor and add the following lines:

```bash
# >>> q-robot settings >>>
export QHOME="/path/to/installation"
export ROBOT=$QHOME/qrob
export PATH=$PATH:$ROBOT/actions:$ROBOT/friends/vtstscripts-1040
export PYTHONPATH=$PYTHONPATH:$ROBOT/brain
# <<< q-robot settings <<<
```

Replace `/path/to/installation` with your actual installation path (e.g., `/home/username/Dropbox/bin` if you installed to `/home/username/Dropbox/bin/qrob`).

**Example for `/home/qli/Dropbox/bin/qrob`:**

```bash
# >>> q-robot settings >>>
export QHOME="/home/qli/Dropbox/bin"
export ROBOT=$QHOME/qrob
export PATH=$PATH:$ROBOT/actions:$ROBOT/friends/vtstscripts-1040
export PYTHONPATH=$PYTHONPATH:$ROBOT/brain
# <<< q-robot settings <<<
```

### For Windows (PowerShell):

If using PowerShell, add the following to your PowerShell profile (location depends on your setup):

```powershell
# >>> q-robot settings >>>
$env:ROBOT = "C:\path\to\qrob"
$env:Path = "$env:Path;${env:ROBOT}\actions;${env:ROBOT}\friends\vtstscripts-1040"
# <<< q-robot settings >>>
```

After editing, save the file and reload your shell:

```bash
source ~/.bashrc      # For Linux/Git Bash
source ~/.zshrc       # For macOS Zsh
source ~/.bash_profile # For macOS Bash
```

Or restart your terminal for the changes to take effect.

## Step 4: Set Up the Conda/Mamba Environment

q-robot has a Python environment configuration file. You can create a conda or mamba environment to match these dependencies.

### Check for the Environment File

The environment file should be located at:

```
/path/to/qrob/manual/qrob_env.yml
```

### Create the Environment

Choose the tool you have installed (mamba is recommended for speed):

**Using Mamba (recommended):**

```bash
mamba env create -f ~/Dropbox/bin/qrob/manual/qrob_env.yml
```

**Using Conda:**

```bash
conda env create -f ~/Dropbox/bin/qrob/manual/qrob_env.yml
```

This will create a conda environment named `qrob` with all required dependencies.

### Activate the Environment

When you want to use q-robot, activate the environment:

```bash
conda activate qrob
# or
mamba activate qrob
```

## Verification

After completing all steps, verify the installation:

```bash
# Check that ROBOT is set
echo $ROBOT

# Check that the directory exists
ls -la $ROBOT

# Verify PATH includes q-robot actions
echo $PATH | grep -o "[^:]*actions[^:]*"

# Activate the environment and test
conda activate qrob
python -c "import qrob; print('q-robot imported successfully')" # If applicable
```

## Troubleshooting

- **Environment variables not loading:** Make sure you reloaded your shell configuration with `source ~/.bashrc` (or appropriate file).
- **Command not found:** Verify the `ROBOT` variable is set and the path exists.
- **Conda/Mamba environment creation fails:** Check that your environment file is valid YAML and all dependencies are available.
- **Permission denied:** If scripts don't run, check file permissions: `chmod +x $ROBOT/actions_py/* $ROBOT/actions_bash/*`

## Notes

- The installation path can be customized to any location on your system.
- Store your installation in a location that won't be frequently moved or deleted.
- For collaborative work, consider using version control (git) to stay updated with changes.
- The conda environment is optional but recommended for consistent dependency management.

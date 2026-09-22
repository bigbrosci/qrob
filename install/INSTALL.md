# q-robot Installation Instructions

This document provides step-by-step instructions to manually install q-robot. Follow these steps in order.

## Step 1: Download the Repository

Clone the q-robot repository from GitHub:

```bash
mkdir ~/bin 
cd ~/bin 
git clone https://github.com/bigbrosci/qrob.git
```

## Step 2: Add the q-robot environment variables to your shell profile. Choose the appropriate file for your operating system:

- **Linux (Bash):** `~/.bashrc`
- **macOS (Zsh):** `~/.zshrc`

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

```bash
cat /path/to/qrob/manual/bashrc >> ~/.bashrc  # for Linux Bash
cat /path/to/qrob/manual/zshrc >> ~/.zshrc    # for macOS Zsh 
```


After editing, save the file and reload your shell:

```bash
source ~/.bashrc      # For Linux/Git Bash
source ~/.zshrc       # For macOS Zsh
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

**Using Conda:**

```bash
conda env create -f ~/Dropbox/bin/qrob/manual/qrob_env.yml
```

This will create a conda environment named `qrob` with all required dependencies.

### Activate the Environment

When you want to use q-robot, activate the environment:

```bash
conda activate qrob
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

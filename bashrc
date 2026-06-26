# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=1000
HISTFILESIZE=2000

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
#force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# colored GCC warnings and errors
#export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Add an "alert" alias for long running commands.  Use like so:
#   sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/home/qli/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/qli/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/home/qli/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/home/qli/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

#source /home/qiangli/intel/oneapi/setvars.sh  > /dev/null

alias p1='cd /home/qiangli/Projects/P1_cluster && ls '
#alias work='cd "/mnt/c/Users/lqlhz/OneDrive - UMass Lowell/Projects/P1_cluster/data_dft" && conda activate ase'
alias mkm='cd "/mnt/c/Users/lqlhz/OneDrive - UMass Lowell/Group_Infor/MKM_Cantera/"'
#alias faster='ssh -J u.ql152895@faster-jump.hprc.tamu.edu:8822 u.ql152895@login.faster.hprc.tamu.edu'
### G09
#ulimit -n 1048576 1048576
#export g16root=/Applications
#. $g16root/g16/bsd/g16.profile
#export GAUSS_SCRDIR=$g16root/temp/Scratch
alias gv='//home/qiangli/sw/gv/gview.sh '

### Cluster 
alias ccei='ssh -Y qli@squidward.che.udel.edu'
alias farber='ssh -Y  qli@farber.hpc.udel.edu'
alias caviness='ssh -X  qli@caviness.hpc.udel.edu'

alias mccei='sshfs qli@squidward.che.udel.edu: ~/ccei'
alias mfarber='sshfs qli@farber.hpc.udel.edu:/home/work/ccei_biomass/users/qli  ~/farber'
alias mcaviness='sshfs qli@caviness.hpc.udel.edu:/work/ccei_biomass/users/qli ~/caviness'
alias ucaviness='sudo umount  ~/caviness -l '

### Lvliang
alias lvliang='ssh iciq-lq@172.16.20.10 -X'
alias mlvliang='sshfs iciq-lq@172.16.20.10: ~/lvliang'
alias ulvliang='sudo umount ~/lvliang -l'

alias darwin='ssh qli@darwin.hpc.udel.edu -X'
alias mdarwin='sshfs qli@darwin.hpc.udel.edu:/lustre/ccei_biomass/users/2092/ ~/darwin'
alias udarwin='sudo umount darwin_qiangli -l'

### Expanse
alias expanse_qiangli='ssh qli9@login01.expanse.sdsc.edu -X'
alias mexpanse='sshfs qli9@login.expanse.sdsc.edu:/expanse/lustre/projects/del124/qli9/ ~/expanse'
alias uexpanse='sudo umount  expanse -l '

### FASTER
alias faster='ssh -J u.ql152895@faster-jump.hprc.tamu.edu:8822 u.ql152895@login.faster.hprc.tamu.edu'

#alias mfaster='sshfs login-faster:/scratch/user/u.ql152895 ~/faster'
## Darwin
#alias flc_darwin='ssh xsedeu3543@darwin.hpc.udel.edu' 
alias darwin_qiangli='ssh xsedeu3547@darwin.hpc.udel.edu'
alias mdarwin_qiangli='sshfs xsedeu3547@darwin.hpc.udel.edu:/lustre/xg-che220076/users/3547  ~/darwin_qiangli'


## Umass
#alias umass='ssh qli@10.0.0.30'
#alias mumass='sshfs qli@10.0.0.30:/home/qli/Desktop ~/umass'

## NERSC
alias nersc='ssh -l lqcata perlmutter.nersc.gov'
### DIY 
alias ..='cd ..'
alias cp='cp -r'
alias tsource='tmux source-file ~/.tmux.conf'

### Q_robot
export ROBOT="$HOME/bin/qrob"

for d in "$ROBOT"/actions_*; do
  [ -d "$d" ] || continue
  PATH="$PATH:$d"
done

export PATH="$PATH:$ROBOT/friends/vtstscripts-1040"
export PYTHONPATH="$PYTHONPATH:$ROBOT/brain"

export JMOL="/home/qli/bin/softs/jmol-16.3.51"
export PATH=$PATH:$JMOL
alias  jmol="$JMOL"/jmol.sh 

export VESTA="/home/qiangli/bin/VESTA-gtk3-x86_64"
export PATH=$PATH:$VESTA
alias  vesta=VESTA
alias  ssd='sudo mount -t drvfs D: ssd'
alias  sse='sudo mount -t drvfs E: sse'
alias  ssf='sudo mount -t drvfs F: ssf'
alias  des='cd $HOME/Desktop'
alias  pc='p4v */CONTCAR '
alias  a1="awk '{print \$1}' "
alias  af="awk '{print \$NF}' "
alias  fenergy=' grep "  without" OUTCAR'
alias  ld='ls -l|grep "^d"|wc -l'
alias  gi="grep 'f/i' OUTCAR"
alias  rsync='rsync --no-g --no-perms --no-owner '

ulimit -s unlimited

## Umass

alias uml='ssh  qiang_li_uml_edu@unity.rc.umass.edu'
alias muml='sshfs qiang_li_uml_edu@unity.rc.umass.edu:/home/qiang_li_uml_edu ~/uml'

alias go="grep '  without' OUTCAR"

# >>> Added by Spyder >>>
#alias spyder=/home/qiangli/.local/spyder-6/envs/spyder-runtime/bin/spyder
#alias uninstall-spyder=/home/qiangli/.local/spyder-6/uninstall-spyder.sh
# <<< Added by Spyder <<<
#
# export OPENAI_API_KEY="your-api-key-here"  # Set this locally in ~/.bashrc_local or via environment
export PATH="$PATH:/home/qli/opt/p4vasp"
alias p4v='/home/qli/opt/p4vasp/run-p4vasp.sh '
alias turning=' ssh rzhao2@turing.wpi.edu '
alias mturning='sshfs rzhao2@turing.wpi.edu: ~/turning'
alias uturning='sudo umount turning -l'

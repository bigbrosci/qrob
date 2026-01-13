#!/bin/bash -l
LOCKFILE=/tmp/automagician/$USER-lock
if [[ -f $LOCKFILE ]]; then
    echo "your automagician is currently running, in order to avoid race conditions insta-submit will wait another minute"
    exit 3
fi

DB=$WORK/../automagician.db
if [[ ! -f $DB ]]; then
    echo "no database! exiting"
    exit 1
fi

MACHINE=$(hostname | sed s/login[0-3]\.//g)
if [[ $MACHINE == "stampede2.tacc.utexas.edu" ]]; then
    SUBFILE="knl.mpi.slurm"
elif [[ $MACHINE == "frontera.tacc.utexas.edu" ]]; then
    SUBFILE="clx.mpi.slurm"
elif [[ $MACHINE == "ls6.tacc.utexas.edu" ]]; then
    SUBFILE="milan.mpi.slurm"
else
    echo "unknown host! exiting"
    exit 2
fi

for dir in `echo "select dir from insta_submit where machine_name = \"$MACHINE\";" | sqlite3 $DB`; do
    echo $dir
    cd $dir
    sbatch $SUBFILE # > /dev/null
done
echo "delete from insta_submit where machine_name = \"$MACHINE\";" | sqlite3 $DB

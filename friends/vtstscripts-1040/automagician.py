#!/usr/bin/env python

import cProfile
import inspect
import subprocess
import os
import time
import datetime
import gzip
import re
from os.path import exists
from optparse import OptionParser
import sqlite3
import socket
import traceback
import shutil
import sys

# there is a helper script am-cron-wrapper.sh

lockfile = "/tmp/automagician/" + os.environ["USER"] + "-lock"
lockdir = "/tmp/automagician"
db_name = "automagician.db"
automagic_remote_dir = "/automagician_jobs"
default_subfile_path_fri_halifax = "/home/kg33564/automagician-permanent/subfile-archive"
default_subfile_path_tacc = "/work2/08734/karan/automagician-slurm-templates"

global stop_submitting
global opt_jobs
global dos_jobs
global opt_queue
global dos_queue
global wav_queue
global sub_queue
global db
global home
global preliminary_results
global ssh
global scp
global machine
global tacc_queue_sizes
global tacc_queue_maxes
global hit_limit
global no_ssh
global no_fabric

no_fabric=False
try:
  import fabric
except:
  print("fabric unavailable")
  no_fabric=True

parser = OptionParser()
parser.add_option("-r","--register",action="store_true",dest="register",default=False,help="Process and add all calculations contained in the current directory and all its subdirectories to known_jobs.dat") # working
parser.add_option("-p","--process",action="store_true",dest="process",default=False,help="Check and re-process every job in unconverged_jobs.dat") # working
parser.add_option("-t","--test",action="store_true",dest="test",default=False,help="test the functions of this script without modifying original files or submitting jobs") # not fully implemented
parser.add_option("-s","--silent",action="store_true",dest="silent",default=False,help="supress output") # working
parser.add_option("--rsc","--reset_converged",action="store_true",dest="reset_converged",default=False,help="move all converged jobs back into unconverged ones") # working
parser.add_option("--rsa","--reset_all",action="store_true",dest="reset_all",default=False,help="visit all jobs recorded in known_jobs.dat, add it to unconverged or converged accordingly if missing") # working
parser.add_option("--cc","--clear_certificate",action="store_true",dest="clear_certificate",default=False,help="Remove the certificate given to converged jobs.") # working
parser.add_option("--ac","--archive_converged",action="store_true",dest="archive_converged",default=False,help="Permanently log converged jobs") # working
parser.add_option("--cpl","--continue_past_limit",action="store_true",dest="continue_past_limit",default=False,help="Once the job limit is hit, continue processing directory but don't submit")
parser.add_option("-l","--limit",action="store",dest="limit",type="int",default=99999,help="Stop this script if more than a number of jobs are in queue.") # working
parser.add_option("-b","--balance",action="store_true",dest="balance",default=False,help="Balance jobs between other machines") # working
parser.add_option("--rcmb",action="store_true",dest="rcmb_flag",default=False,help="Simply recreate cmbFE.dat and cmbXDATCAR at current working directory") # not fully implemented
parser.add_option("--dbplaintext",action="store_true",dest="dbplaintext_flag",default=False,help="Print all job status into a readable text file after finishing other commands") # not fully implemented
parser.add_option("--dbcheck",action="store_true",dest="dbcheck_flag",default=False,help="Check interaction with database without submitting any jobs") # not fully implemented
parser.add_option("--rjs",action="store_true",dest="resetjobstatus_flag",default=False,help="Reset all job statuses from convered to unconverged") # not fully implemented
parser.add_option("--db_debug",action="store_true",dest="db_debug_flag",default=False,help="Used for debugging job directories") # not fully implemented
parser.add_option("--delpwd",action="store_true",dest="delpwd_flag",default=False,help="Remove the present working directgory from database")

parser.parse_args()

#If opt_jobs is a dictionary, then we won't have the problem of matching substrings?
opt_jobs = {} # 0 converged 1 unconverged 2 err -1 running
dos_jobs = {} # opt dir, dos 0 done 1 nonexistent 2 err -1 running sc same
wav_jobs = {}
stop_submitting = False
opt_queue = []
dos_queue = []
wav_queue = []
sub_queue = []
tacc_queue_sizes = [0, 0, 0] # from 2 up
tacc_queue_maxes = [50, 0, 200] # stampede2 knl normal, frontera normal, ls6 normal respectively # no frontera allocation -> alloc 0
# note that ppl might have things queued into other queues--i think the max total is the same though [ik it is for stampede2 at least--no more than 50 in any queue on stampede2]
hit_limit = False
no_ssh = False

class opt_job:
  def __init__(self, status, home_machine, last_on):
    self.status = status
    self.home_machine = home_machine
    self.last_on = last_on

class dos_job:
  opt_dir = None

  def __init__(self, opt_id, sc_status, dos_status, sc_last_on, dos_last_on):
    self.opt_id = opt_id
    self.sc_status = sc_status
    self.dos_status = dos_status
    self.sc_last_on = sc_last_on
    self.dos_last_on = dos_last_on

class wav_job:
  opt_dir = None

  def __init__(self, opt_id, wav_status, wav_last_on):
    self.opt_id = opt_id
    self.wav_status = wav_status
    self.wav_last_on = wav_last_on

# a record of jobs that can no longer be found
class gone_job:
  opt_dir = None

class JobLimitError(Exception):
  def __init__(self):
    pass

def automagic_exit():
  subprocess.call(["rm", lockfile])
  if machine < 2 and not no_ssh:
    ssh.run("rm " + lockfile)
    ssh.close()
  exit()

def check_has_opt(files):
  calc_files = ["POSCAR","POTCAR","INCAR","KPOINTS",subfile] 
  for target_file in calc_files:
    if (target_file not in files):
      # sprint("nope!")
      return False
  return True

def delpwd():
  pwd = os.getcwd()
  db.execute("delete from opt_jobs where dir = '" + pwd + "'" )
  db.connection.commit()
  sprint(pwd ," is deleted from opt_jobs")

def get_machine_name(machine_number):
  return {
    0: "fri.oden.utexas.edu",
    1: "halifax.oden.utexas.edu",
    2: "stampede2.tacc.utexas.edu",
    3: "frontera.tacc.utexas.edu",
    4: "ls6.tacc.utexas.edu"
  }.get(machine_number, "localhost")

def get_machine_number():
  rm_login_node = re.compile("login[0-3]\.")
  machine_name = rm_login_node.sub("", socket.gethostname())
  return {
    "fri.oden.utexas.edu": 0,
    "halifax.oden.utexas.edu": 1,
    "stampede2.tacc.utexas.edu": 2, # TODO differentiate between knl, skx, icx
    "frontera.tacc.utexas.edu": 3,
    "ls6.tacc.utexas.edu": 4,
  }.get(machine_name, -1)


def ssh_scp_init():
  global ssh
  global scp
  global no_ssh
  
  if machine < 2:
    hostname = get_machine_name(1 - machine)
    if no_fabric:
      sprint("you need fabric for ssh to work")
      no_ssh = True
    else:
      try:
        ssh = fabric.Connection(user=os.environ['USER'],host=hostname,connect_kwargs={
          "key_filename":home+"/.ssh/automagician_id_rsa"
        },config=fabric.config.Config(overrides={
          "warn": True
        }))
        scp = fabric.transfer.Transfer(ssh)
        ssh.run("hostname")
      except:
        sprint("you need fri-halifax keys for ssh to work")
        no_ssh = True

  if not parser.values.balance:
    no_ssh = True

def write_lockfile():
  global machine

  if not os.path.isdir(lockdir):
    os.makedirs(lockdir)
    subprocess.run(["chmod", "777", lockdir])

  if machine < 2 and not no_ssh:
    if not ssh.run("test -d " + lockdir, warn=True, hide=True).ok:
      ssh.run("mkdir -p " + lockdir)

  if exists(lockfile):
    sprint("it looks like you already have an instance of automagician running--please wait for it to finish. thank you! :)")
    sprint("other automagician process's details:")
    subprocess.call(["cat", lockfile])
    sprint("if you'd like to override the lock, you can delete " + lockfile + " and rerun your process")
    exit()
  elif machine < 2 and not no_ssh and ssh.run("test -e " + lockfile, warn=True, hide=True).ok:
    sprint("it looks like you already have a remote instance of automagician running--please wait for it to finish. thank you! :)")
    sprint("other automagician process's details:")
    ssh.run("cat " + lockfile)
    sprint("if you'd like to override the lock, you can delete " + lockfile + " on the remote machine and rerun your process")
    exit()
  else:
    lockstring = "user:" + os.environ.get("USER") + " | machine:" + get_machine_name(machine) + " | pid:" + str(os.getpid()) + " | started at:" + str(datetime.datetime.now()) + "\n"
    with open(lockfile, 'w') as f:
      f.write(lockstring)
    if machine < 2 and not no_ssh:
      ssh.run("echo \"" + lockstring + "\" > " + lockfile)

def scp_get_dir(remote, local):
  # sprint("scp get dir time")
  for f in ssh.run("cd " + remote + "; find . -type f | cut -c 2-").stdout.split("\n"):
    if len(f) < 1:
      continue
    # sprint("getting " + remote + f + " to " + local + f)
    scp.get(remote + f, local + f)

def scp_put_dir(local, remote):
  # sprint("calling scp_put_dir from " + local + " to " + remote)

  cwd = os.getcwd()
  os.chdir(local)
  for f in subprocess.run(["find", ".", "-type", "f"], capture_output=True).stdout.decode("utf-8").split("\n"):
    if len(f) < 1:
      continue
    # sprint("trying to copy " + local + f[1:] + " to " + remote + f[1:])
    dirname = os.path.dirname(remote + f[1:])
    ssh.run("mkdir -p " + dirname)
    scp.put(local + f[1:], dirname)
  os.chdir(cwd)

def db_init(path):
  global db

  # if machine < 2 and not no_ssh:
  #   stat = ssh.run("stat -c %Y " + path, warn=True, hide=True)
  #   if stat.ok:
  #     other_db_last_modified = int(stat.stdout)
  #     stat = subprocess.run(["stat", "-c", "%Y", path], capture_output=True)
  #     if stat.ok:
  #       this_db_last_modified = int(stat.stdout)
  #       if other_db_last_modified > this_db_last_modified:
  #         scp.get(remote=path, local=path)

  db = sqlite3.connect(path).cursor()
  # TODO check columns of table are correct?
  has_opt = False
  has_dos = False
  has_wav = False
  has_gone = False
  has_insta_submit = False
  for table in db.execute("select name from sqlite_master where type='table'"):
    if table[0] == "opt_jobs":
      has_opt = True
    elif table[0] == "dos_jobs":
      has_dos = True
    elif table[0] == "wav_jobs":
      has_wav = True
    elif table[0] == "gone_jobs":
      has_gone = True
    elif table[0] == "insta_submit":
      has_insta_submit = True

  if not has_opt:
    db.execute("create table opt_jobs (dir text, status int, home_machine int, last_on int)")
  if not has_dos:
    db.execute("create table dos_jobs (opt_id int, sc_status int, dos_status int, sc_last_on int, dos_last_on int)")
  if not has_wav:
    db.execute("create table wav_jobs (opt_id int, wav_status int, wav_last_on int)")
  if not has_gone:
    db.execute("create table gone_jobs (dir text, status int, home_machine int, last_on int)")
  if not has_insta_submit:
    db.execute("create table insta_submit (dir text, machine_name text)")

def get_string_from_db(cmd):
  out = db.execute(cmd).fetchone()
  if out == None:
    return ""
  return str(out[0])

def sprint(*args):
  if not parser.values.silent:
    print(*args)

def get_subfile(machine):
  return {
    0: "fri.sub",
    1: "halifax.sub",
    2: "knl.mpi.slurm",
    3: "clx.mpi.slurm",
    4: "milan.mpi.slurm"
  }.get(machine)

def register():
  #calc_files = ["POSCAR","POTCAR","INCAR","KPOINTS",subfile] 
  # neb_dirs = [re.compile(".*?[Iini]", ".*?[Fin]", ".*?[Band]")]
  # ini, fin, dos, wav, sc, are now reserved directory names. these cannot be a substring of a directory name.
  exclude_regex = re.compile(".*?(?<!^/home)((/run\d*)|(/dos)|(/sc)|(/[Ii]ni)|(/[Ff]in)|(/wav))")
  NEB_paths_arr = []

  for job_dir, subdirs, files in os.walk(os.getcwd(), followlinks=True):
    if exclude_regex.match(job_dir):
      continue

    job_directory = job_dir.strip("\n")
    sprint("Registrator looking at " + '\x1b[0;49;34m'+ job_dir + '\x1b[0m')

    has_dos = False
    has_wav = False
    exclude = False
    if exists(job_dir+'/automagic_note'):
      with open(job_dir+'/automagic_note', "r") as f:
        for line in f:
          if line == "dos\n":
            has_dos = True
            break
          elif line == "wav\n":
            has_wav = True
            break
          elif line == "exclude\n":
            exclude = True
            break

    has_opt = check_has_opt(files)
    if not has_opt:
      continue
    #for target_file in calc_files:
    #  # sprint("checking if " + job_dir + " has file " + target_file)
    #  if (target_file not in files):
    #    # sprint("nope!")
    #    has_opt = False
    #    break

    dirs_lowercase = {item.lower() for item in subdirs}
    if ('band' in dirs_lowercase) and ('ini' in dirs_lowercase) and ('fin' in dirs_lowercase):
      print("Found a NEB job bundle")
      NEB_paths_arr.append(job_directory)
      # TODO find new solution for NEB logging
      sprint(f'NEB located at {job_directory}')
      continue # skip any further action for this root directory

    if has_opt:
      opt_queue.append(job_directory)
      if job_directory not in opt_jobs:
        opt_jobs[job_directory] = opt_job(1, machine, machine)
    if has_dos:
      dos_queue.append(job_directory)
      if job_directory not in dos_jobs:
        dos_jobs[job_directory] = dos_job(-1, 1, 1, machine, machine)
    if has_wav:
      wav_queue.append(job_directory)
      if job_directory not in wav_jobs:
        wav_jobs[job_directory] = wav_job(-1, 1, machine)

  process_queue()

def NEB_bundle_finder(dirs_lowercase):
  dirs_set = set(dirs_lowercase)


def grep_ll_out_convergence(ll_out):
  grep_retcode = subprocess.call(["grep", "reached required accuracy - stopping structural energy minimisation", ll_out])
  if grep_retcode == 0:
    return True
  else:
    return False
    
# This assumes that all converged calculations do not wrap up its last run
def determine_convergence(job_directory):
  # default
  # No CONTCAR and no ll_out is not converged
  os.chdir(job_directory)
  if exists("convergence_certificate"):
    return True
  if not ( exists(job_directory+"/CONTCAR") and exists(job_directory+"/ll_out") ):
    return False
  # use ll_out to determine convergence
  sprint("running vef.pl")
  subprocess.call("vef.pl",stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  if (grep_ll_out_convergence(job_directory+"/ll_out")):
  # if ("reached required accuracy - stopping structural energy minimisation" in ll_out.read()):
    # ISIF = 3 requires that jobs converge after one step
    if is_isif3(job_directory) == 1 :
      sprint("This is a bulk relaxation job")
      return determine_box_convergence(job_directory)
    return True
  else :
    return False

def determine_box_convergence(job_directory):
  sprint('determining box convergence for ' + job_directory)
  fedatname = job_directory+"/fe.dat"
  wcout = subprocess.check_output(["wc", "-l", fedatname]).decode()
  line_number = int(wcout.split()[0])
  if (line_number == 0):
    sprint("this calculation needs attention")
    return False
  elif (line_number == 1):
    sprint("box relaxation finished")
    return True
  else:
    sprint("number of lines in fe.dat more than 1, it is ", line_number)
    return False

# Determine if this job needs to be treated differently
def is_isif3(job_directory):
  isif3regex = re.compile("ISIF\s*=\s*3")
  with open(job_directory+"/INCAR", "r") as f:
    for line in f:
      if isif3regex.match(line):
        return True
  return False

def process_opt(job_directory):
  sprint("process_opt " + job_directory)
  if machine < 2 and not no_ssh:
    if opt_jobs[job_directory].last_on == 1 - machine:
      sprint("scping from other machine")
      try:
        shutil.rmtree(job_directory)
        scp_get_dir(home + automagic_remote_dir + job_directory, job_directory)
      except Exception as e:
        print(e)
        traceback.print_exc()
      opt_jobs[job_directory].last_on = machine

  os.chdir(job_directory)
  files = os.listdir()
  if not check_has_opt(files):
    sprint("No opt files found!")
    return
  else:
    sprint("Found opt files")
   
  if parser.values.clear_certificate and exists("convergence_certificate"):
    subprocess.call(["rm","/convergence_certificate"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)

  is_converged = False
  is_running = False
  try:
    sprint('checking if job is running')
    is_running = opt_jobs[job_directory].status == -1
  except KeyError:
    traceback.print_exc()
    sprint("is_running KeyError")
    pass

  if is_running:
    sprint("job is running, do nothing")
    step,force,energy = get_residueSFE(job_directory)
    add_preliminary_results(job_directory,step,force,energy)
  else:
    if exists(job_directory+"/ll_out"):
      if check_error(job_directory):
        sprint("job failed!")
        opt_jobs[job_directory].status = 2
        log_error(job_directory,home)
        fix_error(job_directory)
      if not exists(job_directory+"/CONTCAR") or os.path.getsize(job_directory+"/CONTCAR") == 0:
        qsub(job_directory)
      else:
        sprint("Determining convergence")
        is_converged = determine_convergence(job_directory)
        if is_converged:
          process_converged(job_directory)
        else:
          process_unconverged(job_directory)
    else:
      process_unconverged(job_directory)

def check_error(job_directory):
  lloutpath = job_directory+"/ll_out"
  grepout = subprocess.call(["grep", "I\ REFUSE\ TO\ CONTINUE\ WITH\ THIS\ SICK\ JOB", lloutpath])
  
  if grepout == 0:
    sprint("This job reported an error!")
    return True
  else: 
    return False

# generate a permanent error log  
def log_error(job_directory,home): # potentially create an error buffer and write the errors all at once in the end? potentially a bad idea in case of a crash though/not sure if the speedup would be non-negligible
  error_log = open(home+"/error_log.dat","a+")
  for error_message in get_error_message(job_directory):
    error_log.write(str(datetime.datetime.now())+"  "+job_directory+"  "+error_message+"\n")

def get_error_message(job_directory): # TODO replace with grep? run a test to see which is faster
  os.chdir(job_directory)
  ll_out = open('ll_out','r')
  messages=[]
  for line in ll_out:
    if ("ERROR" in line) or ("error" in line):
      messages.append(line)
  if len(messages) == 0:
    return "message not found!"  
  return messages

def fix_error(job_directory):
  os.chdir(job_directory)
  error_messages = get_error_message(job_directory)
  for error_message in error_messages:
    if parser.values.test:
      sprint(error_message)
      continue
    if "ZBRENT" in error_message :
      os.chdir(job_directory)
      if exists(job_directory+"/CONTCAR"):
        if os.path.getsize(job_directory+"/CONTCAR") != 0:
          wrap_up(job_directory)
      archive_ll_out()
      sprint("ll_out archived")
      qsub(job_directory)
      return None
    elif "number of potentials on File POTCAR incompatible with number" in error_message:
      os.chdir(job_directory)
      subprocess.call([home+'/kingRaychardsArsenal/sortpos.py'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
      subprocess.call([home+'/kingRaychardsArsenal/sogetsoftpbe.py'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
      archive_ll_out()
      qsub(job_directory)
      return None

  sprint("a fix was not attempted!")
  return None

def archive_ll_out():
  subprocess.call(['mv','ll_out','archive_stdout'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)

def archive_converged(home):
  subprocess.call(['mv',home+'/converged_jobs.dat',home+'/archive_converged.dat'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)

def reset_converged(home):
  with open(home+"/unconverged_jobs.dat", "a") as f:
    subprocess.call(["grep", "-e", "^\/", home+"/converged_jobs.dat"], stdout=f, stderr=subprocess.STDOUT)
  subprocess.call(["rm", home+"/converged_jobs.dat"])

def set_incar_tags(path, tags_dict):
  read_incar = open(path, "r")
  lines = read_incar.readlines()
  for i in range(0,len(lines)):
    tag = lines[i].strip().split("=")[0]
    try:
      new_val = tags_dict[tag]
      tags_dict[tag] = None
      lines[i] = tag + "=" + new_val + "\n"
    except KeyError:
      sprint("KeyError")
      traceback.print_exc()
      continue
  
  read_incar.close()
  
  write_incar = open(path, "w")
  write_incar.writelines(lines)
  
  more_lines = []
  for tag in tags_dict:
    val = tags_dict[tag]
    if val != None:
      more_lines.append(tag + "=" + val + "\n")
  
  write_incar.writelines(more_lines)
  write_incar.close()

def create_sc(job_directory):
  sprint("creating sc directory")
  cwd = os.getcwd()
  os.chdir(job_directory)
  subprocess.call(["mkdir", "sc"])
  subprocess.call(["cp", "INCAR", "KPOINTS", "POTCAR", subfile, "sc"])
  set_incar_tags("sc/INCAR", {
    "IBRION": "-1",
    "LCHARGE": ".TRUE.",
    "NSW": "0"
  })

  if exists("CONTCAR"):
    subprocess.call(["cp", "CONTCAR", "sc"])
  else:
    subprocess.call(["cp", "POSCAR", "sc"])
    
  qsub(job_directory + "/sc")
  os.chdir(cwd)

def create_dos_from_sc(job_directory):
  cwd = os.getcwd()
  os.chdir(job_directory+"/sc")
  subprocess.call(["mkdir", "../dos"])
  subprocess.call(["cp", "INCAR", "KPOINTS", "POTCAR", "CHGCAR", subfile, "../dos"])

  if exists("CONTCAR"):
    subprocess.call(["cp", "CONTCAR", "../dos"])
  else:
    subprocess.call(["cp", "POSCAR", "../dos"])
  
  set_incar_tags("../dos/INCAR", {
    "ICHARGE": "11",
    "LORBIT": "11"
  })

  qsub(job_directory + "/dos")
  cwd = os.getcwd()

def sc_is_complete(sc_dir):
  cwd = os.getcwd()
  os.chdir(sc_dir)
  if exists("CHGCAR"):
    last_modified = int(subprocess.check_output(["stat", "-c", "%Y", "CHGCAR"]))
    current_time = time.time()
    os.chdir(cwd)
    return current_time - last_modified > 120 # write stopped more than two minutes ago
  else:
    os.chdir(cwd)
    return False

def dos_is_complete(dos_dir):
  cwd = os.getcwd()
  os.chdir(dos_dir)
  if exists("DOSCAR"):
    last_modified = int(subprocess.check_output(["stat", "-c", "%Y", "DOSCAR"]))
    current_time = time.time()
    os.chdir(cwd)
    return current_time - last_modified > 120 # write stopped more than two minutes ago
  else:
    os.chdir(cwd)
    return False

def process_dos(job_directory):
  sprint("process_dos " + job_directory)

  if opt_jobs[job_directory].status != 0: # make parent converge first
    return

  sc_dir = job_directory+"/sc"
  if os.path.isdir(sc_dir):
    if sc_is_complete(sc_dir):
      dos_dir = job_directory+"/dos"
      if os.path.isdir(dos_dir):
        if dos_is_complete(dos_dir):
          dos_jobs[job_directory].sc_status = 0
          dos_jobs[job_directory].dos_status = 0
        elif check_error(dos_dir):
          dos_jobs[job_directory].sc_status = 0
          dos_jobs[job_directory].dos_status = 2
      else:
        create_dos_from_sc(job_directory)
        dos_jobs[job_directory].sc_status = 0
        dos_jobs[job_directory].dos_status = -1
    elif check_error(sc_dir):
      dos_jobs[job_directory].sc_status = 2
      dos_jobs[job_directory].dos_status = 1
      
  else:
    sprint("no sc_dir -> create_sc")
    create_sc(job_directory)
    dos_jobs[job_directory].sc_status = -1
    dos_jobs[job_directory].dos_status = 1

# Create a self-consistent calculation to get WAVECAR for later use
def create_wav(job_directory):
  cwd = os.getcwd()
  os.chdir(job_directory)
  subprocess.call(["mkdir", "wav"])
  subprocess.call(["cp", "INCAR", "KPOINTS", "POTCAR", subfile, "wav"])
  set_incar_tags("wav/INCAR", {
    "IBRION": "-1",
    "LWAVE": ".TRUE.",
    "NSW": "0"
  })

  if exists("CONTCAR"):
    subprocess.call(["cp", "CONTCAR", "sc"])
  else:
    subprocess.call(["cp", "POSCAR", "sc"])
    
  qsub(job_directory+"/wav")
  os.chdir(cwd)

def wav_is_complete(wav_dir):
  cwd = os.getcwd()
  os.chdir(sc_dir)
  if exists("WAVECAR"):
    last_modified = int(subprocess.check_output(["stat", "-c", "%Y", "WAVECAR"]))
    current_time = time.time()
    os.chdir(cwd)
    return current_time - last_modified > 120 # write stopped more than two minutes ago
  else:
    os.chdir(cwd)
    return False

def process_wav(job_directory):
  sprint("process_wav " + job_directory)

  if opt_jobs[job_directory].status != 0: # make parent converge first
    return

  wav_dir = job_directory+"/wav"
  if os.path.isdir(wav_dir):
    if wav_is_complete(wav_dir):
      wav_jobs[job_directory].wav_status = 0
    elif check_error(wav_dir):
      wav_jobs[job_directory].wav_status = 0
  else:
    sprint("no wav_dir -> create_wav")
    create_wav(job_directory)
    wav_jobs[job_directory].wav_status = -1

# Create a POSCAR with reduced size for WAVECAR calculation, potentially Bader as well.
# This won't work across boundary conditions. This is also assuming 
def trim_pos():
  print("WARNING: This is not designed to work for molecules across periodic boundaries!!!")
  if exists("CONTCAR"):
    with open("CONTCAR") as tmpfile:
      car = tmpfile.readlines()
  else:
    with open("POSCAR") as tmpfile: 
      car = tmpfile.readlines()
  if "Cartesian" in car[6]:
    coord_sys = "Cartesian"
    posline_num = 7
  elif "Cartesian" in car[7]:
    coord_sys = "Cartesian"
    posline_num = 8
  elif "Direct" in car[6]:
    coord_sys = "Direct"
    posline_num = 7
  elif "Direct" in car[7]:
    coord_sys = "Direct"
    posline_num = 8
  # First read in position lines, if in direct, convert to cartesian.
  # Line 7 for vasp-5, line 6 for vasp-4

  # Find min and max for x y z
  return None

def process_converged(job_directory):
  sprint("optimization converged! " + job_directory)
  subprocess.call("vef.pl", stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  try:
    #combine_XDAT_FE(job_directory)
    sprint("combine_XDAT_FE disabled due to bugs")
  except EOFError:
    traceback.print_exc()
    sprint("EOFError writting combfe")
    time.sleep(10)
    #combine_XDAT_FE(job_directory)
    sprint("combine_XDAT_FE disabled due to bugs")
  except:
    sprint("error in combining XDATCAR and fe.dat")
    traceback.print_exc()
  give_certificate()
  opt_jobs[job_directory].status = 0 # 0 -> status 0 means converged
    
def process_unconverged(job_directory):
  # First check if this is recorded as unconverged
  sprint("processing unconverged job at " + job_directory)

  opt_jobs[job_directory].status = 1 # 1 -> status 1 means unconverged
    
  # is CONTCAR empty? empty file have size 0. if not empty, wrap up if job is not running
  if not exists(job_directory+"/CONTCAR") or not exists(job_directory+"/OUTCAR"):
    sprint("contcar or outcar is missing -> resubmit")
    qsub(job_directory)
  elif(os.path.getsize(job_directory+"/CONTCAR") != 0) :
    sprint("contcar exists -> wrap up")
    wrap_up(job_directory)
    step,force,energy = get_residueSFE(job_directory) 
    add_preliminary_results(job_directory,step,force,energy)
    qsub(job_directory)
  else:
    sprint("else -> resubmit")
    qsub(job_directory)

def add_preliminary_results(job_directory,step,force,energy):
  preliminary_results.write(job_directory+"\n")
  preliminary_results.write("	"+str(step)+"	"+str(force)+"	"+str(energy)+"\n")

def combine_XDAT_FE(job_directory):
  os.chdir(job_directory)
  cmbX = open("cmbXDATCAR","w")
  cmbF = open("cmbFE.dat","w")
  dirList = [x for x in os.listdir("./") if x.startswith('run')]
  dirList.sort(key = lambda x: int(x[3:]))
  dirList.append(".")
  tlc = 0 # total line count
  initial = True # first XDATCAR file writes the header, apparently
  cwrite = True # can write ?

  for dir in dirList :
    if os.path.isdir(dir) :

      if os.path.isfile(os.path.join(dir,"XDATCAR.gz")):
        f = gzip.open(os.path.join(dir,"XDATCAR.gz"))
      elif os.path.isfile(os.path.join(dir,"XDATCAR")):
        f = open(os.path.join(dir,"XDATCAR"))
      else:
        # sprint("ERROR: No XDATCAR or XDATCAR.gz found!")
        continue

      for line in f:
        try:
          line = line.decode("utf-8")
        except AttributeError:
          sprint("AttributeError in combine_XDAT_FE")
          traceback.print_exc()
          continue
        except: 
          traceback.print_exc()
          continue

        if initial:
          continue

        if "Direct" in line and " 2\n" in line: 
          cwrite = True
          
        if cwrite: 
          cmbX.write(line)
        else:
          continue

      initial = False
      cwrite = False
      f.close()
      
      # now check for fe.dat
      if os.path.isfile(os.path.join(dir,"fe.dat")) :
        with open(os.path.join(dir,"fe.dat"), "r") as f:
          for line in f.readlines() :
            cmbF.write(str(tlc) + "  " + line)
            tlc = tlc + 1

  cmbX.close()
  cmbF.close()

def get_residueSFE(job_directory):
  #this function cannot be used before cmbFE can be created correctly
  return 0,0,0  

  os.chdir(job_directory) 
  cmbfepath = job_directory + "/cmbFE.dat"
  last_line = ""
  try:
    with open(cmbfepath, "r") as f:
      lines = f.readlines()
      last_line = lines[-1] if len(lines) > 0 else ""
  except:
    traceback.print_exc()
    combine_XDAT_FE(job_directory)
    time.sleep(10) # wait for files to be written
    with open(cmbfepath, "r") as f:
      lines = f.readlines()
      last_line = lines[-1] if len(lines) > 0 else ""
  f.close()
  if len(last_line) > 0:
    last_split = last_line.strip().split()
    return last_split[0],last_split[2],last_split[3]
  else:
    return 0,0,0

def classify_job_dir(job_dir):
  is_dos_regex = re.compile(".*?(?<!^/home)\/dos$")
  is_sc_regex = re.compile(".*?(?<!^/home)\/sc$")
  is_wav_regex = re.compile(".*?(?<!^/home)\/wav$")

  if is_dos_regex.match(job_dir):
    return "dos"
  elif is_sc_regex.match(job_dir):
    return "sc"
  elif is_wav_regex.match(job_dir):
    return "wav"
  else:
    return "opt"

def get_opt_dir(job_dir):
  return re.compile("\/(dos|sc|wav)$").sub("", job_dir)

def load_running_qsub_job(qstat_entry, is_remote=False):
  job_machine = 1 - machine if is_remote else machine

  partial_job_info = qstat_entry.split()
  qstat_id = partial_job_info[0]
  job_status = 2 if partial_job_info[4] == "Eqw" else -1
  full_job_info = ssh.run("qstat -j " + qstat_id, hide=True).stdout.split("\\n") if is_remote else subprocess.run(['qstat', '-j', qstat_id], capture_output=True).stdout.decode().split("\n")
  job_dir = None
  for line in full_job_info: # TODO make this use smart qstat formatting instead?
    if "workdir" in line:
      job_dir = line.split()[1]
      break
  
  if job_dir == None:
    job_status = 2

  if job_status == 2:
    ssh.run("qdel " + qstat_id) if is_remote else subprocess.call(["qdel", qstat_id])

  job_type = classify_job_dir(job_dir)
  if job_type in ["dos","sc"]:
    opt_dir = get_opt_dir(job_dir)
    if opt_dir not in dos_jobs:
      if is_remote:
        pass # ignore jobs that live over there--jobs that live here but are running there will already be in the database
      else:
        dos_jobs[opt_dir] = dos_job(-1, -1, -1, machine, machine)

    if job_type == "dos":
      dos_jobs[opt_dir].dos_status = job_status
      dos_jobs[opt_dir].dos_last_on = job_machine
    else:
      dos_jobs[opt_dir].sc_status = job_status
      dos_jobs[opt_dir].sc_last_on = job_machine
  elif job_type == "wav":
    opt_dir = get_opt_dir(job_dir)
    if opt_dir not in wav_jobs:
      if is_remote:
        pass
      else:
        wav_jobs[job_dir] = wav_job(-1, -1, machine)
    wav_jobs[opt_dir].wav_status = job_status
    wav_jobs[opt_dir].wav_last_on = job_machine
  else:
    try:
      if job_dir not in opt_jobs :
        if is_remote:
          pass
        else:
          opt_jobs[job_dir] = dos_job(job_status, machine, machine)
      else:
        opt_jobs[job_dir].status = job_status
        opt_jobs[job_dir].last_on = job_machine
    except:
      traceback.print_exc()
      print(job_dir," is a job type that automagician can't handle yet ")

def get_submitted_jobs_qsub():
  all_jobs = str(subprocess.check_output(['qstat'])).split('\\n')
  
  for job in all_jobs[2:-1]:
    load_running_qsub_job(job)

  if not no_ssh:
    remote_jobs = ssh.run("qstat", hide=True).stdout.split("\\n")
    for job in remote_jobs[2:-1]:
      print("job in remote_jobs is ", job)
      load_running_qsub_job(job, True)

def get_submitted_jobs_slurm():
  all_jobs = str(subprocess.check_output(['squeue', '-u', os.environ['USER'], '-o', "%A %t %Z"])).split("\n")
  for job in all_jobs[1:-1]:
    job = job.split()
    job_id = job[0]
    job_sstatus = job[1] # slurm's status code
    job_dir = job[2]
    
    job_status = -1
    
    if job_sstatus in ["BF", "CA", "F", "NF", "OOM", "TO"]:
      sprint("job id=" + job_id + ", dir=" + job_dir + " is in error")
      subprocess.call(["scancel", job_id])
      job_status = 2
    else:
      job_status = -1

    job_type = classify_job_dir(job_dir)
    if job_type in ["dos","sc"]:
      opt_dir = get_opt_dir(job_dir)
      if opt_dir not in dos_jobs:
        dos_jobs[opt_dir] = dos_job(-1, -1, -1, machine, machine)

      if job_type == "dos":
        dos_jobs[opt_dir].dos_status = job_status
        dos_jobs[opt_dir].dos_last_on = machine
      else:
        dos_jobs[opt_dir].sc_status = job_status
        dos_jobs[opt_dir].sc_last_on = machine
    elif job_type == "wav":
      opt_dir = get_opt_dir(job_dir)
      if opt_dir not in wav_jobs:
        wav_jobs[job_dir] = wav_job(-1, -1, machine)
      wav_jobs[opt_dir].wav_status = job_status
      wav_jobs[opt_dir].wav_last_on = job_machine
    else:
      if job_dir not in opt_jobs:
        opt_jobs[job_dir] = dos_job(job_status, machine, machine)
      else:
        opt_jobs[job_dir].status = status
        opt_jobs[job_dir].last_on = machine

def get_submitted_jobs():
  if machine == 0: # fri
    for job_dir in opt_jobs:
      opt_jobs[job_dir].status = abs(opt_jobs[job_dir].status) # make all -1s into 1s
    for job_dir in dos_jobs:
      dos_jobs[job_dir].sc_status = abs(dos_jobs[job_dir].sc_status)
      dos_jobs[job_dir].dos_status = abs(dos_jobs[job_dir].dos_status)
    for job_dir in wav_jobs:
      wav_jobs[job_dir].wav_status = abs(wav_jobs[job_dir].wav_status)
    get_submitted_jobs_slurm()
  elif machine == 1: #halifax
    for job_dir in opt_jobs:
      opt_jobs[job_dir].status = abs(opt_jobs[job_dir].status) # make all -1s into 1s
							# Ray: why?
    for job_dir in dos_jobs:
      dos_jobs[job_dir].sc_status = abs(dos_jobs[job_dir].sc_status)
      dos_jobs[job_dir].dos_status = abs(dos_jobs[job_dir].dos_status)
    for job_dir in wav_jobs:
      wav_jobs[job_dir].wav_status = abs(wav_jobs[job_dir].wav_status)
      get_submitted_jobs_slurm()
  else: # tacc
    for job_dir in opt_jobs: # TODO make more elegant
      if opt_jobs[job_dir].status == -1:
        tacc_queue_sizes[opt_jobs[job_dir].last_on - 2] = tacc_queue_sizes[opt_jobs[job_dir].last_on - 2] + 1
        if opt_jobs[job_dir].last_on == machine:
          opt_jobs[job_dir].status = 1
    for job_dir in dos_jobs:
      if dos_jobs[job_dir].sc_status == -1:
        tacc_queue_sizes[dos_jobs[job_dir].sc_last_on - 2] = tacc_queue_sizes[dos_jobs[job_dir].sc_last_on - 2] + 1
        if dos_jobs[job_dir].sc_last_on == machine:
          dos_jobs[job_dir].sc_status = 1
      if dos_jobs[job_dir].dos_status == -1:
        tacc_queue_sizes[opt_jobs[job_dir].last_on - 2] = tacc_queue_sizes[opt_jobs[job_dir].last_on - 2] + 1
        if dos_jobs[job_dir].dos_last_on == machine:
          dos_jobs[job_dir].dos_status = 1
    for job_dir in wav_jobs:
      if wav_jobs[job_dir].wav_status == -1:
        tacc_queue_sizes[wav_jobs[job_dir].wav_last_on - 2] = tacc_queue_sizes[wav_jobs[job_dir].wav_last_on - 2] + 1
        if wav_jobs[job_dir].wav_last_on == machine:
          wav_jobs[job_dir].wav_status = 1
    get_submitted_jobs_slurm()

def wrap_up(job_directory):
  sprint('wrapping up job')
  # first find name
  os.chdir(job_directory)
  directories = [f.path for f in os.scandir(job_directory) if f.is_dir()]
  runs = [ f for f in directories if "run" in f]
  # if no runs, wrap up into run0
  if( len(runs) == 0 ):
    if parser.values.test :
      sprint("this job would be wrapped up")
    else : 
      #subprocess.call(['/usr/local/vtstscripts/vfin.pl','run0'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
      subprocess.call(['vfin.pl','run0'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
      subprocess.call(['mv', 'll_out', 'run0'])
  else:
    # find the largest run
    largest_number = 0
    for run in runs:
      try:
        number = int(run.partition('run')[2])
        if( number >= largest_number):
          largest_number = number + 1
      except:
        traceback.print_exc()
        continue
    if not parser.values.test:
      largest_run = 'run'+str(largest_number)
      #subprocess.call(['/usr/local/vtstscripts/vfin.pl',largest_run],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
      subprocess.call(['vfin.pl',largest_run],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
      subprocess.call(['mv', 'll_out', largest_run])
      try:
        #combine_XDAT_FE(job_directory)
        sprint("combine_XDAT_FE disabled due to bugs")
      except EOFError:
        traceback.print_exc()
        time.sleep(10) # why?
        #combine_XDAT_FE(job_directory)
        sprint("combine_XDAT_FE disabled due to bugs")
    else :
      sprint("this job would be wrapped into run "+str(largest_number))
  optimizer_review(job_directory)

# if CG isn't working, use Damped molecular dynamics
def optimizer_review(job_directory):
  print('because bugs related to cmbFE, optimizer review is disabled.')
  return None

  os.chdir(job_directory)
  if not os.path.exists("./cmbFE.dat"):
    try:
      #combine_XDAT_FE(job_directory)
      sprint("combine_XDAT_FE disabled due to bugs")
    except EOFError:
      time.sleep(10)
      #combine_XDAT_FE(job_directory)
      sprint("combine_XDAT_FE disabled due to bugs")
  cmbFE = open('cmbFE.dat','r')       
  cmbFE_lines = cmbFE.readlines()
  if len(cmbFE_lines) < 200:
    return None
  INCAR = open("INCAR",'r')
  for INCAR_line in INCAR.readlines():
    if 'IBRION' in INCAR_line:
      INCAR_line = INCAR_line.strip("\n")
      # If energy went up, switch from CG to damped molecular dynamics
      if '2' in str(INCAR_line.split('=')[1]):
        sprint("IBRION adjustment from 2 to 3 is temporarily disabled")
        continue
        smallest = 0
        for i in range(1,10):
          #if float(cmbFE_lines('utf-8')[-i][4]) < smallest:
          try:
            cmbFE_lines[-i] = cmbFE_lines[-i].decode('utf-8')

          except:
            traceback.print_exc()
            #if cmbFE_lines cannot be read, do nothing
            pass
          cmbFE_lines[-i] = cmbFE_lines[-i].split()
          if float(cmbFE_lines[-i][4]) < smallest:
            smallest = float(cmbFE_lines[-i][4])
          else:
            # CG may not be stable enough. change INCAR
            INCAR.seek(0)
            INCAR_lines = INCAR.readlines()
            INCAR.close()
            if parser.values.test:
              sprint("INCAR will be modified")
              INCAR = open('testINCAR','w')
              for INCAR_line in INCAR_lines:
                if 'IBRION' in INCAR_line:
                  INCAR.write("IBRION = 3 \n")
                elif 'NSW' in INCAR_line:
                  INCAR.write("NSW = 200 \n")
                else:
                  INCAR.write(INCAR_line)
              INCAR.close()
              return None
            else:
              INCAR = open('INCAR','w')
              for INCAR_line in INCAR_lines:
                if 'IBRION' in INCAR_line:
                  INCAR.write("IBRION = 3 \n")
                  sprint("IBRION changed to 3")
                elif 'NSW' in INCAR_line:
                  INCAR.write("NSW = 200 \n")
                else:
                  INCAR.write(INCAR_line)
              INCAR.close()
              return None

      # If using damped molecular dynamics and force has been consistenly smaller than 0.2 eV/angstrom, change back to CG        
      elif '3' in str(INCAR_line.split('=')[1]):
        for i in range(1,10):
          try:
            cmbFE_lines[-i] = cmbFE_lines[-i].decode('utf-8')
          except:
            traceback.print_exc()
            pass
          cmbFE_lines[-i] = cmbFE_lines[-i].split()
          IBRION_3_TO_2_THRESHOLD_FORCE = 0.5
          if float(cmbFE_lines[-i][2]) > IBRION_3_TO_2_THRESHOLD_FORCE:
            return None
          else:
            INCAR.seek(0)
            INCAR_lines = INCAR.readlines()
            INCAR.close()
            INCAR = open('INCAR','w')
            for INCAR_line in INCAR_lines:
              if 'IBRION' not in INCAR_line:
                INCAR.write(INCAR_line)
              else:
                INCAR.write("IBRION = 2 \n")
                sprint("IBRION changed to 2")
            INCAR.close()
            return None

      else :
        return None

def qsub(job_directory):
  global hit_limit

  if parser.values.test:
    sprint("qsub is called by ", inspect.stack()[1].function)
    sprint("a job would have been submitted here")
  elif not hit_limit:
    os.chdir(job_directory)
    update_job_name(subfile)
    sub_queue.append(job_directory)
    
    # sprint("sub_queue is: " + str(sub_queue))

    if len(sub_queue) >= parser.values.limit:
      if parser.values.continue_past_limit:
        hit_limit = True
      else:
        raise JobLimitError()

def switch_subfile(job_dir, new_sub):
  os.chdir(job_dir)
  
  if not exists(subfile):
    return

  default_subfile_path = default_subfile_path_fri_halifax if machine < 2 else default_subfile_path_tacc

  subprocess.call(["cp",default_subfile_path + "/" + new_sub, new_sub])
  # os.remove(old_sub)
  update_job_name(new_sub)

def add_to_insta_submit(job_dir, machine):
  db.execute("insert into insta_submit values (?, ?)", (job_dir, machine))

def set_status_for_newly_submitted_job(job_dir, job_machine):
  job_type = classify_job_dir(job_dir)
  opt_dir = get_opt_dir(job_dir)

  #for now, status -1 is for special jobs that no longer need optimization
  if job_type == "sc":
    dos_jobs[opt_dir].sc_status = -1
    dos_jobs[opt_dir].sc_last_on = job_machine
  elif job_type == "dos":
    dos_jobs[opt_dir].dos_status = -1
    dos_jobs[opt_dir].dos_last_on = job_machine
  elif job_type == "wav":
    wav_jobs[opt_dir].wav_status = -1
    wav_jobs[opt_dir].wav_last_on = job_machine
  else:
    opt_jobs[opt_dir].status = -1
    opt_jobs[opt_dir].last_on = job_machine

def submit_queue():
  sprint("starting queue submit")
  if machine < 2: # fri-halifax
    num_to_sub = len(sub_queue)
    if not parser.values.balance:
      num_to_sub_there = 0
    else:
      other_subfile = get_subfile(1 - machine)
      this_machine_job_count = len(str(subprocess.run(["xqstat"], capture_output=True).stdout).split('\n'))
      other_machine_job_count = int(ssh.run("xqstat | wc -l", hide=True).stdout) if not no_ssh else 0
      diff_in_size = this_machine_job_count - other_machine_job_count
      num_to_sub_there = num_to_sub/2 + diff_in_size

    if not parser.values.balance:
      num_to_sub_there = 0
    elif no_ssh:
      num_to_sub_there = 0
    elif num_to_sub_there < 0:
      num_to_sub_there = 0
    elif num_to_sub_there > num_to_sub:
      num_to_sub_there = num_to_sub

    sprint("num to sub here is " + str(num_to_sub - num_to_sub_there) + ", num to sub there is " + str(num_to_sub_there))

    sub_queue_index = 0
    while sub_queue_index < num_to_sub_there:
      job_dir = sub_queue[sub_queue_index]
      switch_subfile(job_dir, other_subfile)
      new_loc = home + automagic_remote_dir + job_dir
      scp_put_dir(job_dir, new_loc)
      ssh.run("cd " + new_loc + " && qsub " + other_subfile)
      set_status_for_newly_submitted_job(job_dir, 1 - machine)  
      sub_queue_index = sub_queue_index + 1
        
    while sub_queue_index < num_to_sub:
      job_dir = sub_queue[sub_queue_index]
      os.chdir(job_dir)
      if machine >= 0:
        subprocess.call(["sbatch",subfile])
      else:
        subprocess.call(["qsub", subfile])
      set_status_for_newly_submitted_job(job_dir, machine)
      sub_queue_index = sub_queue_index + 1

  else: # tacc
    # sprint("tacc submit")
    num_to_sub = len(sub_queue)
    sprint("num to submit is " + str(num_to_sub))
    num_can_sub = [0,0,0]
    total_free_spaces = 0
    num_will_sub = [0,0,0]
    will_hit_limit = False
    
    for i in range(0, 3):
      num_can_sub[i] = tacc_queue_maxes[i] - tacc_queue_sizes[i]
      total_free_spaces = total_free_spaces + num_can_sub[i]
      
    if not parser.values.balance:
      total_free_spaces = num_can_sub[0]
      num_can_sub[1] = 0
      num_can_sub[2] = 0

    if total_free_spaces < num_to_sub:
      num_will_sub = num_can_sub
      will_hit_limit = True
    else:  
      for i in range(0, 3):
        if total_free_spaces == 0:
          continue
        num_will_sub[i] = round(num_can_sub[i] * num_to_sub/total_free_spaces)
        num_to_sub = num_to_sub - num_will_sub[i]
        total_free_spaces = total_free_spaces - num_can_sub[i]
        
      
    sub_queue_index = 0
    for i in range(0, 3):
      for j in range(0, num_will_sub[i]):
        job_dir = sub_queue[sub_queue_index]
        os.chdir(job_dir)
        if i + 2 == machine:
          subprocess.call(["sbatch", get_subfile(i + 2)])
        else:
          switch_subfile(job_dir, get_subfile(i + 2))
          add_to_insta_submit(job_dir, get_machine_name(i + 2))
        set_status_for_newly_submitted_job(job_dir, i + 2)
        sub_queue_index = sub_queue_index + 1

def update_job_name(subfile_name):
  script = open(subfile_name,"r")
  script_lines = script.readlines()
  script.close()
  with open(subfile_name,"w") as script:
    for line in script_lines:
      if "-J" in line:
        script.write("#SBATCH -J " + "AM_" + os.getcwd().replace("/","_") + "\n")
      else:
        script.write(line)

def give_certificate():
  subprocess.call(['touch','convergence_certificate'],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)

def check_certificate():
  if os.path.exists("./convergence_certificate"):
    return True
  return False

def process_queue():
  print("opt_queue is ", opt_queue)
  for job_dir in opt_queue:
    if exists(job_dir):
      process_opt(job_dir)
    else:
      print("job is no longer found at ", job_dir)
      db.execute('update opt_jobs set status = ?, last_on = ? where rowid = ?', (-10, opt_jobs[job_dir].last_on, old_entry)) 
      # status -10 is a job no longer found

  for job_dir in dos_queue:
    process_dos(job_dir)

  for job_dir in wav_queue:
    process_wav(job_dir)

def read_job_statuses():
  for job in db.execute('select * from opt_jobs'):
    opt_jobs[job[0]] = opt_job(job[1], job[2], job[3])
    
  for job in db.execute('select * from dos_jobs'):
    opt_id = job[0]
    opt_dir = get_string_from_db('select dir from opt_jobs where rowid = ' + str(opt_id))
    dos_jobs[opt_dir] = dos_job(job[0], job[1], job[2], job[3], job[4])

  for job in db.execute('select * from wav_jobs'):
    opt_id = job[0]
    opt_dir = get_string_from_db('select dir from opt_jobs where rowid = ' + str(opt_id))
    wav_jobs[opt_dir] = wav_job(job[0], job[1], job[2])

def write_job_statuses():
  for job_dir in opt_jobs:
    old_entry = get_string_from_db('select rowid from opt_jobs where dir = "' + job_dir + '"')
    if len(old_entry) > 0:
      db.execute('update opt_jobs set status = ?, last_on = ? where rowid = ?', (opt_jobs[job_dir].status, opt_jobs[job_dir].last_on, old_entry)) 
    else:
      db.execute('insert into opt_jobs values (?, ?, ?, ?)', (job_dir, opt_jobs[job_dir].status, opt_jobs[job_dir].home_machine, opt_jobs[job_dir].last_on))

  for job_dir in dos_jobs:
    opt_id = get_string_from_db('select rowid from opt_jobs where dir = "' + job_dir + '"')
    old_entry = get_string_from_db('select rowid from dos_jobs where opt_id = ' + opt_id)
    if len(opt_id) == 0:
      sprint("no opt_id??")
      automagic_exit()
    elif len(old_entry) > 0:
      db.execute('update dos_jobs set sc_status = ?, dos_status = ?, sc_last_on = ?, dos_last_on = ? where rowid = ?', (dos_jobs[job_dir].sc_status, dos_jobs[job_dir].dos_status, dos_jobs[job_dir].sc_last_on, dos_jobs[job_dir].dos_last_on, old_entry)) 
    else:
      db.execute('insert into dos_jobs values (?, ?, ?, ?, ?)', (opt_id, dos_jobs[job_dir].sc_status, dos_jobs[job_dir].dos_status, dos_jobs[job_dir].sc_last_on, dos_jobs[job_dir].dos_last_on))
  db.connection.commit()
  sprint("automagician.db updated")

  for job_dir in wav_jobs:
    opt_id = get_string_from_db('select rowid from opt_jobs where dir = "' + job_dir + '"')
    old_entry = get_string_from_db('select rowid from dos_jobs where opt_id = ' + opt_id)
    if len(opt_id) == 0:
      sprint("no opt_id??")
      automagic_exit()
    elif len(old_entry) > 0:
      db.execute('update wav_jobs set wav_status = ?, wav_last_on = ? where rowid = ?', (wav_jobs[job_dir].wav_status, wav_jobs[job_dir].wav_last_on, old_entry)) 
    else:
      db.execute('insert into wav_jobs values (?, ?, ?)', (opt_id, wav_jobs[job_dir].wav_status, wav_jobs[job_dir].wav_last_on))

  db.connection.commit()
  sprint("automagician.db updated")

def write_plain_text_db():
  sprint("writting out opt_jobs, ")
  f_opt_jobs = open(home+'/opt_jobs',"w")
  f_opt_jobs.write("status | home machine | last on | job name ")
  for job in db.execute('select * from opt_jobs order by dir'):
    for i in (job[1],job[2],job[3]) :
      f_opt_jobs.write("{0:>4}".format(str(i)))
    f_opt_jobs.write(job[0]+'\n')
  f_opt_jobs.close()

def db_check():
  opt_jobs = db.execute("select * from 'opt_jobs' order by dir")
  listOfDir_mult = [];
  for i in range(0, 6):
    for e in opt_jobs:
      listOfDir_mult.append(e)
    db = sqlite3.connect(path).cursor()
    opt_jobs = db.execute("select * from 'opt_jobs' order by dir")
  no_dups_mult = [*set(listOfDir_mult)]
  no_dups_mult.sort()
  # print("Looped 5 times")
  # for i in no_dups_mult:
  # print(i)
  # print()
  # print("Loop once")
  
  listOfDir_once = [];
  db = sqlite3.connect(path).cursor()
  opt_jobs = db.execute("select * from 'opt_jobs' order by dir")
  for e in opt_jobs:
    listOfDir_once.append(e)
  listOfDir_once.sort()
  
  if listOfDir_once == no_dups_mult:
    print("The lists are the same")
  else:
    print("The lists are NOT the same")
  
  
    
def reset_job_status():
  # opt_jobs = db.execute("select * from 'opt_jobs' order by dir")
  # for e in opt_jobs:
  #     print(e[1])
  db.execute("update opt_jobs set status = 1")
  db.connection.commit();
  print("Jobs have been updated")
  
def gone_job_check():
  db.execute("select count(name) from sqlite_master where type = 'table' and name = 'gone_jobs'")
  #if db.fetchone()[0] == 1:
  #  print("gone_jobs table already exists")
  #else:
  #  db.execute("create table gone_jobs (dir text)")
  #  print("gone_jobs table created")
  gone_jobs_list = []
  count = 0
  for direc in db.execute("select * from opt_jobs"):
    count += 1
  print("COUNT OF OPT_JOBS: ", count)
  #for direc in db.execute('select dir from opt_jobs where status = 1'):
  for direc in db.execute('select * from opt_jobs where status = 1'):
    if parser.values.db_debug_flag:
      if not exists(direc[0]):
        sprint(direc[0] + " no longer exists!")
      continue
    else:
      if not exists(direc[0]):
        sprint(direc[0] + " no longer exists!")
        print("direc is ", direc)
        gone_jobs_list.append([direc[0],direc[1],direc[2],direc[3]])
      
  for j in gone_jobs_list:
    print("Job to delete: " + j[0])
    #db.execute("insert into gone_jobs values (?)", (j,))
    db.execute('insert into gone_jobs values (?, ?, ?, ?)', (j[0],j[1],j[2],j[3]))
    db.execute("delete from opt_jobs where dir = (?)", (j[0],))
    del opt_jobs[j[0]]
  
  gone_jobs = db.execute("select * from gone_jobs")
  count = 0
  db.connection.commit()
  

def write_default_subfile_slurm_halifax(nodes=None,partition=None):
  if nodes == None:
    nodes = 1
  if partition == None:
    partition = 'amd'
  # jobs on halifax will use the amd partition by default if submitted through automagician
  subfile = open('amdhalifax.sub','w')
  subfile.write("#!/bin/bash\n")
  subfile.write("#SBATCH -J " + "AM_" + os.getcwd().replace("/","_") + "\n")
  subfile.write("#SBATCH -N " + nodes + "\n")
  subfile.write("#SBATCH -n " + nodes * 48 + "\n")
  subfile.write("#SBATCH --partition=" + partition + "\n")
  subfile.write("#SBATCH --output=ll_out\n")
  return

def main():
  global home
  global preliminary_results
  global subfile
  global machine

  try:
    machine = get_machine_number()
    home = os.environ['HOME'] if machine < 2 else os.environ['WORK'] + "/.."
    ssh_scp_init()
    sprint("no_ssh is " + str(no_ssh))
    write_lockfile()
    db_init(home + '/' + db_name)
    read_job_statuses()
    get_submitted_jobs()
    subfile = get_subfile(machine)
    preliminary_results = open(home+'/preliminary_results.dat','w') # TODO merge this with the other prelim results file
    gone_job_check()
    try:
      if parser.values.reset_converged: reset_converged(home)
      if parser.values.archive_converged: archive_converged(home)
      if parser.values.resetjobstatus_flag: reset_job_status()
      if parser.values.register:
        sprint("Registering all jobs in the current directory")
        register()
        #for direc in db.execute("select * from opt_jobs"):
        #  print(direc)
      if parser.values.process:
        sprint("Processing all unconverged optimization jobs")
        for direc in db.execute('select dir from opt_jobs where status = 1'):
          sprint("inspecting recorded job: ", direc[0])
          if parser.values.db_debug_flag:
            continue
          else:
            if not exists(direc[0]):
              sprint(direc[0] + " no longer exists!")
              continue
            else:
              process_opt(direc[0])

    except JobLimitError:
      sprint("JobLimitError")
      pass
    except Exception as e:
      sprint("error: cannot continue processing")
      sprint(traceback.format_exc())
    finally:
      sprint("done with command-specific stuff, time to submit!")
      submit_queue()
      write_job_statuses()
      if parser.values.delpwd_flag : delpwd()
      if parser.values.dbplaintext_flag : write_plain_text_db()
      preliminary_results.close()
      db.close()
      automagic_exit()

  except:
    if sys.exc_info()[0].__name__ == "SystemExit":
      exit()
    traceback.print_exc()
    submit_queue()
    write_job_statuses()
    sprint("interrupt received, lock released and job statuses written to sql db")
    automagic_exit()

main()

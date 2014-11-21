
from fabric.api import *
import benchmachines
import sys

env.hosts = [benchmachines.emulab]
swifttests = True
mongotests = True
sagetests = True
emulab = True



def run_microbench(testtype, size, runs, large=False):
  run('mkdir -p benchmark')
  print 'Runing %s Microbench. Size: %s, Runs: %s' % (testtype, size, runs)
  for f in ['microbench.py', 'benchmachines.py']:
    put(f, 'benchmark')
  with cd('benchmark'):
    run('mkdir -p binfiles')
    put('binfiles/%s.bin' % (size), 'binfiles')
    run('mkdir -p results/micro/%s/put' % (testtype))
    run('mkdir -p results/micro/%s/get' % (testtype))
    test = 'large' + testtype if large else testtype
    run('python microbench.py %s %s %d' % (test, size, int(runs)))
    local('mkdir -p results/micro/%s/put' % (testtype))
    local('mkdir -p results/micro/%s/get' % (testtype))
    get('results/micro/%s/put/%s.txt' % (testtype, size), 'results/micro/%s/put/%s.txt' % (testtype, size))
    get('results/micro/%s/get/%s.txt' % (testtype, size), 'results/micro/%s/get/%s.txt' % (testtype, size))


def clean_swift_repos():
  local('swift -A http://%s:8080/auth/v1.0 -U system:admin -K sagefs delete bench' % (env.host_string))


def swift_microbench(size='100k', runs='100', large=False):
  if size not in ['1k', '10k', '100k', '1m', '10m', '100m']:
    raise Exception('invalid size: %s' % (size))
  execute(run_microbench, 'swift', size, runs, large)
  execute(clean_swift_repos)


def swift_large_microbench():
  for r in xrange(10):
    execute(swift_microbench, '100m', (r+1)*10, True)


def mongo_microbench(size='1k', runs='100'):
  if size not in ['1k', '10k', '100k', '1m', '10m', '100m']:
    raise Exception('invalid size: %s' % (size))
  execute(run_microbench, 'mongo', size, runs)


def sageswift_microbench(size='1k', runs='100', large=False):
  if size not in ['1k', '10k', '100k', '1m', '10m', '100m']: 
    raise Exception('invalid size: %s' % (size))
  execute(run_microbench, 'sageswift', size, runs, large)

def sageswift_large_microbench():
  for r in xrange(10):
    execute(sageswift_microbench, '100m', (r+1)*10, True)


def sagemongo_microbench(size='1k', runs='100'):
  if size not in ['1k', '10k', '100k', '1m', '10m', '100m']: 
    raise Exception('invalid size: %s' % (size))
  execute(run_microbench, 'sagemongo', size, runs)


def local_microbench(size='1k', runs='100'):
  if size not in ['1k', '10k', '100k', '1m', '10m', '100m']: 
    raise Exception('invalid size: %s' % (size))
  execute(run_microbench, 'local', size, runs)


@hosts(['localhost'])
def microbench(testtype, size='1k', runs=10):
  if testtype == 'sageswift':
    sageswift_microbench(size, runs)
  elif testtype == 'sagemongo':
    sagemongo_microbench(size, runs)
  elif testtype == 'swift':
    swift_microbench(size, runs)
  elif testtype == 'mongo':
    mongo_microbench(size, runs)
  elif testtype == 'largeswift':
    swift_large_microbench()
  elif testtype == 'largesageswift':
    sageswift_large_microbench()
  elif testtype == 'local':
    local_microbench(size, runs)
  else:
    print 'Unknown Test Type %s' % (testtype)


@hosts(['localhost'])
def all_microbench():
  for test in ['sageswift', 'swift']: # 'local', 'mongo', 'sagemongo', 
    for size in ['1k', '10k', '100k', '1m', '10m']:
      microbench(test, size, 100)
  for test in ['largeswift', 'largesageswift']:
    microbench(test)
  microbench('local', '100m', 100)



def run_scalebench(test, maxfiles, iters):
  run('mkdir -p benchmark')
  print 'Runing %s Scalebench. Files: %s, Iters: %s' % (test, maxfiles, iters)
  for f in ['scalebench.py', 'benchmachines.py']:
    put(f, 'benchmark')
  with cd('benchmark'):
    run('mkdir -p binfiles')
    put('binfiles/1k.bin', 'binfiles')
    run('mkdir -p results/scale/%s' % (test))
    run('python scalebench.py %s %s %s' % (test, maxfiles, iters))
    local('mkdir -p results/scale/%s' % (test))
    get('results/scale/%s' % (test), 'results/scale/%s' % (test))
 

@hosts(['localhost'])
def scalebench(test, maxfiles='10000', iters='1'):
  execute(run_scalebench, test, maxfiles, iters)


@hosts(['localhost'])
def all_scalebench():
  for test in ['sageswift', 'swift', 'sagerandom', 'mongo', 'sagemongo']:
    scalebench(test)



def make_emulab_fs():
  sudo('mkdir -p /tmp/bench')
  sudo('chmod 777 /tmp/bench')
  sudo('/usr/testbed/bin/mkextrafs /tmp/bench')


def install_swift():
  local('cd ~/db/fs/swiftsetup && fab swift_install')

def install_mongo():
  sudo('apt-get install -y python-setuptools python-dev mongodb')
  sudo('killall mongod')
  sudo('mkdir -p /tmp/bench/mongo')
  sudo('chmod 777 /tmp/bench/mongo')
  sudo('mongod --fork --logpath /var/log/mongodb.log --dbpath /tmp/bench/mongo')
  sudo('easy_install pymongo')  

def install_sage():
  with settings(warn_only=True):
    run('git clone https://github.com/stredger/sagefs.git')
  with cd('sagefs'):
    sudo('python setup.py install')

def update_sage():
  with cd('~/sagefs'):
    run('git pull')
    sudo('python setup.py install')



def bench_setup():
  if emulab: make_emulab_fs()
  if swifttests: install_swift()
  if mongotests: install_mongo()
  if sagetests: install_sage()
  # run('mkdir -p ~/benchmark')
  # put('~/db/fs/benchmark/binfiles', '~/benchmark')
  

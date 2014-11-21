# These are just incase we do either swift only or mongo only 
#  tests and dont have these modules installed
try: import swiftclient
except ImportError, e: print 'Warning: Failed to import swiftclient'

try: 
  import pymongo
  import bson
except ImportError, e: print 'Warning: Failed to import pymongo'

import time
import sys
import benchmachines
import os
import errno
import shutil

# so we can find up to date sage
sys.path += ['..']
try: import sagefs
except ImportError, e: print 'Warning: Failed to import sagefs'


class BenchTester():
  def __init__(self):
    self.times = []

  def writeTimes(self, outfilename):
    f = open(outfilename, 'w+')
    s = 'starttime, endtime, elapsedtime\n'
    for t in self.times:
      s += '%f, %f, %f\n' % (t[0], t[1], t[2])
    f.write(s)
    f.close()

  def appendTimes(self, outfilename):
    f = open(outfilename, 'a+')
    s = ''
    for t in self.times:
      s += '%f, %f, %f\n' % (t[0], t[1], t[2])
    f.write(s)
    f.close()

  # subclasses should implement
  def putObject(self, filename, fd): pass
  def getObject(self, filename): pass

  def runPutMicroBench(self, filename, runs, timefn, startind=0):
    f = open(filename)
    for i in xrange(startind, runs):
      starttime = timefn()
      self.putObject(str(i), f)
      endtime = timefn()
      elapsedtime = endtime - starttime
      times = (starttime, endtime, elapsedtime)
      print times
      self.times.append(times)
      f.seek(0)
    f.close()
    
  def runGetMicroBench(self, runs, timefn, startind=0): 
    for i in xrange(startind, runs):
      starttime = timefn()
      self.getObject(str(i))
      endtime = timefn()
      elapsedtime = endtime - starttime
      times = (starttime, endtime, elapsedtime)
      print times
      self.times.append(times)



class SwiftTester(BenchTester):

  def __init__(self, host, user='system:admin', key='sagefs', container='bench'):
    self.host = host
    self.authurl = self.getAuthUrl()
    self.user = user
    self.key = key
    self.container = container
    self.sturl, self.token = self.getAuth()
    BenchTester.__init__(self)


  def getAuthUrl(self):
    return 'http://%s:8080/auth/v1.0' % (self.host)

  def getAuth(self):
    return swiftclient.get_auth(self.authurl, self.user, self.key)


  def init(self):
    swiftclient.put_container(self.sturl, self.token, self.container)


  def putObject(self, name, obj):
    swiftclient.put_object(self.sturl, self.token, self.container, name, obj)

  def getObject(self, name):
    swiftclient.get_object(self.sturl, self.token, self.container, name)




class MongoTester(BenchTester):

  def __init__(self, host, port=27017, database='bench', collection='bench'):
    self.client = pymongo.MongoClient() # use localhost and default port
    self.db = self.client[database]
    self.collection = self.db[collection]
    BenchTester.__init__(self)

  def create_select_record(self, name):
    return {'name':name}

  def create_insert_record(self, name, data):
    return {'name':name, 'data':data}

  def putObject(self, name, fd):
    data = fd.read()
    bsondata = bson.binary.Binary(data)
    insertrecord = self.create_insert_record(name, bsondata)
    self.collection.insert(insertrecord)

  def getObject(self, name):
    selectrecord = self.create_select_record(name)
    record = self.collection.find_one(selectrecord)
    # return record['data'] if record else None

  def clean(self):
    self.collection.remove()



class SageTester(BenchTester):

  def __init__(self, fstype):
    BenchTester.__init__(self)
    swifths = {'swift':sagefs.hosts.SwiftHost('localhost', 'admin', 'system', 'sagefs')}
    mongohs = {'mongo':sagefs.hosts.MongoHost('localhost', 'Sage', 'fsdata')}
    self.fs = sagefs.SageFS(swifths, mongohs)
    self.fstype = fstype

  def putObject(self, name, fd):
    data = fd.read()
    f = self.fs.open('/%s/%s' % (self.fstype, name), create=True)
    f.write(data, sync=False)
    f.close()

  def getObject(self, name):
    # this actually gets the file, but we want to read it  
    #  and get the data into python as the other benchmarks 
    #  end up with a bunch of readable data
    f = self.fs.open('/%s/%s' % (self.fstype, name))
    f.read()
    f.close()

  def clean(self):
    files = self.fs.list('/%s/' % (self.fstype))
    for f in files:
      # name = f['name'] if self.fstype == 'swift' else f
      self.fs.remove('/%s/%s' % (self.fstype, f))


class LocalTester(BenchTester):

  def __init__(self, tempdir='/tmp/bench/local'):
    BenchTester.__init__(self)
    self.tempdir = tempdir

  def init(self):
    try: os.mkdir(self.tempdir)
    except OSError, e:
      if not e.errno == errno.EEXIST or not os.path.isdir(self.tempdir): 
        raise e

  def getLocalName(self, name):
    return os.path.join(self.tempdir, name)  

  def putObject(self, name, fd):
    data = fd.read()
    f = open(self.getLocalName(name), 'w+')
    f.write(data)
    f.close()

  def getObject(self, name):
    fd = open(self.getLocalName(name))
    fd.read()
    fd.close()

  def clean(self):
    shutil.rmtree(self.tempdir)


def swiftPutTest(testsize, runs):
  t = SwiftTester(benchmachines.swifthost)
  t.init()
  t.runPutMicroBench('binfiles/%s.bin' % (testsize), runs, time.time)
  t.writeTimes('results/micro/swift/put/%s.txt' % (testsize))

def swiftGetTest(testsize, runs):
  t = SwiftTester(benchmachines.swifthost)
  t.runGetMicroBench(runs, time.time)
  t.writeTimes('results/micro/swift/get/%s.txt' % (testsize))

def swiftLargeFileTest(testsize, runs):
  t = SwiftTester(benchmachines.swifthost)
  t.init()
  t.runPutMicroBench('binfiles/%s.bin' % (testsize), runs, time.time, runs-10)
  t.appendTimes('results/micro/swift/put/%s.txt' % (testsize))
  w = SwiftTester(benchmachines.swifthost)
  w.runGetMicroBench(runs, time.time, runs-10)
  w.appendTimes('results/micro/swift/get/%s.txt' % (testsize))



def mongoPutTest(testsize, runs):
  t = MongoTester(benchmachines.mongohost)
  t.runPutMicroBench('binfiles/%s.bin' % (testsize), runs, time.time)
  t.writeTimes('results/micro/mongo/put/%s.txt' % (testsize))

def mongoGetTest(testsize, runs):
  t = MongoTester(benchmachines.mongohost)
  t.runGetMicroBench(runs, time.time)
  t.writeTimes('results/micro/mongo/get/%s.txt' % (testsize))
  t.clean()



def sageSwiftPutTest(testsize, runs):
  t = SageTester('swift')
  t.runPutMicroBench('binfiles/%s.bin' % (testsize), runs, time.time)
  t.writeTimes('results/micro/sageswift/put/%s.txt' % (testsize))  

def sageSwiftGetTest(testsize, runs):
  t = SageTester('swift')
  t.runGetMicroBench(runs, time.time)
  t.writeTimes('results/micro/sageswift/get/%s.txt' % (testsize))
  t.clean()

def sageSwiftLargeFileTest(testsize, runs):
  t = SageTester('swift')
  t.runPutMicroBench('binfiles/%s.bin' % (testsize), runs, time.time, runs-10)
  t.appendTimes('results/micro/sageswift/put/%s.txt' % (testsize))
  w = SageTester('swift')
  w.runGetMicroBench(runs, time.time, runs-10)
  w.appendTimes('results/micro/sageswift/get/%s.txt' % (testsize))
  w.clean()



def sageMongoPutTest(testsize, runs):
  t = SageTester('mongo')
  t.runPutMicroBench('binfiles/%s.bin' % (testsize), runs, time.time)
  t.writeTimes('results/micro/sagemongo/put/%s.txt' % (testsize))  

def sageMongoGetTest(testsize, runs):
  t = SageTester('mongo')
  t.runGetMicroBench(runs, time.time)
  t.writeTimes('results/micro/sagemongo/get/%s.txt' % (testsize))
  t.clean()



def localPutTest(testsize, runs):
  t = LocalTester()
  t.init()
  t.runPutMicroBench('binfiles/%s.bin' % (testsize), runs, time.time)
  t.writeTimes('results/micro/local/put/%s.txt' % (testsize))

def localGetTest(testsize, runs):
  t = LocalTester()
  t.runGetMicroBench(runs, time.time)
  t.writeTimes('results/micro/local/get/%s.txt' % (testsize))
  t.clean()


if __name__ == '__main__':
  try:
    testsize = sys.argv[2]
    runs = int(sys.argv[3])
  except Exception, e:
    testsize = '1k'
    runs = 10
  testtype = sys.argv[1]

  if testtype == 'sageswift':
    sageSwiftPutTest(testsize, runs)
    sageSwiftGetTest(testsize, runs)
  elif testtype == 'sagemongo':
    sageMongoPutTest(testsize, runs)
    sageMongoGetTest(testsize, runs)
  elif testtype == 'swift':
    swiftPutTest(testsize, runs)
    swiftGetTest(testsize, runs)
  elif testtype == 'mongo':
    mongoPutTest(testsize, runs)
    mongoGetTest(testsize, runs)
  elif testtype == 'largeswift':
    swiftLargeFileTest(testsize, runs)
  elif testtype == 'largesageswift':
    sageSwiftLargeFileTest(testsize, runs)
  elif testtype == 'local':
    localPutTest(testsize, runs)
    #localGetTest(testsize, runs)
  else:
    print 'Unknown Test Type %s' % (testtype)

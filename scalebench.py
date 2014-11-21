
import time
import sys
import benchmachines
import os

# so we can find up to date sage
sys.path += ['..']
import sagefs

import swiftclient
import pymongo
import bson



class FakeFD():
  def write(self, *args, **kwargs): pass
  def close(self): pass

class FakeFS():

  def __init__(self):
    self.sleeptime = 0
    self.sleepinc = 0.05

  def open(self, *args, **kwargs):
    time.sleep(self.sleeptime)
    self.sleeptime += self.sleepinc
    return FakeFD()

  def list(self, *args, **kwargs):
    time.sleep(self.sleeptime)
    return ['a']*10

  def remove(self, *args, **kwargs):
    time.sleep(self.sleeptime)
    self.sleeptime -= self.sleepinc



class ScalabilityTester():
  def __init__(self, maxfiles=1000, iterations=2, timefn=time.time):
    self.listtimes = [[None]*iterations for i in xrange(maxfiles)]
    self.createtimes = [[None]*iterations for i in xrange(maxfiles)]
    self.removetimes = [[None]*iterations for i in xrange(maxfiles)]
    self.timefn = timefn
    self.iterations = iterations
    self.curriteration = 0
    self.maxfiles = maxfiles
    self.filecount = 0

  def writeHeaders(self, fd):
    s = 'iterations=%d, maxfiles=%d\n' % (self.iterations, self.maxfiles)
    s += 'starttime, endtime, elapsedtime\n'
    fd.write(s)

  def appendTimes(self, times, fd):
    s = ''
    for t in times:
      s += '%f, %f, %f\n' % (t[0], t[1], t[2])
    fd.write(s)

  def writeAllTimes(self, outfilename, timeslist):
    fd = open(outfilename, 'w+')
    self.writeHeaders(fd)
    for times in timeslist:
      self.appendTimes(times, fd)
    fd.close()


  # subclasses must implement these
  def list(self): pass
  def create(self, fname, data): pass
  def remove(self, fname): pass


  def listTest(self):
    starttime = self.timefn()
    self.list()
    endtime = self.timefn()
    elapsedtime = endtime - starttime
    times = (starttime, endtime, elapsedtime)
    # print 'list: %f, %f, %f' % (times[0], times[1], times[2])
    self.listtimes[self.filecount][self.curriteration] = times    

  def createTest(self, fname, data):
    starttime = self.timefn()
    self.create(fname, data)
    endtime = self.timefn()
    elapsedtime = endtime - starttime
    times = (starttime, endtime, elapsedtime)
    # print 'create: %f, %f, %f' % (times[0], times[1], times[2])
    self.createtimes[self.filecount][self.curriteration] = times 

  def removeTest(self, fname):
    starttime = self.timefn()
    self.remove(fname)
    endtime = self.timefn()
    elapsedtime = endtime - starttime
    times = (starttime, endtime, elapsedtime)
    # print 'remove: %f, %f, %f' % (times[0], times[1], times[2])
    self.removetimes[self.filecount][self.curriteration] = times 

  def performTests(self, basepath):
    fd = open('binfiles/1k.bin')
    fdata = fd.read()
    fd.close()    
    for i in xrange(self.iterations):
      self.curriteration = i
      for j in xrange(self.maxfiles):
        self.createTest(os.path.join(basepath, str(j)), fdata)
        self.listTest()
        self.filecount += 1
        if not self.filecount % 500:
          print 'increment iteration %s' % (self.filecount)
      for f in self.list():
        self.filecount -= 1
        self.removeTest(f)
        if not self.filecount % 500:
          print 'decrement iteration %s' % (self.filecount)



class SageScaleTester(ScalabilityTester):

  def __init__(self, maxfiles, iters, fakesage=False):
    if fakesage: 
      self.fs = FakeFS()
    else: 
      swifths = {'swift':sagefs.hosts.SwiftHost('localhost', 'admin', 'system', 'sagefs')}
      mongohs ={'mongo':sagefs.hosts.MongoHost('localhost', 'Sage', 'fsdata')}
      self.fs = sagefs.SageFS(swifths, mongohs)
    ScalabilityTester.__init__(self, maxfiles, iters)


  def remove(self, fname):
    self.fs.remove(fname)

  def create(self, fname, data):
    fd = self.fs.open(fname, create=True)
    fd.write(data, sync=False)
    fd.close()

  def list(self):
    return self.fs.list()



class SwiftScaleTester(ScalabilityTester):

  def __init__(self, maxfiles, iters, host=benchmachines.swifthost, user='system:admin', key='sagefs', container='bench'):
    self.host = host
    self.authurl = self.getAuthUrl()
    self.user = user
    self.key = key
    self.container = container
    self.sturl, self.token = self.getAuth()
    ScalabilityTester.__init__(self, maxfiles, iters)
    swiftclient.put_container(self.sturl, self.token, self.container)

  def getAuthUrl(self):
    return 'http://%s:8080/auth/v1.0' % (self.host)

  def getAuth(self):
    return swiftclient.get_auth(self.authurl, self.user, self.key)


  def remove(self, fname):
    swiftclient.delete_object(self.sturl, self.token, self.container, fname['name'])

  def create(self, fname, data):
    swiftclient.put_object(self.sturl, self.token, self.container, fname, data)

  def list(self):
    return swiftclient.get_container(self.sturl, self.token, self.container)[1]



class MongoScaleTester(ScalabilityTester):
  
  def __init__(self, maxfiles, iters, host=benchmachines.mongohost, port=27017, database='bench', collection='bench'):
    self.client = pymongo.MongoClient() # use localhost and default port
    self.db = self.client[database]
    self.collection = self.db[collection]
    ScalabilityTester.__init__(self, maxfiles, iters)

  def create_insert_record(self, name, data):
    return {'name':name, 'data':data}

  def create_select_record(self, name):
    return {'name':name}


  def remove(self, fname):
    record = self.create_select_record(fname['name'])
    self.collection.remove(record)

  def create(self, fname, data):
    bsondata = bson.binary.Binary(data)
    insertrecord = self.create_insert_record(fname, bsondata)
    self.collection.insert(insertrecord)

  def list(self):
    return self.collection.find({})



def runSageSwiftScaleTest(maxfiles, iters):
  t = SageScaleTester(maxfiles, iters)
  t.performTests('/swift')
  t.writeAllTimes('results/scale/sageswift/list%s.txt' % (maxfiles), t.listtimes)
  t.writeAllTimes('results/scale/sageswift/create%s.txt' % (maxfiles), t.createtimes)
  t.writeAllTimes('results/scale/sageswift/remove%s.txt' % (maxfiles), t.removetimes)

def runSageMongoScaleTest(maxfiles, iters):
  t = SageScaleTester(maxfiles, iters)
  t.performTests('/mongo')
  t.writeAllTimes('results/scale/sagemongo/list%s.txt' % (maxfiles), t.listtimes)
  t.writeAllTimes('results/scale/sagemongo/create%s.txt' % (maxfiles), t.createtimes)
  t.writeAllTimes('results/scale/sagemongo/remove%s.txt' % (maxfiles), t.removetimes)

def runSageRandomScaleTest(maxfiles, iters):
  t = SageScaleTester(maxfiles, iters)
  t.performTests('/all')
  t.writeAllTimes('results/scale/sagerandom/list%s.txt' % (maxfiles), t.listtimes)
  t.writeAllTimes('results/scale/sagerandom/create%s.txt' % (maxfiles), t.createtimes)
  t.writeAllTimes('results/scale/sagerandom/remove%s.txt' % (maxfiles), t.removetimes)

def runSwiftScaleTest(maxfiles, iters):
  t = SwiftScaleTester(maxfiles, iters)
  t.performTests('/swift')
  t.writeAllTimes('results/scale/swift/list%s.txt' % (maxfiles), t.listtimes)
  t.writeAllTimes('results/scale/swift/create%s.txt' % (maxfiles), t.createtimes)
  t.writeAllTimes('results/scale/swift/remove%s.txt' % (maxfiles), t.removetimes)

def runMongoScaleTest(maxfiles, iters):
  t = MongoScaleTester(maxfiles, iters)
  t.performTests('/mongo')
  t.writeAllTimes('results/scale/mongo/list%s.txt' % (maxfiles), t.listtimes)
  t.writeAllTimes('results/scale/mongo/create%s.txt' % (maxfiles), t.createtimes)
  t.writeAllTimes('results/scale/mongo/remove%s.txt' % (maxfiles), t.removetimes)



if __name__ == '__main__':
  try:
    maxfiles = int(sys.argv[2])
    iters = int(sys.argv[3])
  except Exception, e:
    maxfiles = 10
    iters = 2
  testtype = sys.argv[1]

  if testtype == 'sageswift':
    runSageSwiftScaleTest(maxfiles, iters)
  elif testtype == 'sagemongo':
    runSageMongoScaleTest(maxfiles, iters)
  elif testtype == 'sagerandom':
    runSageRandomScaleTest(maxfiles, iters)
  elif testtype == 'swift':
    runSwiftScaleTest(maxfiles, iters)
  elif testtype == 'mongo':
    runMongoScaleTest(maxfiles, iters)

  else:
    print 'Unknown Test Type %s' % (testtype)


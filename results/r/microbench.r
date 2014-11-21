library(ggplot2)
library(gridExtra)

GetResultFilename = function(testtype, mode, size) {
  sizefile = paste(size, '.txt', sep='')
  paste('~/Dropbox/fs/benchmark/results/micro', testtype, mode, sizefile, sep='/')
}


GetSimpleData = function(testtype, mode, size) {
  datapath = GetResultFilename(testtype, mode, size)
  cdata = read.csv(datapath)
  data.frame(iteration=attr(cdata, 'row.names'), times=cdata$elapsedtime)
}


SimplePlot = function(testtype, mode, size) {
  
  data = GetSimpleData(testtype, mode, size)
  
  title = paste(size, 'file', mode, 'request times')
  
  # points
  print(paste('Rendering simple points plot', testtype, mode, size, sep=' '))
  pdfpath = paste( paste('../plots/micro', testtype, sep='/'), '/', size, 'points', mode, '.pdf', sep='')
  p1 = ggplot(data, aes(x=iteration, y=times)) + geom_point() + ggtitle(title) + 
    xlab('iteration') + ylab('request time')
  ggsave(pdfpath)
  
  # histogram
  print(paste('Rendering simple histogram', testtype, mode, size, sep=' '))
  pdfpath = paste( paste('../plots/micro', testtype, sep='/'), '/', size, 'hist', mode, '.pdf', sep='')  
  p2 = ggplot(data, aes(x=times)) + geom_histogram(binwidth=(max(data$times) - min(data$times)) / 40) + 
    ggtitle(title) + xlab('request time')
  ggsave(pdfpath)
  
  # density plot
  print(paste('Rendering simple density plot', testtype, mode, size, sep=' '))
  pdfpath = paste( paste('../plots/micro', testtype, sep='/'), '/', size, 'dense', mode, '.pdf', sep='')  
  p3 = ggplot(data, aes(x=times)) + geom_density() + ggtitle(title) + xlab('request time')
  ggsave(pdfpath)
  
  # all in one
  print(paste('Rendering multiplot for', testtype, mode, sep=' '))
  pdfpath = paste( paste('../plots/micro', testtype, sep='/'), '/', size, 'multi', mode, '.pdf', sep='')
  gframe = arrangeGrob(p1, p2, p3, nrow=3, ncol=1)
  ggsave(pdfpath, gframe)
}


GetBigPlotData = function(testtype, mode, files) {
  
  filesize = 1
  y = c()
  x = c()
  for (f in files) {
    datapath = GetResultFilename(testtype, mode, f)
    data = read.csv(datapath)
    y = c(y, data$elapsedtime[1:100])
    x = c(x, rep(filesize, 100))
    filesize = filesize * 10
  }
  data.frame(sizes=factor(x), times=y)
}


BigPlot = function(testtype, mode, files) {
  
  title = paste('File', mode, 'request times from', testtype)
  data = GetBigPlotData(testtype, mode, files)
  
  # Create point plots
  cat(paste('Rendering big points plots', testtype, mode, 'with: ', sep=' '))
  cat(paste(files, sep=' '))
  pdfpath = paste( paste('../plots/micro', testtype, 'point', sep='/'), mode, '.pdf', sep='')  
  ggplot(data, aes(x=sizes, y=times, fill=sizes)) + geom_point() + ggtitle(title) + 
    xlab('file size in kB') + ylab('request time')
  ggsave(pdfpath)
  
  pdfpath = paste( paste('../plots/micro', testtype, 'pointlog', sep='/'), mode, '.pdf', sep='')  
  ggplot(data, aes(x=sizes, y=times, fill=sizes)) + geom_point()  + scale_y_log10() +
    ggtitle(title) + xlab('file size in kB') + ylab('log request time')
  ggsave(pdfpath)
  
  # create box plots
  cat(paste('Rendering big points plots', testtype, mode, 'with: ', sep=' '))
  cat(paste(files, sep=' '))
  pdfpath = paste( paste('../plots/micro', testtype, 'bar', sep='/'), mode, '.pdf', sep='')  
  ggplot(data, aes(x=sizes, y=times, fill=sizes)) + geom_boxplot() + ggtitle(title) + 
    xlab('file size in kB') + ylab('request time')
  ggsave(pdfpath)
  
  pdfpath = paste( paste('../plots/micro', testtype, 'barlog', sep='/'), mode, '.pdf', sep='')
  ggplot(data, aes(x=sizes, y=times, fill=sizes)) + geom_boxplot() + scale_y_log10() +
    ggtitle(title) + xlab('file size in kB') + ylab('log request time')
  ggsave(pdfpath)
}


GetAllPlotData = function(files, mode, tests, aggregatefn) {
  y = c()
  x = c()
  labs = c()
  for (testtype in tests) {
    filesize = 1
    for (f in files) {
      if ( (testtype == 'mongo'|| testtype == 'sagemongo') && f == '100m') {
        y = c(y, NA)
      } else {
        datapath = GetResultFilename(testtype, mode, f)
        data = read.csv(datapath)
        y = c(y, aggregatefn(data$elapsedtime[1:100]))
      }
      x = c(x, filesize)
      labs = c(labs, testtype)
      filesize = filesize * 10
    }
  }
  data = data.frame(sizes=factor(x), times=y, labels=factor(labs))
}

AllPlot = function(files, mode, tests) {
    
  # generate median all scatterplot
  title = paste('Median file', mode, 'request times for all')
  print(paste('Rendering all scatterplot using median for', mode, sep=' '))
  pdfpath = paste('../plots/micro/all/', 'median', mode, '.pdf', sep='')
  data = GetAllPlotData(files, mode, tests, median)
  p1 = ggplot(data, aes(x=sizes, y=times, shape=labels)) + geom_point() + scale_y_log10() +
    ggtitle(title) + xlab('file size in kB') + ylab('log request time')
  ggsave(pdfpath)
  
  # generate mean all scatterplot
  title = paste('Mean file', mode, 'request times for all')
  print(paste('Rendering all scatterplot using mean for', mode, sep=' '))
  pdfpath = paste('../plots/micro/all/', 'mean', mode, '.pdf', sep='')
  data = GetAllPlotData(files, mode, tests, mean)
  p2 = ggplot(data, aes(x=sizes, y=times, shape=labels)) + geom_point() + scale_y_log10() +
    ggtitle(title) + xlab('file size in kB') + ylab('log request time')
  ggsave(pdfpath)
  
  # generate max all scatterplot
  title = paste('Max file', mode, 'request times for all')
  print(paste('Rendering all scatterplot using max for', mode, sep=' '))
  pdfpath = paste('../plots/micro/all/', 'max', mode, '.pdf', sep='')
  data = GetAllPlotData(files, mode, tests, max)
  p3 = ggplot(data, aes(x=sizes, y=times, shape=labels)) + geom_point() + scale_y_log10() +
    ggtitle(title) + xlab('file size in kB') + ylab('log request time')
  ggsave(pdfpath)
  
  # generate min all scatterplot
  title = paste('Min file', mode, 'request times for all')
  print(paste('Rendering all scatterplot using min for', mode, sep=' '))
  pdfpath = paste('../plots/micro/all/', 'min', mode, '.pdf', sep='')
  data = GetAllPlotData(files, mode, tests, min)
  p4 = ggplot(data, aes(x=sizes, y=times, shape=labels)) + geom_point() + scale_y_log10() +
    ggtitle(title) + xlab('file size in kB') + ylab('log request time')
  ggsave(pdfpath)
  
  # put all in one plot for fun
  print(paste('Rendering all multiplot for', mode, sep=' '))
  pdfpath = paste('../plots/micro/all/', 'multi', mode, '.pdf', sep='')
  gframe = arrangeGrob(p1, p2, p3, p4, nrow=2, ncol=2)
  ggsave(pdfpath, gframe)
}

GeneratePlots = function() {
  files = c('1k', '10k', '100k', '1m', '10m', '100m')
  modes = c('put', 'get')
  tests = list(c('swift', 'sageswift', 'local'), c('mongo', 'sagemongo'))
  
  # generate plot with all the data
  for (m in modes) {
    ts = c()
    for (t in tests) {
      ts = c(ts, t)
    }
    AllPlot(files, m, ts)
  }
  # mongo is different from swift and local  
  for (tt in tests) {
    # sage and not
    for (t in tt) {
      # put and get
      for (m in modes) {
        # simple plot for each test size
        for (f in files) {
          SimplePlot(t, m, f)
        }
        # big plots for mode with all sizes
        BigPlot(t, m, files)
      }
    }
    # mongo has no 100m so trim it off
    files = files[1:length(files)-1]
  }
}

GenerateTables = function() {

  modes = c('put', 'get')
  tests = list(c('swift', 'sageswift', 'local'), c('mongo', 'sagemongo'))
  methods = c('min', 'max', 'median', 'mean', 'stddev')
  
  for (m in modes) {
    files = c('1k', '10k', '100k', '1m', '10m', '100m')
    dnames = list(methods, files)
    alldatamatrix = list(swift=matrix(nrow=length(methods), ncol=length(files), dimnames=dnames),
                         sageswift=matrix(nrow=length(methods), ncol=length(files), dimnames=dnames),
                         mongo=matrix(nrow=length(methods), ncol=length(files), dimnames=dnames),
                         sagemongo=matrix(nrow=length(methods), ncol=length(files), dimnames=dnames),
                         local=matrix(nrow=length(methods), ncol=length(files), dimnames=dnames))
    # mongo is different from swift and local  
    for (tt in tests) {
      # sage and not
      for (t in tt) {
        # simple plot for each test size
        for (f in files) {
          data = GetSimpleData(t, m, f)
          ts = data$times
          alldatamatrix[[t]]['min', f] = min(ts)
          alldatamatrix[[t]]['max', f] = max(ts)
          alldatamatrix[[t]]['median', f] = median(ts)
          alldatamatrix[[t]]['mean', f] = mean(ts)
          alldatamatrix[[t]]['stddev', f] = sd(ts)
        }
      }
      # mongo has no 100m so trim it off
      files = files[1:length(files)-1]
    }
    print(m)
    print(alldatamatrix)
  }
}

GeneratePlots()
GenerateTables()

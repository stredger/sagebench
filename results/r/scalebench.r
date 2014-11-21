library(ggplot2)

GetResultFilename = function(testtype, optype) {
  paste('~/Dropbox/fs/benchmark/results/scale', testtype, paste(optype, '.txt', sep=''), sep='/')
}

SimplePlot = function(testtype, op) {
  
  nums = sort(rep(1:1000, 10))
  datapath = GetResultFilename(testtype, op)
  cdata = read.csv(datapath, skip=1)
  data = data.frame(times=cdata$elapsedtime, filenum=nums)
  meandata = c()
  meddata = c()
  mindata = c()
  maxdata = c()
  for (i in 0:999) {
    meandata = c(meandata, mean(data$times[(i*10+1):((i+1)*10)]))
    meddata = c(meddata, median(data$times[(i*10+1):((i+1)*10)]))
    mindata = c(mindata, min(data$times[(i*10+1):((i+1)*10)]))
    maxdata = c(maxdata, max(data$times[(i*10+1):((i+1)*10)]))
  }
  meandf = data.frame(times=meandata, filenum=1:1000)
  meddf = data.frame(times=meddata, filenum=1:1000)
  maxdf = data.frame(times=maxdata, filenum=1:1000)
  mindf = data.frame(times=mindata, filenum=1:1000)
  alldf = data.frame(times=c(meddata, meandata, maxdata, mindata, data$times),
                     filenum=factor(c(rep(1:1000, 4), nums)), 
                     aggfn=c(rep('median', 1000), rep('mean', 1000), rep('max', 1000), rep('min', 1000), rep('scatter', 1000*10)))
  
  
  print(paste('Rendering 1000 scatter plot for', testtype, op))
  title = paste('File', op, 'times')
  pdfpath = paste( paste('../plots/scale', testtype, '', sep='/'), op, 'scatter.pdf', sep='')
  ggplot(data, aes(x=filenum, y=times)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 mean scatter plot for', testtype, op))
  title = paste('Mean file', op, 'times')
  pdfpath = paste( paste('../plots/scale', testtype, '', sep='/'), op, 'mean.pdf', sep='')
  ggplot(meandf, aes(x=filenum, y=times)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 median scatter plot for', testtype, op))
  title = paste('Median file', op, 'times')
  pdfpath = paste( paste('../plots/scale', testtype, '', sep='/'), op, 'median.pdf', sep='')
  ggplot(meddf, aes(x=filenum, y=times)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 max scatter plot for', testtype, op))
  title = paste('Max file', op, 'times')
  pdfpath = paste( paste('../plots/scale', testtype, '', sep='/'), op, 'max.pdf', sep='')
  ggplot(maxdf, aes(x=filenum, y=times)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 min scatter plot for', testtype, op))
  title = paste('Min file', op, 'times')
  pdfpath = paste( paste('../plots/scale', testtype, '', sep='/'), op, 'min.pdf', sep='')
  ggplot(mindf, aes(x=filenum, y=times)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  #ggplot(alldf, aes(x=filenum, y=times, color=aggfn)) + geom_point() + ylim(0, 0.1)
}


All1000Plot = function(tests, op) {
  
  meddata = c()
  meandata = c()
  maxdata = c()
  mindata = c()
  tnames = c()
  for (testtype in tests) {
    datapath = GetResultFilename(testtype, op)
    cdata = read.csv(datapath, skip=1)
    for (i in 0:999) {
      meddata = c(meddata, median(cdata$elapsedtime[(i*10+1):((i+1)*10)]))
      meandata = c(meandata, mean(cdata$elapsedtime[(i*10+1):((i+1)*10)]))
      maxdata = c(maxdata, max(cdata$elapsedtime[(i*10+1):((i+1)*10)]))
      mindata = c(mindata, min(cdata$elapsedtime[(i*10+1):((i+1)*10)]))
    }
    tnames = c(tnames, rep(testtype, 1000))
  }
  meddf = data.frame(times=meddata, test=tnames, filenum=factor(rep(1:1000, length(tests))))
  meandf = data.frame(times=meandata, test=tnames, filenum=factor(rep(1:1000, length(tests))))
  maxdf = data.frame(times=maxdata, test=tnames, filenum=factor(rep(1:1000, length(tests))))
  mindf = data.frame(times=mindata, test=tnames, filenum=factor(rep(1:1000, length(tests))))
  alldf = data.frame(times=c(meddata, meandata, maxdata, mindata),
                     test=rep(tnames, 4),
                     filenum=factor(rep(rep(1:1000, length(tests)), 4)), 
                     aggfn=c(rep('median', 1000), rep('mean', 1000), rep('max', 1000), rep('min', 1000)))
  
  print(paste('Rendering 1000 plot for', op))
  title = paste('Median file', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, 'median.pdf', sep='')
  ggplot(meddf, aes(x=filenum, y=times, color=test)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 log plot for', op))
  title = paste('Median file', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, 'logmedian.pdf', sep='')
  ggplot(meddf, aes(x=filenum, y=times, color=test)) + geom_point() + scale_y_log10() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste('log', op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 plot for', op))
  title = paste('Mean file', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, 'mean.pdf', sep='')
  ggplot(meandf, aes(x=filenum, y=times, color=test)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 log plot for', op))
  title = paste('Mean file', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, 'logmean.pdf', sep='')
  ggplot(meandf, aes(x=filenum, y=times, color=test)) + geom_point() + scale_y_log10() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste('log', op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 plot for', op))
  title = paste('Max file', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, 'max.pdf', sep='')
  ggplot(maxdf, aes(x=filenum, y=times, color=test)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 log plot for', op))
  title = paste('Max file', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, 'logmax.pdf', sep='')
  ggplot(maxdf, aes(x=filenum, y=times, color=test)) + geom_point() + scale_y_log10() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste('log', op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 plot for', op))
  title = paste('Min file', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, 'min.pdf', sep='')
  ggplot(mindf, aes(x=filenum, y=times, color=test)) + geom_point() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
  
  print(paste('Rendering 1000 log plot for', op))
  title = paste('Min file', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, 'logmin.pdf', sep='')
  ggplot(mindf, aes(x=filenum, y=times, color=test)) + geom_point() + scale_y_log10() + scale_x_discrete(breaks=c(0:10*100)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste('log', op, 'time'))
  ggsave(pdfpath)
  
  # ggplot(alldf, aes(x=filenum, y=times, color=test, shape=aggfn)) + geom_point() + ylim(0.05, 0.1)
}


All10000Plot = function(tests, op) {
  tnames = c()
  times = c()
  fnums = c()
  for (testtype in tests) {
    datapath = GetResultFilename(testtype, paste(op, '10000', sep=''))
    cdata = read.csv(datapath, skip=1)
    times = c(times, cdata$elapsedtime)
    tnames = c(tnames, rep(testtype, 10000))
  }
  data = data.frame(times=times, test=tnames, filenum=factor(rep(1:10000, length(tests))))
  
  print(paste('Rendering 10000 plot for', op))
  title = paste('File', op, 'times')
  pdfpath = paste('../plots/scale/all/', op, '10000.pdf', sep='')
  ggplot(data, aes(x=filenum, y=times, color=test)) + geom_point() +  scale_x_discrete(breaks=c(0:10*1000)) +
    ggtitle(title) + xlab('number of existing files') + ylab(paste(op, 'time'))
  ggsave(pdfpath)
}

tests = c('mongo', 'sagemongo', 'swift', 'sageswift', 'sagerandom')
ops = c('create', 'list', 'remove')

for (op in ops) {
  for (tt in tests) {
    SimplePlot(tt, op)
  }
  All1000Plot(tests, op)
  All10000Plot(tests, op)
}
print('Done!')

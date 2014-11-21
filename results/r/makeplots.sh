#! /usr/bin/env bash


for f in "swift" "mongo" "sageswift" "sagemongo" "local" "all"; do
  mkdir -p "../plots/micro/${f}"
done

for f in "swift" "mongo" "sageswift" "sagemongo" "sagerandom" "all"; do
  mkdir -p "../plots/scale/${f}"
done

Rscript microbench.r
Rscript scalebench.r
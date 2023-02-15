#!/usr/bin/env python
import sys
import os
import subprocess
import fileinput
import matplotlib.pyplot as plt
from operator import itemgetter

v8_cmd='/home/denis/src/v8/v8/out/x64.release/d8'
sm_cmd='/home/denis/src/mozilla-central/obj-js/dist/bin/js'
workload='/home/denis/src/shell/Speedometer/resources/todomvc/architecture-examples/react/index.js'

def measureMemory(exe,test):
    cmd=['/usr/bin/time','-v',exe,test]
    #print(" ".join(cmd))
    process = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=os.path.dirname(workload))
    stdout, stderr = process.communicate()

    output = stdout.split(b'\n')
    for line in output:
      if b'took:' in line:
        print(line.decode('utf-8'))
        break

    output = stderr.split(b'\n')
    for line in output:
      if b'Maximum resident set size' in line:
        peakMem = int(line.split(b':')[1])
        print(peakMem)
        return peakMem

def ReplaceIterationCount(iteration):
    for line in fileinput.input(workload, inplace=1):
        if 'var numberOfItemsToAdd =' in line:
          print("        var numberOfItemsToAdd = " + str(iteration) + ";")
        else:
          print(line,end="")

iterations = []
v8_mem = []
sm_mem = []

for i in range(200,5000,300):
  print("----------------- " + str(i) + " ------------------")
  ReplaceIterationCount(i)
  print("V8:")
  v8_peak = measureMemory(v8_cmd,workload)
  print("SM:")
  sm_peak = measureMemory(sm_cmd,workload)

  iterations.append(i)
  v8_mem.append(v8_peak)
  sm_mem.append(sm_peak)


plt.plot(iterations, sm_mem, label = "sm")
plt.plot(iterations, v8_mem, label = "v8")
plt.title("Maximum resident set size (kb)")
plt.ylabel('Maximum resident set size (kb)')
plt.xlabel('numberOfItemsToAdd')
plt.legend()
plt.show()

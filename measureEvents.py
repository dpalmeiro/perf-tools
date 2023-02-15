#!/usr/bin/env python
import getopt
import json
import sys
import glob
import os
import subprocess
from operator import itemgetter

metrics_dir='/home/denis/src/perfmon-metrics/linux/tools/perf/pmu-events/arch/x86/skylakex/'
v8_cmd='/home/denis/src/v8/v8/out/x64.release/d8'
sm_cmd='/home/denis/src/mc/obj-js/dist/bin/js'
workload='/home/denis/src/shell/Speedometer/resources/todomvc/architecture-examples/react/index.js'

eventSet = set({})
metricGroups = {}
v8_results = {}
sm_results = {}

def PopulateEvents(eventsFilename):
  print("Populating events with " + eventsFilename)
  with open(eventsFilename) as eventsFile:
    events = json.load(eventsFile)
    for event in events:
      eventSet.add(event['EventName'])

def CheckForError(stdout):
  lines = stdout.split(b'\n')
  for line in lines:
    if b'took:' in line:
      print(line.decode('utf-8'))
      break

  if b'Error' in stdout:
    print("Error encountered in stdout")
    sys.exit(1)

def CollectPerfStats(exe,test,metric):
    cmd=['perf','stat','-M',metric,exe,test]
    print(" ".join(cmd))
    process = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=os.path.dirname(workload))
    stdout, stderr = process.communicate()
    CheckForError(stdout);

    output = stderr.split(b'\n')

    retVal = {}
    for line in output:
      fields = line.split()

      #print(line)
      for i,field in enumerate(fields):
        counter = field.replace(b',',b'')
        if counter.isdigit():
          event = fields[i+1].decode('utf-8')
          if event in eventSet:
            metricGroups[event] = metric
            retVal[event] = int(counter)

    return retVal

def AddToResults(output, results):
  for event,ctr in output.items():
    results[event] = ctr

def ComputeComparisons(results1, results2):
  results = []
  for event in results1:
    if event in results2:
      val1 = results1[event]
      val2 = results2[event]
      if val1 == 0 or val2 == 0:
        continue

      ratio = val2/val1;
      entry = [event, results1[event], results2[event], ratio]
      results.append(entry)
  return results

def PrintResults(results, results1_title, results2_title):
  # Header
  print()
  print("%30s"% "metric group" + "%50s"% "event" + "%15s"% results1_title + "%15s"% results2_title + "%9s"% "ratio")
  print("-"*(30+50+15+15+9))

  for entry in results:
    print("%30s"% metricGroups[entry[0]] + 
          "%50s"% entry[0] + 
          "%15d"% entry[1] + 
          "%15d"% entry[2] + 
          "%9.2f"% entry[3])

########## Start Execution Here ###############
os.chdir(metrics_dir);
files = glob.glob("*.json")

metricsFilename = '';
for filename in files:
  if 'metrics.json' in filename:
    if not metricsFilename:
      metricsFilename = filename
    else:
      print("Multiple metrics filenames found.")
      sys.exit(1);
  else:
    PopulateEvents(filename);

print("Found metrics file " + metricsFilename)
with open(metricsFilename) as metricsFile:
  metrics = json.load(metricsFile)
  
  for i,m in enumerate(metrics):
    metricName = m['MetricName']

    # Run V8
    output = CollectPerfStats(v8_cmd, workload, metricName)
    AddToResults(output, v8_results)

    # Run SM
    output = CollectPerfStats(sm_cmd, workload, metricName)
    AddToResults(output, sm_results)

results = ComputeComparisons(v8_results, sm_results)
results = sorted(results, key=itemgetter(3), reverse=True)
PrintResults(results,"v8","SM")


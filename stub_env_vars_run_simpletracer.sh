#!/bin/bash
#     LD_LIBRARY_PATH,
#     LD_CORPUS_PATH,
#     LD_TRACES_PATH
# environment variables
# needed for generating build/bin/trace.simple.out and 
# 			build/bin/execution.log.
#

cd ~/github_repos/symexec
cd build/bin

export LD_LIBRARY_PATH=`pwd`/../lib
export LD_CORPUS_PATH=""

export LD_TRACES_PATH="all_trace_simple_out/"

# TODO
#   check paths are valid

#testcase="~/github_repos/river-log-file-analysis/genetic_code/test"
scp ~/github_repos/river-log-file-analysis/genetic_code/test .
testcase="test"
echo $testcase
printf "Using %s testcase.\n" "$testcase"
./simple_tracer --payload libhttp-parser.so < $testcase

executionLogFileName="execution.log"
traceSimpleOutFileName="trace.simple.out"

echo ""
du -h $executionLogFileName $traceSimpleOutFileName
echo "execution.log and trace.simple.out can be found in build/bin/"



cd ~/github_repos/river-log-file-analysis/genetic_code

spark-submit --master local --num-executors 2 --total-executor-cores 2 --executor-memory 1g main.py --testsFolderCount 20 --populationSize 100 --numTasks 10 --isParallelExecution 1 --logsPath $SIMPLETRACERLOGSPATH


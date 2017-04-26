import glob
import argparse
import sys
import os
import functools
from worker import Worker
from functors import EvalFunctors
import utils
import probabilities
import time
import struct

def generateNewTestsFolder(path, listOfTests, evalFunctor):
    # Generate the new tests folder on disk.
    # The code below iterates over existing population of inputs and generates the traces.
    # Write these as files in a new folder similar to the existing tests folder.
    	
    if not os.path.exists(path):
        os.makedirs(path)
    	
    testcaseIndex = 0
    for test in listOfTests.getPopulation():
        traceOutput = []
        streamData, streamSize = evalFunctor.getTrace(test)

        # write Trace		
        outTrace = open(path + "/trace.simple.out_" + str(testcaseIndex), "wb")
        outTrace.write(streamData)  # because the first 4 bytes contain the size
        outTrace.close()
        testcaseIndex += 1

def createSimpleTracerProcesses(outListOfProcesses, Params):
    cmd = utils.createTracerCmd(Params)
    for i in range(Params.numTasks):
        p = utils.createTracerProcess(cmd, int(Params.inputLength))
        outListOfProcesses.append(p)

def stopSimpleTracerProcesses(listOfProcesses):
    for p in listOfProcesses:
        utils.stopTracerProcess(p)

def runApp(Params):
    sc = None
    isParallelExecution = Params.isParallelExecution
    if isParallelExecution:
        sc = utils.createSparkContext(Params)
        print ("NUMBER OF TASKS USED = " + str(Params.numTasks) + " PlEASE provide correct number should be a factor of number of workers (e.g. 5 * NUM WORKERS). PySpark API doesn't know number of workers :(")

    # TODO CPaduraru: hacked see the other comments in this file about spark / serialization of process issue
    recreateTracerProcessAtEachNewFolder = True # isParallelExecution

    # One tracer process opened for each task. Basically these will be working processes sleeping most of the time so it shouldn't affect performance
    if not recreateTracerProcessAtEachNewFolder:
        tracerProcesses = []
        createSimpleTracerProcesses(tracerProcesses, Params)
    #---

    t0 = time.time()

    for testIndex in range(Params.testsFolderCount):
        # The noEdgeProbability represents the value to use in fitness evaluation when an edge was not encountered yet in the probabilities map
        probabilities.updateFromFolder(utils.getFolderPathFromId(testIndex), Params.entryTemplate)

        # Generate new worker tasks.
        Workers = []
        for i in range(Params.numTasks):

            evalFunctor = EvalFunctors(probabilities.Probability, probabilities.noEdgeProbability,
                                       probabilities.blockOffsetToIndex, Params.entryTemplate, None if recreateTracerProcessAtEachNewFolder else tracerProcesses[i]) # TODO CPaduraru: see other comments about the the spark / process optimization.

            worker = Worker(evalFunctor,  # fitness functor
                            Params.populationSize, Params.inputLength, Params.numberOfIterations,
                            Params.elitismPercent,
                            Params.oldGenerationP,
                            Params.mutationP,
                            Params.deltaMutate,
                            Params.thresholdForLocalMaxima,
                            recreateTracerProcessAtEachNewFolder, utils.createTracerCmd(Params), int(Params.inputLength))
            Workers.append(worker)

        if isParallelExecution:
            workersRDD = sc.parallelize(Workers) # I would expect to use defaultParallelism and split the Workers list on each worker, equall chunks
            workerRes = workersRDD.map(lambda w: w.solve()).reduce(lambda w1, w2: Worker.reduce(w1, w2)) # TODO: make sure that data is not copied in an inneficient way !
        else:
            # Solve and reduce to one worker
            Workers[0].solve(Params.DEBUG_ENABLED)
            workerRes = Workers[0]
            for i in range(1, Params.numTasks):
                Workers[i].solve(Params.DEBUG_ENABLED);  # Send first parameter as True for debugging population at each generation
                workerRes = Worker.reduce(workerRes, Workers[i])

        # TODO CPaduraru: again a horrible hack because python closure can include a subprocess data.
        # After solve (map part), the tracer process is set on None so we must create it back  to generate new tests folder
        if recreateTracerProcessAtEachNewFolder:
            cmd = utils.createTracerCmd(Params)
            workerRes.evalFunctor.tracerProcess = utils.createTracerProcess(cmd, int(Params.inputLength))
        #-----------

        generateNewTestsFolder(utils.getFolderPathFromId(testIndex+1), workerRes.population, workerRes.evalFunctor)

        # TODO Cpaduraru: hack associated with the one above
        if recreateTracerProcessAtEachNewFolder:
            utils.stopTracerProcess(workerRes.evalFunctor.tracerProcess)
        #------

    # Now stop all tracer processes
    if not recreateTracerProcessAtEachNewFolder:
        stopSimpleTracerProcesses(tracerProcesses)

    dt = time.time() - t0
    print("Time to solve : %fs" % dt)



def main(argv=None):
    # Short story: We'll create N Tasks
    # Each task is a genetic algorithm which has a population of individuals
    # (each individual represents a test and its represented in memory as
    # an array of bytes)
    # We create N tasks which will compete on W workers available,
    # ideally N should be greater significantly than W to optimize
    # stuff - that's what parameter tasksFactor stands for.
    # Each task will have a number of generations available to optimize things.
    # After this number of iterations, we do a merge operation to select the
    # bests tests from those N workers.
    # The bests tests will be outputed on a new folder with tests,
    # how many folders is defined by testsFolderCount.
    # TODO: many of this parameter should not be optional!
    #       But we keep them optional for easy testing :)
	
	# TODO CPADURARU: environment variables
	# subprocess.Popen("sh stub_env_variables_genetic_code.sh", shell=True)
    Params = utils.readParams()
    runApp(Params)


if __name__ == "__main__":
    sys.exit(main())


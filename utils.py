# To make it work with pycharm IDE do the following 2 steps:
# 2. Create a new configuration and use that one (Run, Edit Configuration, New Configuration
# 3. Add SPARK_HOME to your spark folder (where bin, conf, jars etc folders are located).
# 4. Add PYTHONPATH as $SPARK_HOME$/python/
# 5. Unzip the py4j-0.10.3-src.zip content to $SPARK_HOME$/python/py4j (at least on windows)
#http://stackoverflow.com/questions/34685905/how-to-link-pycharm-with-pyspark
import argparse
import sys
import os
import subprocess
import struct
from collections import namedtuple
from parse import *
from pyspark import SparkConf, SparkContext

logsFullPath =""

# Creates the spark context
def createSparkContext(Params):
    conf = (SparkConf().setMaster(Params.parameterMaster)
                        .setAppName(Params.parameterAppName)
                        .set("spark.executor.memory", Params.parameterMemory))

    sc = SparkContext(conf=conf)

    # Add modules needed to be exported (copied) to all workers
    currentDirPath = os.path.dirname(os.path.abspath(__file__)) + "/"
    modulesToImport = ['functors.py', 'worker.py', 'population.py']

    for module in modulesToImport:
        sc.addPyFile(currentDirPath + module)

    sc.addPyFile(Params.simpleTracerPath)

    return sc

def readParams():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testsFolderCount", help="A number how many new folders with tests to generate",type=int)
    parser.add_argument("--numTasks", help="Num tasks to be created. THese will compete on your N workers. Unfortunatelly Python doesn't have something implemented as Scala to find out the number of workers in the system.", type=int)
    parser.add_argument("--testProgramName", help="The program used to evaluate the new generated tests. This must exist in env var LD_LIBRARY_PATH folder")
    parser.add_argument("--simpleTracerPath", help="The path to the full path of simple tracer executable. If nothing here, take it by default from SIMPLETRACERPATH")
    parser.add_argument("--isDebugEnabled", help="Display output from genetic generations", type=int)
    parser.add_argument("--isParallelExecution", help="Is Parallel execution ? ", type=int)

    parser.add_argument("--elitismPercent", help="How many to store from the best individuals from the previous generation", type=float)
    parser.add_argument("--populationSize", help="How many individuals per task", type=int)
    parser.add_argument("--inputLength", help="Length of each test (individual)", type=int)
    parser.add_argument("--numberOfIterations", help="Number of generations per task. A task will try to optimize its population this number of times", type=int)
    parser.add_argument("--oldGenerationP", help="Probability of selecting normal individuals (not elite ones) from the old generation - creates some diversity", type=float)
    parser.add_argument("--mutationP", help="Mutation probability", type=float)
    parser.add_argument("--deltaMutate", help="How much to increase mutation probability when local maxima is detected", type=float)
    parser.add_argument("--thresholdForLocalMaxima", help="Tthreshold to consider local maxima stuck and apply the delta mutate", type=float)

    parser.add_argument("--master", help="master of execution. By default is 'local' machine")
    parser.add_argument("--executorMemory", help="num gigabytes of ram memory that you allow spark to use on executor machines. by default we are using 1 gigabyte", type=int)
    parser.add_argument("--appName", help="name of the application - used for tracking purposes. by default is 'myapp'")
    args = parser.parse_args()

    Params = ParamsType
    Params.parameterMaster 			= "local" if args.master is None else str(args.master)
    Params.parameterMemory 			= "1g" if args.master is None else (str(args.executorMemory) + "g")
    Params.parameterAppName 		= "MyApp" if args.appName is None else str(args.appName)

    # First folder comes from somewhere ...fuzzy probably
    Params.testsFolderCount        = 1 if args.testsFolderCount is None else args.testsFolderCount
    Params.numTasks                = 1 if args.numTasks is None else args.numTasks

    simpleTracerPath = None
    if args.simpleTracerPath is None:
        #if psimple tracer path is not overridden, take it from the environment variable
        try:
            simpleTracerPath = os.environ["SIMPLETRACERPATH"]
        except KeyError:
            print ("ERROR: Please set the environment variable SIMPLETRACERPATH")
            sys.exit(1)

    if not os.path.exists(simpleTracerPath):
        print("ERROR: Simple tracer was not found at " + simpleTracerPath)
        sys.exit(1)

    Params.simpleTracerPath = simpleTracerPath

    # HACK : parameter shouldn't be optional
    if args.testProgramName is None:
        Params.testProgramName          = "libfmi.so" # "libhttp-parser.so"
    else:
        Params.testProgramName          = args.testProgramName

    # Check if it's there
    if not os.environ["LD_LIBRARY_PATH"]:
        print("ERROR: Please set the environment variable LD_LIBRARY_PATH. It should contain inside this folder the binaries used for testing (testProgramName parameter)")
        sys.exit(1)

    ldPaths = os.environ["LD_LIBRARY_PATH"].split(":")

    fullTestProgramPath = ""
    for path in ldPaths:
        fullTestProgramPath = os.path.join(path, Params.testProgramName)
        if not os.path.exists(fullTestProgramPath):
            print("WARN: Skipping ld path " + path)
            continue

    if not fullTestProgramPath:
        print("ERROR: Program to test was not found at " + fullTestProgramPath)
        sys.exit(1)

    Params.DEBUG_ENABLED            = False if args.isDebugEnabled is None else args.isDebugEnabled
    Params.isParallelExecution      = False if args.isParallelExecution is None else args.isParallelExecution

    Params.elitismPercent 			= 0.2 if args.elitismPercent is None else args.elitismPercent
    Params.populationSize 			= 2  if args.populationSize is None else args.populationSize
    Params.inputLength    			= 20  if args.inputLength is None else args.inputLength
    Params.numberOfIterations 		= 1  if args.numberOfIterations is None else args.numberOfIterations
    Params.oldGenerationP			= 0.1 if args.oldGenerationP is None else args.oldGenerationP
    Params.mutationP				= 0.2 if args.mutationP is None else args.mutationP
    Params.deltaMutate				= 0.3 if args.deltaMutate is None else args.deltaMutate
    Params.thresholdForLocalMaxima  = 0.000001 if args.thresholdForLocalMaxima is None else args.thresholdForLocalMaxima

    #  Set template for a input entry
    entryType_TestName              = 0x0010
    entryType_Module                = 0x00B0
    entryType_NextModule            = 0x00C0
    entryType_Offset                = 0x00BB
    entryType_InputUsage            = 0x00AA
    entryType_NextOffset            = 0x00A0
    EntryTemplate                   = namedtuple("t", "hF hS oF oS TN TM TO TIU TNM TNO") # header format, header size, offset format, offset size
    headerFtm                       = 'h h'
    offsetFtm                       = 'I h h h h'
    Params.entryTemplate            = EntryTemplate(hF = headerFtm, hS = struct.calcsize(headerFtm), oF = offsetFtm, oS = struct.calcsize(offsetFtm),
                                                    TN = entryType_TestName, TM = entryType_Module, TO = entryType_Offset, TIU = entryType_InputUsage,
                                                    TNO = entryType_NextOffset, TNM = entryType_NextModule)

    if Params.populationSize < 2:
        print("EROR: Please set a valid population size >=2" )
        sys.exit(1)

    global logsFullPath
    try:
        logsFullPath = os.environ["SIMPLETRACERLOGSPATH"]
    except KeyError:
        print("ERROR: Please set the environment variable SIMPLETRACERLOGSPATH")
        sys.exit(1)

    return Params

def getFolderPathFromId(ithFolder):
    return logsFullPath + "/generation" + str(ithFolder)

def getBlockOffsetEntryFromLine(line):
    if len(line.split()) != 5:
        return None,None # assert ?
    wordsOnLine = parse("{module} + {offset:x} ({cost:^d})", line)

    modulePath = wordsOnLine["module"]
    moduleName = modulePath[modulePath.rfind('/')+1 : ]; # using only the name for name as an optimization for string searches. Could make a map between full and name in the end if someone needs the full path
    return moduleName, int(wordsOnLine["offset"], 10)

def writeToProcess(var, process, numBytes, doFlush=True):
    process.stdin.write(var.to_bytes(numBytes, sys.byteorder))
    process.stdin.flush()

def createTracerCmd(Params):
    return [Params.simpleTracerPath, "--payload", Params.testProgramName, "--outfile", "stdout", "--flow", "--binlog", "--binbuffered", "--disableLogs"]

def createTracerProcess(cmd, payloadSize):
    p = subprocess.Popen(cmd, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # fully buffered, PIPE read/write
    writeToProcess(payloadSize, p, 4) # Init the process
    return p

def stopTracerProcess(p):
    writeToProcess(0, p, 1)

def getNextEntryFromStream(dataStream, streamPos, entryTemplate):
    headerFtm = entryTemplate.hF
    headerSize = entryTemplate.hS
    offsetInfoFmt = entryTemplate.oF
    offsetInfoSize = entryTemplate.oS

    headerRes = struct.unpack_from(headerFtm, dataStream, streamPos)
    streamPos += headerSize

    type = headerRes[0]
    length = headerRes[1]

    nameString = ''
    offset = 0
    cost = 0
    jumpType = 0
    jumpInstruction = 0
    nInstructions = 0
    nextoffset = 0
    nextModule = ''

    if type == entryTemplate.TN or type == entryTemplate.TM: # test name or module name type
        # do something
        nameString = dataStream[streamPos: streamPos + length]

        entrySize = headerSize + length
        streamPos += length
    elif type == entryTemplate.TNM: # next module
        nextModule = dataStream[streamPos: streamPos + length]
        entrySize = headerSize + length
        streamPos += length
    elif type == entryTemplate.TO: # pffset type
        offsetInfoRes   = struct.unpack_from(offsetInfoFmt, dataStream, streamPos)
        offset          = offsetInfoRes[0]
        cost            = offsetInfoRes[1]
        jumpType        = offsetInfoRes[2]
        jumpInstruction = offsetInfoRes[3]
        nInstructions   = offsetInfoRes[4]

        entrySize = headerSize + length
        streamPos += length
    elif type == entryTemplate.TNO:
        nextoffset = struct.unpack_from('I', dataStream, streamPos)
        entrySize = headerSize + length
        streamPos += length
    elif type == entryTemplate.TIU:
        print("Input usage: Not supported")
        exit(1)
    else:
        assert 1 == 0 # Unknown type !!!


    return (type, length, nameString, offset, cost, jumpType, entrySize,
            jumpInstruction, nInstructions, nextModule, nextoffset)


class ParamsType:
    pass

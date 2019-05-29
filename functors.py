import sys
import subprocess
import utils
import struct
import signal
import os

# Functors used for evaluation purposes
class EvalFunctors:
    def __init__(self, ProbabilityMap, noEdgeProbability, Mapping, entryTemplate, tracerProcess):
        self.ProbabilityMap 	= ProbabilityMap
        self.noEdgeProbability 	= noEdgeProbability
        self.Mapping 			= Mapping
        self.tracerProcess      = tracerProcess
        self.parentWorker       = None


        self.entryTemplate      = entryTemplate
        #self.headerFtm          = entryTemplate.hF
        #self.headerSize         = entryTemplate.hS
        #self.offsetFtm          = entryTemplate.oF
        #self.offsetSize         = entryTemplate.oS
        # alignment = 4  # this is the header alignment. how can we get this from code ?
        # alignmentMask = ~(alignment - 1)

    # InputString is a stream of bytes that is needed to evaluate the program
    # We take this and give it as input to the executable and we want to get the trace from it

    def getTrace(self, inputString):
        # in this method we run simpletracer using an output pipe and get the result (trace output) from that pipe	

        tracer = self.tracerProcess

        utils.writeToProcess(1, tracer, 1, False) # Wake up process and give it a task payload
        tracer.stdin.write(bytearray(inputString))
        tracer.stdin.flush()

        # Read the size of the returned buffer and data
        receivedOutputSize = tracer.stdout.read(4)
        if receivedOutputSize == b'Payl':
            print("Payload not found!")
            exit(1)

        # If process has crashed, saved the input and restart tracer
        if len(receivedOutputSize) == 0:
            # Wait for process returncode
            tracer.wait()

            # Save crash info
            self.saveCrashData(tracer, inputString)

            # Restart tracer process
            self.parentWorker.updateTracerProcess()

            # Interesting inputString
            return None, 0

        streamSize = struct.unpack("I", receivedOutputSize)[0]
        # print(streamSize)
        streamData = tracer.stdout.read(streamSize)

        return streamData, streamSize

    def saveCrashData(self, tracerProcess, inputString):
        from utils import logsFullPath
        error_type = {
            signal.SIGHUP: 'hup',
            signal.SIGINT: 'int',
            signal.SIGQUIT: 'quit',
            signal.SIGILL: 'ill',
            signal.SIGTRAP: 'trap',
            signal.SIGABRT: 'abrt',
            signal.SIGBUS: 'bus',
            signal.SIGFPE: 'fpe',
            signal.SIGUSR1: 'usr1',
            signal.SIGSEGV: 'segv',
            signal.SIGUSR2: 'usr2',
            signal.SIGPIPE: 'pipe',
            signal.SIGALRM: 'alrm',
            signal.SIGTERM: 'term'
        }

        signalCode = -tracerProcess.returncode
        
        if logsFullPath == "":
            logsFullPath = '/home/boc/genetic-algorithm-with-Spark-for-test-generation/logs' 
        folder = logsFullPath + '/crash/' + error_type[signalCode]

        # Create folder if it doesn't exist
        os.makedirs(folder, exist_ok=True)

        # Create new file and save the input that caused the crash
        from uuid import uuid4
        file_name = error_type[signalCode] + '-' + str(uuid4())

        with open(folder + '/' + file_name + '.bin', 'wb') as f:
            f.write(bytearray(inputString))


    def processDataStream(self, dataStream, streamSize):
        hashForEdges = set()  # We don't count an edge if it appears twice
        pathProbability = 1.0

        # Caching some variables for faster access
        entryType_TestName = self.entryTemplate.TN
        entryType_Module = self.entryTemplate.TM
        entryType_Offset = self.entryTemplate.TO

        streamPos = 0
        currModuleName = None
        currentOffsetToEntryIndex = None
        prevEntryIndex = -1
        firstItem = 1
        while streamPos < streamSize:
            currOffset = -1

            entry           = utils.getNextEntryFromStream(dataStream, streamPos, self.entryTemplate)
            type            = entry[0]
            len             = entry[1]
            moduleString    = entry[2]
            currOffset      = entry[3]
            cost            = entry[4]
            jumpType        = entry[5]
            entrySize       = entry[6]
            jumpInstruction = entry[7]
            nInstructions   = entry[8]
            nextModule      = entry[9]
            nextoffset      = entry[10]

            streamPos += entrySize

            if type == entryType_Module:
                currModuleName = moduleString
                currentOffsetToEntryIndex = self.Mapping[currModuleName] if currModuleName in self.Mapping else None    # Update the current map to search to
            elif type == entryType_Offset:
                # use here currModuleName#offset

                # Find the current entry index
                currEntryIndex = -1
                if currentOffsetToEntryIndex is not None and currOffset in currentOffsetToEntryIndex:
                    currEntryIndex = currentOffsetToEntryIndex[currOffset]

                if firstItem == 0:  # Don't compute probabilities for the first item because it can be misunderstood as no edge in probabilities graph
                    isNewEdge = True
                    bothNodesAreKnown = currEntryIndex != -1 and prevEntryIndex != -1
                    if bothNodesAreKnown:  # If one of the node doesn't exist always consider it a new edge.
                        isNewEdge = not (prevEntryIndex, currEntryIndex) in hashForEdges
                        if isNewEdge:
                            hashForEdges.add((prevEntryIndex, currEntryIndex))

                    if isNewEdge:
                        edgeProb = self.getEdgeProbability(prevEntryIndex,
                                                           currEntryIndex) if bothNodesAreKnown else self.noEdgeProbability
                        pathProbability = pathProbability * edgeProb

                firstItem = 0
                prevEntryIndex = currEntryIndex

            elif type == entryType_TestName:
                continue  # we are not interested in this type of data

        return 1.0 - pathProbability

    # Get the probability of an edge knowing the probability map and the
    # noEdgeProbability value, as defined in the computeProbabilitiesMap function.
    def getEdgeProbability(self, idA, idB):
        neighbOfA = self.ProbabilityMap[idA]  # get the dictionary of neighboors for node idA
        if neighbOfA == None:
            return self.noEdgeProbability

        edgeValue = neighbOfA.get(idB)
        return edgeValue if edgeValue != None else self.noEdgeProbability

    # This function currently tests the program against an input,
    # gets the Trace and computes the probability of the path.
    # Fitness score is 1-pathProbability.
    # We don't consider same edge twice.
    # We must play/improve this a lot. E.g. - consider that first part of
    # the path could be very common and this should influence less the costs.
    def evaluate(self, inputString):
        streamData, streamSize = self.getTrace(inputString)
        return self.processDataStream(streamData, streamSize)



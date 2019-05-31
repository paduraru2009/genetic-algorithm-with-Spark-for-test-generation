# TODO cpaduraru: try to use spark in an efficient way to compute the probabilities. Currently running serially

# The functions and data structure in this module are used to update the probabilities of each CFG transition between different generations
# Each generation output is currently represented by a folder of traces. 
# We store some persistent data structure and at each new generation of outputs we add the delta from this one

import os
import utils
import struct

from parse import *

#Persistent data - stores data from all test folder discovered until now
# Deltas are uploaded in updateNewGeneration function
#-----------------------------------------------------------------------------------

globalEntriesCounter = 0 # From this we generate the indices of module#offset entries

blockOffsetToIndex = {}		# converting from a block#offset pair to an index.  blockOffsetToIndex[moduleName][offset] = index
#indexToBlockOffset= []		# inverse of above

# countTraversalsFromNode[x] represents the total number of traversals made from x to all its neighbours. It is a dictionary since we could possibly add new block#offset indices
countTraversalsFromNode = {}

# numTransitions[x][y] gives the number of occurrences of edge (x,y) in registered data. When init numTransitions[x] = {} (map).
# On update: if y not in numTransitions[x] then numTransitions[x][y]=1 else numTransitions[x][y] ++
# numTransitions[x][y] = numTransitions[x][y]+1.
numTransitions = {}

#---------------------------

# Temporary data - optimized data structures used to query probabilities for the current generation
#------------------------------------------------
# The benefit of this is that probability query is used way more times than the single pass computation of deltas.
Probability =[] #Probability[x].find(y) returns value ; Probability[x] represent a map {(y,value)}, where y are neighbors and value are the probability of (x,y)

# The noEdgeProbability represents the value to use in fitness evaluation when an edge was not encountered yet in the probabilities map
# go through entire map, find minimum and divide it by 10 for example
noEdgeProbability = 0
#---------------------------

def updateFromFolder(folderPath, entryTemplate):
    #(IGNORE - dosn't worth the effort since now it's a static / quick operation)TODO CPADURARU: since every machine writes output to a single file, this is highly parallelizable. So create a task for each then merge results.
    # Caching some variables for faster access
    entryType_TestName              = entryTemplate.TN
    entryType_Module                = entryTemplate.TM
    entryType_Offset                = entryTemplate.TO

    os.makedirs(folderPath, exist_ok=True)
    for filename in os.listdir(folderPath):
        fileDescriptor = open(folderPath + "/" + filename , "rb")
        fileDescriptor.seek(0, os.SEEK_END)
        streamSize = fileDescriptor.tell()
        fileDescriptor.seek(0, os.SEEK_SET)
        streamData = fileDescriptor.read()

        streamPos = 0
        currModuleName = None
        currentOffsetToEntryIndex = None # current lookup map
        global blockOffsetToIndex
        global globalEntriesCounter
        prevBlockOffsetEntry_Index = -1

        while streamPos < streamSize:
            entry           = utils.getNextEntryFromStream(streamData, streamPos, entryTemplate)
            type            = entry[0]
            len             = entry[1]
            moduleString    = entry[2]
            currOffset      = entry[3]
            cost            = entry[4]
            jumpType        = entry[5]
            entrySize       = entry[6]

            streamPos += entrySize

            if type == entryType_Module:
                currModuleName = moduleString

                # Check first if module is in dictionary, if not add it
                if currModuleName not in blockOffsetToIndex:
                    blockOffsetToIndex[currModuleName] = {}

                # Update the current offset to entryIndex map
                currentOffsetToEntryIndex = blockOffsetToIndex[currModuleName]
            elif type == entryType_Offset:
                # Check the offset in the map
                blockOffsetEntry_Index = -1
                if currOffset not in currentOffsetToEntryIndex:
                    currentOffsetToEntryIndex[currOffset] = globalEntriesCounter
                    blockOffsetEntry_Index = globalEntriesCounter
                    globalEntriesCounter += 1
                else:
                    blockOffsetEntry_Index = currentOffsetToEntryIndex[currOffset]

                # Update the counters
                global countTraversalsFromNode
                global numTransitions
                if prevBlockOffsetEntry_Index != -1:
                    if prevBlockOffsetEntry_Index not in countTraversalsFromNode:
                        countTraversalsFromNode[prevBlockOffsetEntry_Index] = 1
                    else:
                        countTraversalsFromNode[prevBlockOffsetEntry_Index] += 1

                    if prevBlockOffsetEntry_Index not in numTransitions:
                        numTransitions[prevBlockOffsetEntry_Index] = {}

                    if blockOffsetEntry_Index not in numTransitions[prevBlockOffsetEntry_Index]:
                        numTransitions[prevBlockOffsetEntry_Index][blockOffsetEntry_Index] = 1
                    else:
                        numTransitions[prevBlockOffsetEntry_Index][blockOffsetEntry_Index] += 1

                prevBlockOffsetEntry_Index = blockOffsetEntry_Index
            elif type == entryType_TestName:
                continue  # we are not interested in this type of data

    constructProbabilitiesMap()

def constructProbabilitiesMap():
    numModules = len(blockOffsetToIndex)

    global Probability
    Probability = [None]*globalEntriesCounter
    global noEdgeProbability
    minProbability = 1

    for moduleName in blockOffsetToIndex:
        offsetToIndexMap = blockOffsetToIndex[moduleName]
        for offset in offsetToIndexMap:
            x = offsetToIndexMap[offset]

            Probability[x] =  {}
            if not x in numTransitions:
                continue

            numTransitionsOf_X        = numTransitions[x]
            countTraversalsFromNode_X = countTraversalsFromNode[x]
            assert (countTraversalsFromNode_X > 0)
            for y in numTransitionsOf_X:
                probXY = numTransitionsOf_X[y] / countTraversalsFromNode_X
                Probability[x][y] = probXY
                if probXY < minProbability:
                    minProbability = probXY

    noEdgeProbability = minProbability * 0.2

# Verify if x, either as a (block + offset) string or as a integer is fine or not
def getNormalizedVertex(x):
    return blockOffsetToIndex[x]

def getEdgeProbabilityWithStringVertices(vertex1, vertex2):
    vertex1 = getNormalizedVertex(vertex1)
    if vertex1 == -1:
        return noEdgeProbability
    vertex2 = getNormalizedVertex(vertex2)
    if vertex2 == -1:
        return noEdgeProbability

    return getEdgeProbability(vertex1, vertex2)

# Considering that vertex1 and vertex2 are nodes for speed
def getEdgeProbability(vertex1, vertex2):
    if not vertex1 in Probability:
        return noEdgeProbability

    if not vertex2 in Probability[vertex1]:
        return noEdgeProbability

    return Probability[vertex1][vertex2]

def main():
    separator = "+++++++++++++++++++++++++++++++++++++++++++++++++++++"

    params = utils.readParams()
    entryTemplate = params.entryTemplate

    # Test 1
    inputFilePath_initial = utils.getFolderPathFromId(0)
    updateFromFolder(inputFilePath_initial, entryTemplate)

    # input file path hardcoded in getEdgeProbability()
    #print (Probability)
    #print(getEdgeProbabilityWithStringVertices("name1", "name2"), separator)
    print(getEdgeProbability(0, 1), separator)
    print(getEdgeProbability(0, 2), separator)

    #updateFromFolder(utils.getFolderPathFromId(1))
    print("Probabilities " + str(Probability))
    print ("Count " + str(countTraversalsFromNode))
    print ("NumTransitions " + str(numTransitions))
    print(getEdgeProbability(3, 1), separator)

    '''
    {0: {1: 0.75, 2: 0.25}, 1: {2: 0.5, 3: 0.5}, 2: {}, 3: {2: 1.0}}
    0.75 +++++++++++++++++++++++++++++++++++++++++++++++++++++
    0.75 +++++++++++++++++++++++++++++++++++++++++++++++++++++
    0.25 +++++++++++++++++++++++++++++++++++++++++++++++++++++
    Probabilities {0: {1: 0.6, 2: 0.2, 3: 0.2}, 1: {2: 0.5, 3: 0.5}, 2: {1: 1.0}, 3: {2: 1.0}}
    Count {0: 5, 1: 2, 2: 1, 3: 2}
    NumTransitions {0: {1: 3, 2: 1, 3: 1}, 1: {2: 1, 3: 1}, 2: {1: 1}, 3: {2: 2}}
    0.020000000000000004 +++++++++++++++++++++++++++++++++++++++++++++++++++++
    '''

if __name__ == "__main__":
    main()

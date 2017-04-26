import os
import utils
import sys
import subprocess
import time
import struct

'''
def createCommand(Params):
    command = [Params.simpleTracerPath, "--payload", Params.testProgramName, "--outfile", "stdout", #"--disableLogs",
           "--flow", "--binlog", "--binbuffered", "--writeLogOnFile"]

    return command
'''

# writes to a process's pipe a variable encoded in numBytes
def writeToProcess(var, process, numBytes, doFlush=True):
    process.stdin.write(var.to_bytes(numBytes, 'little'))
    process.stdin.flush()

def processDataStream(dataStream, streamSize, entryTemplate):

    # Caching some variables for faster access
    entryType_TestName              = entryTemplate.TN
    entryType_Module                = entryTemplate.TM
    entryType_Offset                = entryTemplate.TO

    streamPos = 0
    prevModuleName = ''
    prevOffset = -1
    while streamPos < streamSize:
        currModuleName = prevModuleName
        currOffset = -1
        entry = utils.getNextEntryFromStream(dataStream, streamPos, entryTemplate)

        type            = entry[0]
        len             = entry[1]
        moduleString    = entry[2]
        offset          = entry[3]
        cost            = entry[4]
        jumpType        = entry[5]
        entrySize       = entry[6]

        streamPos += entrySize

        if type == entryType_Module:
            currModuleName = moduleString
            prevModuleName = currModuleName
        elif type == entryType_Offset:
            # use here currModuleName#offset
            print(str(currModuleName) + str(offset))
        elif type == entryType_TestName:
            continue # we are not interested in this type of data

'''
def simulateCommText(Params, inputString):
    command = createCommand(Params)
    p = subprocess.Popen(command, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)  # fully buffered, PIPE read/write

    # write input len
    writeToProcess(int(len(inputString)), p, 4)

    entryFtm = 'I h h I'
    entrySize = struct.calcsize(entryFtm)
    # alignment = 4  # this is the header alignment. how can we get this from code ?
    # alignmentMask = ~(alignment - 1)

    for i in range(0, 1):
        # Write a new input payload
        utils.writeToProcess(1, p, 1, False)
        payloadInput = bytearray(inputString, 'utf8')
        p.stdin.write(payloadInput)
        p.stdin.flush()

        # Read the size of the returned buffer and data
        streamData = p.stdout.readline().decode('utf8').split("&");
        for line in streamData:
            print(line)

    # Write a message to let to other end know that it's over
    writeToProcess(0, p, 1)

    # Read any garbabe output ? More like a check to make sure nothing is left behind
    while (p.poll()):
        garbageOutput = p.stdout.read()
        print("Garbage output !! " + garbageOutput)

        # close
'''

def simulateCommBinary(p, Params, inputString):
    # alignment = 4  # this is the header alignment. how can we get this from code ?
    # alignmentMask = ~(alignment - 1)

    for i in range(0, 10000):
        # Write a new input payload
        writeToProcess(1, p, 1, False)
        payloadInput = bytearray(inputString, 'utf8')
        p.stdin.write(payloadInput)
        p.stdin.flush()

        # Read the size of the returned buffer and data
        streamSize = struct.unpack("I", p.stdout.read(4))[0]
        #print(streamSize)
        streamData = p.stdout.read(streamSize)

        processDataStream(streamData, streamSize, Params.entryTemplate)

        print("==============================")

    # Write a message to let to other end know that it's over
    writeToProcess(0, p, 1)

    # Read any garbabe output ? More like a check to make sure nothing is left behind
    while (p.poll()):
        garbageOutput = p.stdout.read()
        print("Garbage output !! " + garbageOutput)

        # close


def main(argv=None):
    Params = utils.readParams()

    print ("simple tracer path " + Params.simpleTracerPath + " " + Params.testProgramName)
    inputString = "ciprian paduraru este un programator sa vedem ce iese acu"

    # create the process
    command = utils.createTracerCmd(Params)
    p = subprocess.Popen(command, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)  # fully buffered, PIPE read/write

    # write input len
    utils.writeToProcess(int(len(inputString)), p, 4)

    simulateCommBinary(p, Params,inputString)
    #simulateCommText(Params, inputString)





if __name__ == "__main__":
    sys.exit(main())

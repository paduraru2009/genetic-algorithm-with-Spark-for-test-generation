import sys
from population import Population
import utils

class Worker:
    'Worker class that holds a population and operations over it'
    # comment

    def __init__(self,
                 evalFunctor,  # self explaining
                 populationSize,  # how big is the population
                 individualLength,  # length of an individual (number of bytes in the input in our case)
                 maxIterations,  # max iterations for new generations
                 elitismPercent,  # percent of the best individula from the old population to store in the new one
                 oldGenerationSelectProbability,  # How many individuals to select randomly from the old population that are not elite (ignoring their scores). Reason - create more diversity
                 mutateProbability,  # probability of a mutation
                 deltaMutateProbability,  # how much to increase mutation probability if we are stuck
                 epsilonToIncreaseMutation, # if nothing changes between consecutive generations ( avgFitness(Generation1) - avgFitness(Generation2) < epislon) go and apply the deltaMutate
                 runningInParallel, tracerProcessCmd, tracerProcessPayloadSize): # need to know this in order to do some different code / serialization / optimizations

        # Immutable members internal members # TODO how to maark them better ?
        self.evalFunctor = evalFunctor
        self.evalFunctor.parentWorker = self
        self.retainPercent = elitismPercent
        self.oldGenerationSelectP = oldGenerationSelectProbability
        self.individualLength = individualLength
        self.populationSize = populationSize
        self.maxIterations = maxIterations
        self.baseMutateP = mutateProbability
        self.deltaMutateP = deltaMutateProbability
        self.epsilonToIncreaseMutation = epsilonToIncreaseMutation

        # Mutable memebers
        self.population = Population(evalFunctor, individualLength, populationSize)
        self.currentMutateP = mutateProbability
        self.isRunningInParallel = runningInParallel
        self.tracerProcessCmd = tracerProcessCmd
        self.tracerProcessPayloadSize = tracerProcessPayloadSize

    def getFitness(self, individual):
        return self.evalFunctor(individual) # individual is a string stream for the test program

    def __str__(self):
        return str(self.population)

    def adjustMutationRatio(self, genId, debugEachGeneration):
        # Do mutation adjustements if not getting any improvements. TODO: move this func and parameters to a class to simulate a strategy pattern
        # At each 5 th generations if avg fitness doesn't modify try to increase mutation probability. Could do at each iteration but doesn't worth the cycles probably
        if genId % 5 == 0:
            avgFitness = self.population.getAvgFitness();
            #print("generation " + str(genId) + " avg fitness " + str(avgFitness))
            if abs(self.lastAvgFitness - avgFitness) < self.epsilonToIncreaseMutation:
                self.currentMutateP = self.baseMutateP + self.deltaMutateP

                if debugEachGeneration:
                    print ("using the extended mutation probability " + str(self.currentMutateP))
            else:
                self.currentMutateP = self.baseMutateP

                if debugEachGeneration:
                    print ("Returning back to normal mutation probability " + str(self.currentMutateP))

            self.lastAvgFitness = avgFitness

    # Combines the best results from both
    def combine(self, other):
        self.population.combine(other.population)

    # Static reduce function
    def reduce(worker1, worker2):
        worker1.combine(worker2)
        return worker1

    def updateTracerProcess(self):
        if self.isRunningInParallel:
            self.evalFunctor.tracerProcess = utils.createTracerProcess(self.tracerProcessCmd, self.tracerProcessPayloadSize)

    # Generates a specified number of iterations
    def solve(self, debugEachGeneration=False):

        # TODO CPaduraru: workaround - Need to create the process at each new folder step. Still a huge improvement but would be nice if someone on stackoverflow would respond me how to serialize a process / keep one per executor
        self.updateTracerProcess();

        self.lastAvgFitness = sys.float_info.max
        self.population.generateRandom()

        for genId in range(self.maxIterations):
            if debugEachGeneration:
                print("========== Generation " + str(genId) + " ==========")
                print(str(self))

            # internal update of the generation
            self.population.updateGeneration(self.retainPercent, self.oldGenerationSelectP, self.currentMutateP)

            # Do mutation adjustements if not getting any improvements
            self.adjustMutationRatio(genId, debugEachGeneration)

        # TODO CPaduraru: workaround - stop the process - see the comment above
        if self.isRunningInParallel:
            utils.stopTracerProcess(self.evalFunctor.tracerProcess)
            self.evalFunctor.tracerProcess = None

        return self

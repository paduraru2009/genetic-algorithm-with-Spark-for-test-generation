from random import randint, random
from operator import add
from functools import reduce

class Population:
	# each individual has a fitness, 1:1 to self.population but keeping this independent for cache optimization.
	def __init__(self, fitnessFunctor, individualLen, populationSize):
		self.individuals = []
		self.individualsFitness = []
		self.fitnessFunctor = fitnessFunctor
		self.individualLen = individualLen
		self.populationSize = populationSize

	def addIndividual(self, individual, computeFitness = True):
		self.individuals.append(individual)
		if computeFitness:
			self.individualsFitness.append(self.fitnessFunctor.evaluate(individual))

	def computeFitnessForInitialPopulation(self): # TODO CPaduraru: delete this after we solve the Spark - process spawn optimization and move the code back in addIndividual
		for individual in self.individuals:
			self.individualsFitness.append(self.fitnessFunctor.evaluate(individual))

	# use this variant when fitness is already known for individual to avoid recomputation
	def addIndividualKnownFitness(self, individual, fitness):
		self.individuals.append(individual)
		self.individualsFitness.append(fitness)

	def clear(self):
		self.individuals.clear()
		self.individualsFitness.clear()

	def getSize(self):
		return len(self.individuals)

	def sanityCheck(self):
		assert len(self.individuals) == len(self.individualsFitness)

	def generateIndividual(self):
		'A chromosome in our population'
		return [randint(0, 255) for x in range(self.individualLen)]

	def generateRandom(self):
		for i in range(self.populationSize):
			individualRef = self.generateIndividual()
			self.addIndividual(individualRef)  # TODO CPaduraru: change this back to True when we solved things commented in main.py

	def getAvgFitness(self):
		sum = reduce(add, (x for x in self.individualsFitness))
		return sum / (len(self.individuals) * 1.0)

	def __str__(self):
		res = "{ Avg fitness" + str(self.getAvgFitness()) + " \n"
		for i in range(len(self.individuals)):
			res = res + str(self.individuals[i]) + " \n"
		res += "}"
		return res

	def getPopulation(self):
		return self.individuals

	# combine best population from this and other and return single population of the same size
	def combine(self, other):
		popLen = len(self.individuals)
		assert popLen == len(other.individuals)

		combinedPopulation = []
		indices = [x for x in range(2*popLen)] # Indices [0,N-1] representing this set, [N, 2*N-1] the other set
		combinedFitness = self.individualsFitness + other.individualsFitness
		indices = sorted(indices, key=lambda a: combinedFitness[a])

		# select the best individuals now
		newPopulation = Population(self.fitnessFunctor, self.populationSize, self.individualLen)
		for i in range(popLen):
			ithIndex = indices[i]
			target,index = (self,ithIndex) if ithIndex < popLen else (other, ithIndex-popLen)
			newPopulation.addIndividualKnownFitness(target.individuals[index], target.individualsFitness[index])

		self.individuals 		= newPopulation.individuals
		self.individualsFitness	= newPopulation.individualsFitness

	def updateGeneration(self, elitismPercent, oldGenerationSelectProbability, currentMutateProbability):
		# just cache some variables
		populationSize = self.populationSize
		individualLen = self.individualLen

		# Sort population by fitness (get fitness for all first instead of recomputing multiple times at sort)
		indices = [x for x in range(populationSize)]
		sortedIndices = [sorted(indices, key=lambda a: self.individualsFitness[a])]

		# Keep the best part from the old generation
		retainCount = int(populationSize * elitismPercent)
		newPopulation = Population(self.fitnessFunctor, populationSize, individualLen)
		for i in range(retainCount):
			ithIndex = indices[i]
			newPopulation.addIndividualKnownFitness(self.individuals[ithIndex], self.individualsFitness[ithIndex])

		# Randomly add other individuals to promote genetic diversity
		for i in range(retainCount, populationSize):
			if oldGenerationSelectProbability > random():
				ithIndex = indices[i]
				newPopulation.addIndividualKnownFitness(self.individuals[ithIndex], self.individualsFitness[ithIndex])

		# Mutate some individuals. Q: from the old population or the new one ?!
		for i, individual in enumerate(self.individuals):
			if currentMutateProbability > random():
				mutatePosition = randint(0, individualLen - 1)
				individual[mutatePosition] = randint(0, 255)  # change the value of the byte

		# Crossover. Q : from the old population or the new one ?!
		neededNewIndividuals = populationSize - newPopulation.getSize()
		while neededNewIndividuals > 0:
			idA = randint(0, populationSize - 1)
			idB = randint(0, populationSize - 1)
			if (idA != idB):
				A = self.individuals[idA]
				B = self.individuals[idB]

				limit = max(individualLen - 2, 1)
				crossPos = randint(1, limit)
				result = A[:crossPos] + B[crossPos:]

				newPopulation.addIndividual(result)
				neededNewIndividuals -= 1

		assert newPopulation.getSize() == self.populationSize
		self.individuals 		= newPopulation.individuals
		self.individualsFitness = newPopulation.individualsFitness

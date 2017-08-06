# python3 runClass2.py /Users/Laura/Desktop/Dissertation/data/phonetic_stoplist.txt /Users/Laura/Desktop/Dissertation/data/english/NWF089/NWF089-praat-1.txt /Users/Laura/Desktop/Dissertation/data/english/NWF089/NWF089-vs-1.txt
import csv
import random
from sklearn import svm, metrics
from sklearn.svm import SVC
from sklearn.metrics import precision_recall_fscore_support, mean_squared_error
from sklearn.model_selection import cross_val_predict, StratifiedShuffleSplit, GridSearchCV
from matplotlib import rc
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt
import numpy as np
import itertools
import argparse
import statistics
import pandas as pd
import sys
import itertools
from statsmodels.tools import tools
import ARPABETconversion as arpa

# Set font for plots to use CM from LaTeX
def setFont():
	rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
	params = {'backend': 'ps',
		'axes.labelsize': 25,
		'text.fontsize': 25,
		'legend.fontsize': 10,
		'xtick.labelsize': 15,
		'ytick.labelsize': 15,
		'text.usetex': True}
	plt.rcParams.update(params)

# Inputs should be path for stop list and path for data files (Praat, VS)
def parseArgs():
	parser = argparse.ArgumentParser()
	parser.add_argument("stoplist")
	parser.add_argument("praat")
	parser.add_argument("VS")
	return parser.parse_args()

# Make a list from a file of words
# Use this for the stop words to be excluded
def getStopWords(filename):
	stopWords = []
	with open(filename) as f:
		for line in f:
			line = line.strip().upper()
			stopWords.append(line)
	return stopWords

# Remove anything but B M C
# Return array of data and list of headers
# x is the index of the column containing labels
def prepData(filename, x):
	data = []
	phonationLabs = ["B", "C", "M"]
	with open(filename) as f:
		count = 0
		reader = csv.reader(f, delimiter = "\t")
		header = next(reader)
		for line in reader:
			count += 1
			if line[x] in phonationLabs:
				data.append(line)
	print("Vowels, total:", count)
	data = np.array(data)
	return data, header

# Combines Praat and VS data
# At this point, 0 and 1 have been removed but stop words have not; undefined remains
def combineData(praat, VS):
	data = np.concatenate((praat, VS), axis = 1)
	print("Vowels, without 0 or 1:", len(data))
	return data

# Removes stop words
def remStopWords(data, stopWords):
	remove = []
	for row in data:
		remove.append(row[5] not in stopWords)
	remove = np.array(remove)
	data = data[remove]
	#np.savetxt('/Users/Laura/Desktop/out.txt', data, fmt = '%s')
	print("Vowels, without stop words, 0, or 1:", len(data))
	return data

# Returns an array with lists of features (x) and a list of labels (y)
def pickFeatures(data):
	xlist = [] # x = features
	y = [] # y = labels
	speakerList = []
	for row in data:
		# local jitter, CPP mean, energy mean, HNR25, strF0
		xline = [row[8], row[82], row[83], row[86], row[104]] 
		xlist.append(xline) 
		y.append(row[6])
		speakerList.append(row[0])
	x = np.array(xlist)
	return x, y, speakerList

# Count measured that are "undefined"
# Replace "undefined" with 1
def undefined(x):
	udefCount = 0
	for row in x:
		for i in range(len(row)):
			if row[i] == '--undefined--':
				udefCount += 1
				row[i] = 1 # Change this line to change what --undefined-- becomes
	x = x.astype(float)
	return x

# Returns the confusion matrix, including sums
def confusionMatrix(trainy, predictedy):
	y_actu = pd.Series(trainy, name='Actual')
	y_pred = pd.Series(predictedy, name='Predicted')
	df_confusion = pd.crosstab(y_actu, y_pred, rownames=['Actual'], colnames=['Predicted'], margins=True)
	return df_confusion

# Calculates precision, recall, fscore, and support
def prfs(trainy, predictedy):
	y_true = np.array(trainy)
	y_pred = np.array(predictedy)
	return precision_recall_fscore_support(y_true, y_pred, average = 'weighted')

# Z-normalizes one feature by speaker
# Takes an array of all data, a corresponding list of speakers, and feature to normalize
# bySpeaker: key = speaker; value = list of 
def zNorm(x, speakerList, index):
	bySpeaker = {}
	# For each row in x
	for i in range(len(x)):
		# If that speaker isn't yet in the dictionary:
		if speakerList[i] not in bySpeaker:
			# Add that speaker to the dictionary with an empty value
			bySpeaker[speakerList[i]] = []
		# Add the row # at the index to the value list
		bySpeaker[speakerList[i]].append(i)
	# For each key's value list
	for valList in bySpeaker.values():
		# Make temporary list of actual measures for each speaker
		tempList = []
		# For each value in the value list (which is actually a row #):
		for val in valList:
			# Find the actual # it represents
			measure = x[val,index]
			# Add that measure to tempList
			tempList.append(measure)
		# Get mean of values in tempList
		featureMean = statistics.mean(tempList)
		# Get STD of values in tempList
		featureSTD = statistics.stdev(tempList)
		# For each number in tempList
		for i in range(len(tempList)):
			# Calculate z score (jitter - mean)/STD
			zmeasure = ((tempList[i] - featureMean) / featureSTD)
			x[valList[i],index] = zmeasure

# Runs z normalization over whatever features listed
def zNormFeatures(x, speakerList, featureList):
	for feature in featureList:
		zNorm(x, speakerList, feature)

def addPitchDiff(data):
	VoPTAdd = []
	for row in data:
		VoPT = [0]
		strF0 = row[40]
		sF0 = row[41]
		pF0 = row[42]
		shrF0 = row[43]
		tracks = [strF0, sF0, pF0, shrF0]
		pairs = (list(itertools.combinations(tracks, 2)))
		for pair in pairs:
			a = float(pair[0])
			b = float(pair[1])
			diff = abs(a - b)
			VoPT[0] += diff
		VoPTAdd.append([VoPT[0]])
	data = np.append(data, VoPTAdd, 1)
	#np.savetxt('/Users/Laura/Desktop/out-vopt.txt', data, fmt = '%s')
	return data

def main():
	setFont()
	args = parseArgs()
	praatData, praatHeader = prepData(args.praat, 4)
	VSData, VSHeader = prepData(args.VS, 1)
	data = combineData(VSData, praatData)
	stopWords = getStopWords(args.stoplist)
	data = remStopWords(data, stopWords)
	daata = addPitchDiff(data)
	#x, y, speakerList = pickFeatures(data)
	#x = undefined(x)
	#featureList = [0, 1, 2] # Pick features to normalize here
	"""
	zNormFeatures(x, speakerList, featureList)
	# Shuffle?
	clf = svm.SVC()
	predictedy = cross_val_predict(clf, x, y, cv = 10)
	p, r, f, s = prfs(y, predictedy)
	print("Precision: ", p)   
	print("Recall: ", r)
	print("F-score: ", f)  
	print("Accuracy:", metrics.accuracy_score(y, predictedy))
	print("-------------------------")
	print(confusionMatrix(y, predictedy))
"""

"""	
# Grid search - not tested yet in smaller version
	C_range = np.logspace(-3, 2, 6)
	gamma_range = np.logspace(-3, 2, 6)
	param_grid = dict(gamma=gamma_range, C=C_range)
	cv = StratifiedShuffleSplit(n_splits=10, test_size=0.1, random_state=42)
	grid = GridSearchCV(clf, param_grid=param_grid, cv=cv)
	grid.fit(x, y)
	print("The best parameters are %s with a score of %0.2f"
      % (grid.best_params_, grid.best_score_))
"""

if __name__ == "__main__":
	main()
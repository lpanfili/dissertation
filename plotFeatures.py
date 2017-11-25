# Makes a bar plot of correlations, weights, or importances
# Colors = categories
# y-axis = metric

import matplotlib.pyplot as plt
from matplotlib import rc
import pandas as pd
import argparse
import numpy as np
import matplotlib.patches as mpatches

# Two args, lg and metric
def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('features_csv', type = str, help = 'features csv location')
	parser.add_argument('lg', type = str, help = 'three letter language code')
	parser.add_argument('metric', type = str, help = 'corr, weight, imp, abl')
	return parser.parse_args()


# Use LaTeX font
def set_font():
	rc('font',**{'family':'serif','serif':['Computer Modern Roman']})
	params = {'backend': 'ps',
		'axes.labelsize': 15,
		'text.fontsize': 15,
		'legend.fontsize': 13,
		'xtick.labelsize': 15,
		'ytick.labelsize': 15,
		'text.usetex': True}
	plt.rcParams.update(params)


# Makes and returns a dataframe from each contrast
def get_data_corr(lg):
	path = "../data/lgs/" + lg + "/" + lg + "-corr-all.csv"
	data = pd.read_csv(path, na_values = "")
	data = data.set_index(['Unnamed: 0'])
	BC = data['BC-corr'].copy()
	BM = data['BM-corr'].copy()
	CM = data['CM-corr'].copy()
	return data, BC, BM, CM

def get_data_imp(lg):
	path = "../data/lgs/" + lg + "/" + lg + "-importance_rs.csv"
	data = pd.read_csv(path, na_values = "")
	data = data.set_index(['feat'])
	data = data['importance'].copy()
	return data

def get_data_weight(lg):
	path = "../data/lgs/" + lg + "/" + lg + "-weights-rs.csv"
	data = pd.read_csv(path, na_values = "")
	data = data.set_index(['feat'])
	if lg == 'cmn':
		CM = data['CM-weight'].copy()
		BC = ""
		BM = ""
	elif lg == 'guj':
		BM = data['BM-weight'].copy()
		BC = ""
		CM = ""
	else:
		BC = data['BC-weight'].copy()
		BM = data['BM-weight'].copy()
		CM = data['CM-weight'].copy()
	return data, BC, BM, CM


# Makes and returns a list of tuples for just one contrast
# Feature, metric
def make_list_contrast(data):
	feat_val_list = []
	feat_dict = data.to_dict()
	for feat in feat_dict:
		pair = [feat, feat_dict[feat]]
		feat_val_list.append(pair)
	return feat_val_list


def plot_feat(feat_val_list, features_csv, metric, lg, title):
	# Sort by absolute value
	feat_val_list.sort(key = lambda x: abs(x[1]), reverse = True)
	feat, val = zip(*feat_val_list)
	colors = get_color(feat, features_csv)
	val = [abs(n) for n in val] # Convert to absolute values
	# Plot
	x_pos = np.arange(len(feat))
	plt.bar(x_pos, val, color = colors, edgecolor = "none")
	plt.xlabel('Feature')
	if metric == 'corr':
		plt.ylabel('Correlation (Absolute Value)')
	if metric == 'imp':
		plt.ylabel('Importance')
	if metric == 'weight':
		plt.ylabel('Weight (Absolute Value)')
	plt.xticks([])
	f0 = mpatches.Patch(color = '#a6cee3', label = 'f0')
	vopt = mpatches.Patch(color = '#1f78b4', label = 'VoPT')
	jitter = mpatches.Patch(color = '#000080', label = 'Jitter')
	cpp = mpatches.Patch(color = '#b2df8a', label = 'CPP')
	rmse = mpatches.Patch(color = '#33a02c', label = 'RMS Energy')
	shimmer = mpatches.Patch(color = '#fb9a99', label = "Shimmer")
	hnr = mpatches.Patch(color = '#e31a1c', label = 'HNR')
	shr = mpatches.Patch(color = '#fdbf6f', label = 'SHR')
	tilt = mpatches.Patch(color = '#ff7f00', label = "Spectral Tilt")
	f1 = mpatches.Patch(color = '#cab2d6', label = 'F1')
	dur = mpatches.Patch(color = '#6a3d9a', label = 'Duration')
	pos = mpatches.Patch(color = '#ffff99', label = 'Prosodic Position')
	surr = mpatches.Patch(color = '#b15928', label = 'Surrounding Phones')
	plt.legend(handles=[f0, vopt, jitter, cpp, rmse, shimmer, hnr, shr, tilt, f1, dur, pos, surr])
	plt.title(title)
	plt.show()


# Make the list of colors that corresponds with the feature categories
def get_color(feat, features_csv):
	colors = []
	color_dict = {
		'5': '#a6cee3', # f0
		'11': '#1f78b4', # VoPT
		'8': '#000080', # jitter
		'1': '#b2df8a', # CPP
		'2': '#33a02c', # RMSE
		'9': '#fb9a99', # shimmer
		'3': '#e31a1c', # HNR
		'4': '#fdbf6f', # SHR
		'0': '#ff7f00', # Tilt
		'6': '#cab2d6', # F1
		'7': '#6a3d9a', # dur
		'10': '#ffff99', # prosodic pos
		'12': '#b15928' # surrounding
	}
	features_all = pd.read_csv(features_csv)
	features = pd.concat([features_all['feature'], features_all['category']], axis = 1)
	features = features.set_index(['feature'])
	category_dict = features.to_dict()
	category_dict = category_dict['category']
	for i in feat:
		category = category_dict[i]
		colors.append(color_dict[category])
	return colors


# Adds a column for the category of the data
def group_features(data, features_csv):
	features_all = pd.read_csv(features_csv)
	features = pd.concat([features_all['feature'], features_all['category']], axis = 1)
	features = features.set_index(['feature'])
	category_dict = features.to_dict()
	category_dict = category_dict['category']
	# Replace features in data with category numbers
	category_list = []
	for index, row in data.iterrows():
		category_list.append(category_dict[row[0]])
	category_list = pd.Series(category_list)
	data['Category'] = category_list.values
	return data



def make_title(lg, metric):
	if lg == 'eng':
		title = 'English'
	if lg == 'guj':
		title = 'Gujarati'
	if lg == 'hmn':
		title = 'Hmong'
	if lg == 'cmn':
		title = 'Mandarin'
	if lg == 'maj':
		title = 'Mazatec'
	if lg == 'zap':
		title = 'Zapotec'
	if metric == 'corr':
		title += ' Correlations'
	if metric == 'weight':
		title += ' SVM Weights'
	if metric == 'imp':
		title += ' RF Importance'
	if metric == 'abl':
		title += ' Ablation'
	return title

def main():
	args = parse_args()
	set_font()
	# Make partial title
	title = make_title(args.lg, args.metric)
	# Get the data depending on which information you want
	if args.metric != 'imp':
		if args.metric == 'corr':
			data, BC, BM, CM = get_data_corr(args.lg)
		if args.metric == 'weight':
			data, BC, BM, CM = get_data_weight(args.lg)
		# Plot for lgs with two-way contrast
		if args.lg == 'guj':
			BM_feat_val_list = make_list_contrast(BM)
			plot_feat(BM_feat_val_list, args.features_csv, args.metric, args.lg, title)
		elif args.lg == 'cmn':
			CM_feat_val_list = make_list_contrast(CM)
			plot_feat(CM_feat_val_list, args.features_csv, args.metric, args.lg, title)
		# Plot contrats + all for other lgs
		else:
			BC_feat_val_list = make_list_contrast(BC)
			BM_feat_val_list = make_list_contrast(BM)
			CM_feat_val_list = make_list_contrast(CM)
			plot_feat(BC_feat_val_list, args.features_csv, args.metric, args.lg, title + ', B vs. C')
			plot_feat(BM_feat_val_list, args.features_csv, args.metric, args.lg, title + ', B vs. M')
			plot_feat(CM_feat_val_list, args.features_csv, args.metric, args.lg, title + ', C vs. M')
			# All
			all_feat_val_list = BC_feat_val_list + BM_feat_val_list + CM_feat_val_list
			plot_feat(all_feat_val_list, args.features_csv, args.metric, args.lg, title +', All Contrasts')
	if args.metric == 'imp':
		data = get_data_imp(args.lg)
		feat_val_list = make_list_contrast(data)
		plot_feat(feat_val_list, args.features_csv, args.metric, args.lg, title)

# TODO: Add titles to plots
# TODO: Add ablation

if __name__ == "__main__":
	main()
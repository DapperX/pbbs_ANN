import sys
import ANNparse
import util
import math
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import scipy as sp

plt.rcParams.update({'font.size': 17})
plt.rc('legend', fontsize=11)

def lineGraph(x, y, figname, title = "", ylabel = "", xlabel= "", xscaleopt = "linear", yscaleopt = "linear"):
	plt.plot(x, y)
	plt.yscale(yscaleopt)
	plt.xscale(xscaleopt)
	plt.ylabel(ylabel)
	plt.xlabel(xlabel)
	plt.title(title, fontsize=17)
	plt.savefig(figname)
	plt.clf()

def multiLineGraph(x, y_range, labels, figname, title = "", ylabel="", xlabel="", xscaleopt = "linear", 
	yscaleopt = "linear"):
	for (y, l) in zip(y_range, labels):
		plt.plot(x, y, "-o", label = l)
	plt.yscale(yscaleopt)
	plt.xscale(xscaleopt)
	plt.ylabel(ylabel)
	plt.xlabel(xlabel)
	plt.title(title, fontsize=17)
	plt.legend()
	plt.tight_layout()
	figname = figname + ".png"
	plt.savefig(figname)
	plt.clf()

def multiLineMultiAxisGraph(x_range, y_range, labels, figname, title = "", ylabel="", xlabel="", xscaleopt="linear", yscaleopt = "linear", markers=[], colors=[], show_legend=True):
	if(markers != []):
		for (x, y, l, m, c) in zip(x_range, y_range, labels, markers, colors):
			plt.plot(x, y, m, color=c, label = l)
	else:
		for (x, y, l) in zip(x_range, y_range, labels):
			plt.plot(x, y, "-o", label = l)
	plt.yscale(yscaleopt)
	plt.xscale(xscaleopt)
	plt.ylabel(ylabel)
	plt.xlabel(xlabel)
	plt.title(title, fontsize=17)
	if (show_legend):
	  plt.legend()
	# plt.tight_layout()
	figname = figname + ".png"
	plt.savefig(figname)
	plt.clf()
	


def multiLineMultiAxisGraphSideLegend(x_range, y_range, labels, figname, title = "", ylabel="", xlabel="", xscaleopt="linear", yscaleopt = "linear", markers=[], colors=[]):
	if(markers != []):
		for (x, y, l, m, c) in zip(x_range, y_range, labels, markers, colors):
			plt.plot(x, y, m, color=c, label = l)
	else:
		for (x, y, l) in zip(x_range, y_range, labels):
			plt.plot(x, y, "-o", label = l)
	plt.yscale(yscaleopt)
	plt.xscale(xscaleopt)
	plt.ylabel(ylabel, fontsize=18)
	plt.xlabel(xlabel, fontsize=18)
	plt.title(title, fontsize=20)
	plt.legend(bbox_to_anchor=(1.04, 0), loc="lower left", fontsize=16)
	fig = matplotlib.pyplot.gcf()
	fig.set_size_inches(10, 5.5)
	plt.tight_layout()
	figname = figname + ".pdf"
	plt.savefig(figname)
	plt.clf()


x_range=[]
y_range=[]
labels=[]
markers=[]
# colors=[]
colors=["tab:blue", "tab:purple", "tab:orange", "tab:green", "tab:red", "tab:red", "tab:brown"]

for file_in in sys.argv[1:]:
	preamble, building, query = ANNparse.parser_kNN.parse(file_in)
	q_in_bucket = util.bucket_query(
		query, 
		list(range(0,5000,10)), 
		lambda q: q["ef"],
		lambda x,y: x if x["QPS"]>y["QPS"] else y
	)
	q_in_bucket = [qb for qb in q_in_bucket if qb[0] is not None]
	q_in_bucket = [
		q_in_bucket[i] for i in range(len(q_in_bucket)-1)
			if q_in_bucket[i][0] is not q_in_bucket[i+1][0]
	]

	hnsw_ef=[q["ef"] for q,b in q_in_bucket]
	hnsw_avg_cmp=[q["avg_cmp"] for q,b in q_in_bucket]
	print(hnsw_ef)
	print(hnsw_avg_cmp)
	x_range.append(hnsw_ef)
	y_range.append(hnsw_avg_cmp)
	labels.append("%dM"%int(preamble["scale_M"]))
	markers.append("-o")
	# colors.append("tab:purple")

figname0="t"
title0="Title"
ylabel0="Average dist cmps"
xlabel0="Beam size"

multiLineMultiAxisGraph(x_range, y_range, labels, figname0, title0, ylabel0, xlabel0, "linear", "linear", markers, colors)
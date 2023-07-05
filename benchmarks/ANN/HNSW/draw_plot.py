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
	plt.tight_layout()
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
colors=["tab:blue", "tab:purple", "tab:orange", "tab:green", "tab:red", "tab:brown"]
# labels = ["none", "symm", "LDD", "symmLDD", "Bisection", "symmBisection"]
# labels = ["BIGANN-n", "BIGANN-re", "MSSPACEV-n", "MSSPACEV-re", "YandexT2I-n", "YandexT2I-re"]
labels = ["MSSPACEV-n-deg35.5", "MSSPACEV-re-deg37.1", "MSSPACEV-n-deg13.3", "MSSPACEV-re-deg12.9"]

baseline = None

for file_in in sys.argv[1:]:
	preamble, building, query = ANNparse.parser_kNN.parse(file_in)
	q_in_bucket = util.bucket_query(
		query, 
		# list(range(200,5000,10)),
		[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.83, 0.85, 0.87, 0.9, 0.95, 0.97, 0.99, 0.995, 0.999, 1],
		lambda q: q["recall"],
		lambda x,y: x if x["QPS"]>y["QPS"] else y
	)
	q_in_bucket = [qb for qb in q_in_bucket if qb[0] is not None]# and qb[0]["recall"]>=0.8]
	q_in_bucket = [
		q_in_bucket[i] for i in range(len(q_in_bucket)-1)
			if q_in_bucket[i][0] is not q_in_bucket[i+1][0]
	]

	if file_in==sys.argv[1]:
		baseline = [q for q,b in q_in_bucket]

	# hnsw_ef=[q["ef"] for q,b in q_in_bucket]
	# hnsw_avg_cmp=[q["avg_cmp"] for q,b in q_in_bucket]
	hnsw_QPS=[q["QPS"] for q,b in q_in_bucket]
	hnsw_recall=[q["recall"] for q,b in q_in_bucket]
	# hnsw_QPS_rel = []
	# hnsw_recall = []
	# for q,b in q_in_bucket:
	# 	int_cmp = None
	# 	if baseline[0]["recall"]>q["recall"]:
	# 		continue
	# 	for i in range(1,len(baseline)):
	# 		if baseline[i]["recall"]>=q["recall"]:
	# 			int_cmp = (baseline[i-1], baseline[i])
	# 			break
	# 	if int_cmp is None:
	# 		continue
	# 	s,t = int_cmp
	# 	slope = (t["QPS"]-s["QPS"])/(t["recall"]-s["recall"])
	# 	QPS_base = slope*(q["recall"]-s["recall"])+s["QPS"]
	# 	hnsw_QPS_rel.append(q["QPS"]/QPS_base)
	# 	hnsw_recall.append(q["recall"])

	# print(hnsw_ef)
	# print(hnsw_QPS_rel)
	# print(hnsw_avg_cmp)
	print(hnsw_recall)
	print(hnsw_QPS)
	x_range.append(hnsw_recall)
	# x_range.append(hnsw_ef)
	# y_range.append(hnsw_avg_cmp)
	y_range.append(hnsw_QPS)
	# y_range.append(hnsw_QPS_rel)
	# labels.append("%dM"%int(preamble["scale_M"]))
	markers.append("-o")
	# colors.append("tab:purple")

dataset = ["Unknown", "BIGANN", "MSSPACEV", "YandexT2I", "All"][2]
figname0 = "QPS_recall_%s_refactor_10M_mix"%dataset
# title0 = "QPS on %s (relative to none)"%dataset
title0 = "QPS on %s"%dataset
# title0 = "QPS on 10M datasets"
# ylabel0="Average dist cmps"
# ylabel0="Relative throughput"
ylabel0="Throughput"
xlabel0="Recall"

multiLineMultiAxisGraph(x_range, y_range, labels, figname0, title0, ylabel0, xlabel0, "linear", "linear", markers, colors)

print("The figure is", figname0)
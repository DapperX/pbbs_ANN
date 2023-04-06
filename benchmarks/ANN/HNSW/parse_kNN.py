import sys
import re
import functools

p_cmd = re.compile(r"\./calc_recall -n ([0-9]*)")
p_algo = re.compile(r"Start building (.*)")
p_buildtime = re.compile(r"Build index: (.*)")
p_deg0 = re.compile(r"# 0: *([0-9]*) *([0-9]*) *([0-9]*)")
p_read_gt = re.compile(r"Read groundTruthFile")
p_qparam = re.compile(r"measure recall@([0-9]*) with ef=([0-9]*) beta=([0-9\.]*) on ([0-9]*) queries")
p_recall = re.compile(r"([0-9\.]*) at (.*)kqps")
p_stat99 = re.compile(r"0\.9900 tail stat")
p_cmp_total = re.compile(r"^# visited: ([0-9\.]*)")
p_visit_total = re.compile(r"^# eval: ([0-9\.]*)")
p_cmp_tailing = re.compile(r"\t# visited: ([0-9\.]*)")
p_visit_tailing = re.compile(r"\t# eval: ([0-9\.]*)")
p_stat_tailing = re.compile(r"tail stat")
p_endq = re.compile(r"---")

file_in = sys.argv[1]
target_k = int(sys.argv[2]) if len(sys.argv)>2 else None

preamble = {}
building = {}
query = []
q = {}
state = "PREAMBLE"

f = open(file_in)
for l in f.readlines():
	if state=="PREAMBLE":
		res = re.search(p_cmd, l)
		if res is not None: # commandline
			n = int(res.group(1))
			preamble["scale"] = n
			preamble["scale_M"] = n/1000000
			continue
		res = re.search(p_algo, l)
		if res is not None: # algorithm name
			preamble["algo"] = res.group(1)
			continue
		res = re.search(p_buildtime, l)
		if res is not None: # building time
			building["time"] = float(res.group(1))
			state = "BUILD"
			continue

	if state=="BUILD":
		res = re.search(p_deg0, l)
		if res is not None: # degree info
			building["avg_deg"] = float(res.group(2))/int(res.group(1))
			building["max_deg"] = int(res.group(3))
			continue
		res = re.search(p_read_gt, l)
		if res is not None: # load ground truth
			state = "QUERY"
			continue

	if state=="QUERY":
		res = re.search(p_qparam, l)
		if res is not None: # query param
			q["k"] = int(res.group(1))
			q["ef"] = int(res.group(2))
			q["beta"] = float(res.group(3))
			q["cnt"] = int(res.group(4))
			continue
		res = re.search(p_recall, l)
		if res is not None: # recall
			print(l)
			q["recall"] = float(res.group(1))
			q["QPS"] = float(res.group(2))*1000
			continue
		res = re.search(p_cmp_total, l)
		if res is not None: # the total number of comparisons
			q["avg_cmp"] = float(res.group(1))/q["cnt"]
			continue
		res = re.search(p_visit_total, l)
		if res is not None: # the total number of visits
			q["avg_visit"] = float(res.group(1))/q["cnt"]
			continue
		res = re.search(p_stat99, l)
		if res is not None: # 0.99 tailing statistics
			state = "TAILING_STAT"
			continue
		res = re.match(p_endq, l)
		if res is not None: # at the end of current query
			if target_k is None or q["k"]==target_k:
				query.append(q)
			q = {}

	if state=="TAILING_STAT":
		res = re.search(p_cmp_tailing, l)
		if res is not None: # the tailing number of comparisons
			q[".99_cmp"] = int(res.group(1))
			continue
		res = re.search(p_visit_tailing, l)
		if res is not None: # the tailing number of visits
			q[".99_visit"] = int(res.group(1))
			continue
		res = re.search(p_stat_tailing, l)
		if res is not None: # 0.99 tailing statistics
			state = "QUERY"
			continue

f.close()

print(preamble)
print(building)
# print(query[0])

query.sort(key=lambda q: q["recall"])
# print(query[0])

print("ef\trecall\t\tQPS\t\tavg_cmp")
bucket = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 0.999, 1]
# bucket = [0.8,0.9]
recall_in_bucket = []
QPS_in_bucket = []
ucand_in_bucket = []
for j in range(len(bucket)-1):
	b = bucket[j]
	l = 0
	r = len(query)
	while l+1<r:
		mid = (l+r)//2
		if query[mid]["recall"]<b:
			l = mid
		else:
			r = mid

	d = (bucket[j+1]-b)*0.2
	R = b + d
	L = b - d/4

	candidate = []
	for q in query:
		recall = q["recall"]
		if L<=recall:
			candidate.append(q)

	"""
	size_limit = 5
	for i in range(l,-1,-1):
		q = query[i]
		if q["recall"]<L:
			break
		candidate.append(q)
		if len(candidate)>size_limit/2:
			break

	for i in range(r,len(q)):
		q = query[i]
		if q["recall"]>R:
			break
		candidate.append(q)
		if len(candidate)>size_limit:
			break
	"""

	print("====== [target recall: %f] ======"%b)
	if len(candidate)>0:
		q = functools.reduce(lambda x,y: x if x["QPS"]>y["QPS"] else y, candidate)
		print("%d\t%f\t%f\t%d"%(q["ef"],q["recall"],q["QPS"],int(q["avg_cmp"])))
		recall_in_bucket.append(q["recall"])
		QPS_in_bucket.append(q["QPS"])
		ucand_in_bucket.append(q["avg_cmp"])
	"""
	for q in candidate:
		print("%d %f %f"%(q["ef"],q["recall"],q["QPS"]))
		pass
	"""

print(",".join([str(k) for k in recall_in_bucket]))
print(",".join(["%.2f"%k for k in QPS_in_bucket]))
print(",".join([str(int(k)) for k in ucand_in_bucket]))
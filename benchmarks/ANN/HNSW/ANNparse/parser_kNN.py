import re

def parse(file_in):
	p_cmd = re.compile(r"\./calc_recall -n ([0-9]*) .*?-m ([0-9]*) .*?-efc ([0-9]*)")
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
				building["m"] = int(res.group(2))
				building["efc"] = int(res.group(3))
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
	return (preamble, building, query)
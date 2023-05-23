import sys
import argparse
import ANNparse
import util
import csv

parser = {
	"kNN": ANNparse.parser_kNN
}

ap = argparse.ArgumentParser(description="Collect ANN test results")
ap.add_argument("--format", "-f", choices=list(parser.keys()), help="format of the log file")
ap.add_argument("-o", metavar="FILE", dest="file_out", help="statistics in csv format")
ap.add_argument("-k", metavar="target_k", type=int, help="filter in queries with the given k")
ap.add_argument("file_in", help="log file")
args = ap.parse_args()

preamble, building, query = parser[args.format].parse(args.file_in)

print(preamble)
print(building)
# print(query[0])

bucket = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.83, 0.85, 0.87, 0.9, 0.95, 0.97, 0.99, 0.995, 0.999, 1]

q_in_bucket = util.bucket_query(
	query, 
	bucket, 
	lambda q: q["recall"],
	lambda x,y: x if x["QPS"]>y["QPS"] else y,
	lambda q: args.k is None or q["k"]==args.k
)
q_in_bucket = [qb for qb in q_in_bucket if qb[0] is not None]
q_in_bucket = [
	q_in_bucket[i] for i in range(len(q_in_bucket)-1)
		if q_in_bucket[i][0] is not q_in_bucket[i+1][0]
]

print("ef\trecall\t\tQPS\t\tavg_cmp")
for q,b in q_in_bucket:
	print("======== [target recall: %f] ========"%b)
	print("%d\t%f\t%f\t%d"%(q["ef"],q["recall"],q["QPS"],int(q["avg_cmp"])))

print(",".join([str(q["recall"]) for q,b in q_in_bucket]))
print(",".join(["%.2f"%q["QPS"] for q,b in q_in_bucket]))
print(",".join([str(int(q["avg_cmp"])) for q,b in q_in_bucket]))
# print("ef=30:", next(q for q in query if q["ef"]==30))

if args.file_out is not None:
	with open(args.file_out, "a", newline='') as csvfile:
		writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
		writer.writerow(["GRAPH","Parameters","Size","Build time","Avg degree","Max degree"])
		writer.writerow([
			preamble["algo"],
			"m = %d, efc = %d" % (building["m"],building["efc"]),
			preamble["scale"],
			round(building["time"], 3),
			round(building["avg_deg"], 4),
			building["max_deg"]
		]);
		writer.writerow([])
		writer.writerow([
			"Num queries","Target recall","Actual recall","QPS","Beam size",
			"Average Cmps","Tail Cmps","Average Visited","Tail Visited","k"
		])

		for i in range(len(q_in_bucket)):
			q,b = q_in_bucket[i]
			if i+1<len(q_in_bucket) and q==q_in_bucket[i+1][0]:
				continue
			writer.writerow([
				q["cnt"],
				b,
				q["recall"],
				round(q["QPS"], 2),
				int(q["ef"]),
				int(q["avg_cmp"]),
				q[".99_cmp"],
				int(q["avg_visit"]),
				q[".99_visit"],
				q["k"]
			])
		writer.writerow([])
import functools

"""
Return 'q_in_bucket' where each element is a tuple (q,b), of
that q is best selected by `selector` from those less than or
equal to b, (compared via `key`) which is one of the `bucket`,
while satisfying `cond`
If no such query exists for a bucket b, (None,b) is presented
"""
def bucket_query(query, bucket, key, selector, cond=lambda _:True):
	query.sort(key=key)

	q_in_bucket = []
	for j in range(len(bucket)-1):
		b = bucket[j]
		l = 0
		r = len(query)
		while l+1<r:
			mid = (l+r)//2
			if key(query[mid])<b:
				l = mid
			else:
				r = mid

		d = (bucket[j+1]-b)*0.2
		R = b + d
		L = b - d/4

		candidate = []
		for q in query:
			if L<=key(q) and cond(q):
				candidate.append(q)

		"""
		size_limit = 5
		for i in range(l,-1,-1):
			q = query[i]
			if key(q)<L:
				break
			candidate.append(q)
			if len(candidate)>size_limit/2:
				break

		for i in range(r,len(q)):
			q = query[i]
			if key(q)>R:
				break
			candidate.append(q)
			if len(candidate)>size_limit:
				break
		"""

		if len(candidate)>0:
			q = functools.reduce(selector, candidate)
			q_in_bucket.append((q,b))
		else:
			q_in_bucket.append((None,b))
		"""
		for q in candidate:
			print("candidate for {}: {}".format(b,candidate))
		"""
	return q_in_bucket
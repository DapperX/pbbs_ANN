#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <algorithm>
#include <string>
#include <map>
#include <chrono>
#include <stdexcept>
#include "HNSW.hpp"
#include "dist.hpp"
using ANN::HNSW;

template<typename T>
point_converter_default<T> to_point;

template<typename T>
class gt_converter{
public:
	using type = T*;
	template<typename Iter>
	type operator()([[maybe_unused]] uint32_t id, Iter begin, Iter end)
	{
		using type_src = typename std::iterator_traits<Iter>::value_type;
		static_assert(std::is_convertible_v<type_src,T>, "Cannot convert to the target type");

		const uint32_t n = std::distance(begin, end);

		T *gt = new T[n];
		for(uint32_t i=0; i<n; ++i)
			gt[i] = *(begin+i);
		return gt;
	}
};

// Visit all the vectors in the given 2D array of points
// This triggers the page fetching if the vectors are mmap-ed
template<class T>
void visit_point(const T &array, size_t dim0, size_t dim1)
{
	parlay::parallel_for(0, dim0, [&](size_t i){
		const auto &a = array[i];
		[[maybe_unused]] volatile auto elem = a.coord[0];
		for(size_t j=1; j<dim1; ++j)
			elem = a.coord[j];
	});
}

template<class U>
void output_recall(HNSW<U> &g, parlay::internal::timer &t, uint32_t ef, uint32_t recall, 
	uint32_t cnt_query, parlay::sequence<typename U::type_point> &q, parlay::sequence<uint32_t*> &gt, uint32_t rank_max)
{
	g.total_visited.assign(parlay::num_workers(), 0);
	g.total_eval.assign(parlay::num_workers(), 0);
	g.total_size_C.assign(parlay::num_workers(), 0);
	//std::vector<std::vector<std::pair<uint32_t,float>>> res(cnt_query);
	parlay::sequence<parlay::sequence<std::pair<uint32_t,float>>> res(cnt_query);
	parlay::parallel_for(0, cnt_query, [&](size_t i){
		res[i] = g.search(q[i], recall, ef);
	});
	t.next("Doing search");
	//auto t1 = std::chrono::high_resolution_clock::now();
	parlay::parallel_for(0, cnt_query, [&](size_t i){
		// flag_query
		search_control ctrl{};
		res[i] = g.search(q[i], recall, ef, ctrl);
	});
	//auto t2 = std::chrono::high_resolution_clock::now();
	double time_query = t.next_time();
	//printf("time diff: %.8f\n", time_query);
	// auto diff = std::chrono::duration_cast<std::chrono::milliseconds>(t2-t1);
	//std::chrono::duration<double, std::milli> diff = t2-t1;
	//printf("time diff (hi): %.4f\n", diff.count());
	// t.report(time_query, "Find neighbors");
	printf("HNSW: Find neighbors: %.4f\n", time_query);

	if(rank_max<recall)
		recall = rank_max;
//	uint32_t cnt_all_shot = 0;
	std::vector<uint32_t> result(recall+1);
	printf("measure recall@%u with ef=%u on %u queries\n", recall, ef, cnt_query);
	for(uint32_t i=0; i<cnt_query; ++i)
	{
		uint32_t cnt_shot = 0;
		for(uint32_t j=0; j<recall; ++j)
			if(std::find_if(res[i].begin(),res[i].end(),[&](const std::pair<uint32_t,double> &p){
				return p.first==gt[i][j];}) != res[i].end())
			{
				cnt_shot++;
			}
		/*
		printf("#%u:\t%u (%.2f)[%lu]", i, cnt_shot, float(cnt_shot)/recall, res[i].size());
		if(cnt_shot==recall)
		{
			cnt_all_shot++;
		}
		putchar('\n');
		*/
		result[cnt_shot]++;
	}
	// printf("#all shot: %u (%.2f)\n", cnt_all_shot, float(cnt_all_shot)/cnt_query);
	uint32_t cnt_shot = 0;
	for(uint32_t i=0; i<=recall; ++i)
	{
		printf("%u ", result[i]);
		cnt_shot += result[i]*i;
	}
	putchar('\n');
	printf("%.6f at %ekqps\n", float(cnt_shot)/cnt_query/recall, cnt_query/time_query/1000);
	printf("# visited: %lu\n", parlay::reduce(g.total_visited,parlay::addm<size_t>{}));
	printf("# eval: %lu\n", parlay::reduce(g.total_eval,parlay::addm<size_t>{}));
	printf("size of C: %lu\n", parlay::reduce(g.total_size_C,parlay::addm<size_t>{}));
	puts("---");
}

template<class U>
void output_recall(HNSW<U> &g, commandLine param, parlay::internal::timer &t)
{
	if(param.getOption("-?"))
	{
		printf(__func__);
		puts(
			"[-q <queryFile>] [-g <groundtruthFile>]"
			"-ef <ef_query> [-r <recall@R>=1] [-k <numQuery>=all]"
		);
		return;
	};
	const char* file_query = param.getOptionValue("-q");
	const char* file_groundtruth = param.getOptionValue("-g");
	auto [q,_] = load_point(file_query, to_point<typename U::type_elem>);
	t.next("Read queryFile");
	printf("%s: [%lu,%u]\n", file_query, q.size(), _);

	visit_point(q, q.size(), g.dim);
	t.next("Fetch query vectors");

	uint32_t cnt_rank_cmp = param.getOptionIntValue("-r", 1);
//	const uint32_t ef = param.getOptionIntValue("-ef", cnt_rank_cmp*50);
	const uint32_t cnt_pts_query = param.getOptionIntValue("-k", q.size());

	auto [gt,rank_max] = load_point(file_groundtruth, gt_converter<uint32_t>{});
	t.next("Read groundTruthFile");
	printf("%s: [%lu,%u]\n", file_groundtruth, gt.size(), rank_max);
	for(uint32_t scale=1; scale<60; scale+=2)
		output_recall(g, t, scale*cnt_rank_cmp, cnt_rank_cmp, cnt_pts_query, q, gt, rank_max);
}

template<typename U>
void run_test(commandLine parameter) // intend to be pass-by-value manner
{
	const char *file_in = parameter.getOptionValue("-in");
	const uint32_t cnt_points = parameter.getOptionLongValue("-n", 0);
	const float m_l = parameter.getOptionDoubleValue("-ml", 0.36);
	const uint32_t m = parameter.getOptionIntValue("-m", 40);
	const uint32_t efc = parameter.getOptionIntValue("-efc", 60);
	const float alpha = parameter.getOptionDoubleValue("-alpha", 1);
	const float batch_base = parameter.getOptionDoubleValue("-b", 2);
	const bool do_fixing = !!parameter.getOptionIntValue("-f", 0);
	const char *file_out = parameter.getOptionValue("-out");
	flag_query = parameter.getOptionIntValue("-flag", 0);
	
	parlay::internal::timer t("HNSW", true);

	using T = typename U::type_elem;
	auto [ps,dim] = load_point(file_in, to_point<T>, cnt_points);
	t.next("Read inFile");
	printf("%s: [%lu,%u]\n", file_in, ps.size(), dim);

	visit_point(ps, ps.size(), dim);
	t.next("Fetch input vectors");

	fputs("Start building HNSW\n", stderr);
	HNSW<U> g(
		ps.begin(), ps.begin()+ps.size(), dim,
		m_l, m, efc, alpha, batch_base, do_fixing
	);
	t.next("Build index");

	const uint32_t height = g.get_height();
	printf("Highest level: %u\n", height);
	puts("level     #vertices         #degrees");
	for(uint32_t i=0; i<=height; ++i)
	{
		const uint32_t level = height-i;
		size_t cnt_vertex = g.cnt_vertex(level);
		size_t cnt_degree = g.cnt_degree(level);
		printf("#%2u: %14lu %16lu\n", level, cnt_vertex, cnt_degree);
	}
	t.next("Count vertices and degrees");

	if(file_out)
	{
		g.save(file_out);
		t.next("Write to the file");
	}

	output_recall(g, parameter, t);
}

int main(int argc, char **argv)
{
	for(int i=0; i<argc; ++i)
		printf("%s ", argv[i]);
	putchar('\n');

	commandLine parameter(argc, argv, 
		"-type <elemType> -dist <distance> -n <numInput> -ml <m_l> -m <m> "
		"-efc <ef_construction> -alpha <alpha> -r <recall@R> [-b <batchBase>]"
		"-in <inFile> -out <outFile>"
	);

	const char *dist_func = parameter.getOptionValue("-dist");
	auto run_test_helper = [&](auto type){ // emulate a generic lambda in C++20
		using T = decltype(type);
		if(!strcmp(dist_func,"L2"))
			run_test<descr_l2<T>>(parameter);
		else if(!strcmp(dist_func,"angular"))
			run_test<descr_ang<T>>(parameter);
		else throw std::invalid_argument("Unsupported distance type");
	};

	const char* type = parameter.getOptionValue("-type");
	if(!strcmp(type,"uint8"))
		run_test_helper(uint8_t{});
	else if(!strcmp(type,"int8"))
		run_test_helper(int8_t{});
	else if(!strcmp(type,"float"))
		run_test_helper(float{});
	else throw std::invalid_argument("Unsupported element type");
	return 0;
}

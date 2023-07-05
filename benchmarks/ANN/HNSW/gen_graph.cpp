#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <algorithm>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <chrono>
#include <stdexcept>
#include "HNSW.hpp"
#include "dist.hpp"
using ANN::HNSW;

parlay::sequence<size_t> per_visited;
parlay::sequence<size_t> per_eval;
parlay::sequence<size_t> per_size_C;

template<typename T>
point_converter_default<T> to_point;

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

template<typename U>
void build_index(commandLine parameter) // intend to be pass-by-value manner
{
	const char *file_in = parameter.getOptionValue("-in");
	const uint32_t cnt_points = parameter.getOptionLongValue("-n", 0);
	const float m_l = parameter.getOptionDoubleValue("-ml", 0.36);
	const uint32_t m = parameter.getOptionIntValue("-m", 40);
	const uint32_t efc = parameter.getOptionIntValue("-efc", 60);
	const float alpha = parameter.getOptionDoubleValue("-alpha", 1);
	const float batch_base = parameter.getOptionDoubleValue("-b", 2);
	const bool symmetrize = parameter.getOption("--symm");
	const bool refactor = parameter.getOption("--refactor");
	const bool reorder = parameter.getOption("--reorder");
	const char *file_out = parameter.getOptionValue("-out");
	
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
		m_l, m, efc, alpha, batch_base
	);
	t.next("Build index");

	// post-processing
	if(symmetrize)
	{
		g.symmetrize();
		t.next("Symmetrize edges");
	}
	if(reorder)
	{
		g.reorder();
		t.next("Reorder edges");
	}
	if(refactor)
	{
		g.refactor();
		t.next("Refactor");
	}

	const uint32_t height = g.get_height();
	printf("Highest level: %u\n", height);
	puts("level     #vertices         #degrees  max_degree");
	for(uint32_t i=0; i<=height; ++i)
	{
		const uint32_t level = height-i;
		size_t cnt_vertex = g.cnt_vertex(level);
		size_t cnt_degree = g.cnt_degree(level);
		size_t degree_max = g.get_degree_max(level);
		printf("#%2u: %14lu %16lu %11lu\n", level, cnt_vertex, cnt_degree, degree_max);
	}
	t.next("Count vertices and degrees");

	if(file_out)
	{
		// g.save(file_out);
		auto tg = g.make_gbbsGraph(0);
		gbbs::gbbs_io::write_graph_to_file(file_out, tg);
		printf("#vertices: %lu, #edges: %lu\n", tg.n, tg.m);
		t.next("Write to the file");
	}

	// output_recall(g, parameter, t);
}

int main(int argc, char **argv)
{
	for(int i=0; i<argc; ++i)
		printf("%s ", argv[i]);
	putchar('\n');

	commandLine parameter(argc, argv, 
		"-type <elemType> -dist <distance> -n <numInput> -ml <m_l> -m <m> [--reorder] "
		"-efc <ef_construction> -alpha <alpha> --symm [-b <batchBase>] --refactor "
		"-in <inFile> -out <outFile>"
	);

	const char *dist_func = parameter.getOptionValue("-dist");
	auto build_index_helper = [&](auto type){ // emulate a generic lambda in C++20
		using T = decltype(type);
		if(!strcmp(dist_func,"L2"))
			build_index<descr_l2<T>>(parameter);
		else if(!strcmp(dist_func,"angular"))
			build_index<descr_ang<T>>(parameter);
		else if(!strcmp(dist_func,"ndot"))
			build_index<descr_ndot<T>>(parameter);
		else throw std::invalid_argument("Unsupported distance type");
	};

	const char* type = parameter.getOptionValue("-type");
	if(!strcmp(type,"uint8"))
		build_index_helper(uint8_t{});
	else if(!strcmp(type,"int8"))
		build_index_helper(int8_t{});
	else if(!strcmp(type,"float"))
		build_index_helper(float{});
	else throw std::invalid_argument("Unsupported element type");
	return 0;
}

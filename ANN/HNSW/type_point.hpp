#ifndef __TYPE_POINT_HPP__
#define __TYPE_POINT_HPP__

#include <cstdint>
#include <cstddef>
#include <iterator>
#include <algorithm>
#include <memory>
#include <type_traits>
#include <stdexcept>
#include <any>
#include "benchUtils.h"

#ifdef SUPPORT_HDF5
#include "h5_ops.hpp"
#endif

class internal_termination{
protected:
	internal_termination(){}
	internal_termination(int){std::terminate();}
};

template<typename T>
class fake_copyable : public internal_termination{
	T content;
public:
	fake_copyable(const T &c) : content(c){}
	fake_copyable(T &&c) : content(std::move(c)){}

	fake_copyable(fake_copyable&&) = default;
	fake_copyable(const fake_copyable &other)
		: internal_termination(0), 
		  content(std::move(const_cast<fake_copyable&>(other).content))
	{
	}
};
template<typename T>
fake_copyable(const T&) -> fake_copyable<T>;
template<typename T>
fake_copyable(T&&) -> fake_copyable<T>;

template<typename T>
struct point
{
	typedef T type;

	uint32_t id;
	const T *coord;

	point()
		: id(~0u), coord(NULL), closure()
	{
	}
	point(uint32_t id_, const T *coord_)
		: id(id_), coord(coord_)
	{
	}
	template<class C>
	point(uint32_t id_, const T *coord_, C &&closure_)
		: id(id_), coord(coord_), closure(fake_copyable(std::forward<C>(closure_)))
	{
	}
private:
	std::any closure;
};

enum class file_format{
	VEC, HDF5, BIN
};

template<typename T>
class point_converter_default
{
public:
	using type = point<T>;

	template<typename Iter>
	type operator()(uint32_t id, Iter begin, [[maybe_unused]] Iter end)
	{
		using type_src = typename std::iterator_traits<Iter>::value_type;
		static_assert(std::is_convertible_v<type_src,T>, "Cannot convert to the target type");

		if constexpr(std::is_same_v<Iter,ptr_mapped<T,ptr_mapped_src::PERSISTENT>>||
			std::is_same_v<Iter,ptr_mapped<const T,ptr_mapped_src::PERSISTENT>>)
			return point<T>(id, &*begin);
		else
		{
			const uint32_t dim = std::distance(begin, end);

			// T *coord = new T[dim];
			auto coord = std::make_unique<T[]>(dim);
			for(uint32_t i=0; i<dim; ++i)
				coord[i] = *(begin+i);
			return point<T>(id, coord.get(), std::move(coord));
		}
	}
};

template<typename Src, class Conv>
inline std::pair<parlay::sequence<typename Conv::type>,uint32_t>
load_from_vec(const char *file, Conv converter, uint32_t max_num)
{
	const auto [fileptr, length] = mmapStringFromFile(file);

	// Each vector is 4 + sizeof(Src)*dim bytes.
	// * first 4 bytes encode the dimension (as an uint32_t)
	// * next dim values are Src-type variables representing vector components
	// See http://corpus-texmex.irisa.fr/ for more details.

	const uint32_t dim = *((const uint32_t*)fileptr);
	std::cout << "Dimension = " << dim << std::endl;

	const size_t vector_size = sizeof(dim) + sizeof(Src)*dim;
	const uint32_t n = std::min<size_t>(length/vector_size, max_num);
	// std::cout << "Num vectors = " << n << std::endl;

	typedef ptr_mapped<const Src,ptr_mapped_src::PERSISTENT> type_ptr;
	parlay::sequence<typename Conv::type> ps(n);

	parlay::parallel_for(0, n, [&,fp=fileptr] (size_t i) {
		const Src *coord = (const Src*)(fp+sizeof(dim)+i*vector_size);
		ps[i] = converter(i, type_ptr(coord), type_ptr(coord+dim));
	});

	return {std::move(ps), dim};
}

template<class Conv>
inline std::pair<parlay::sequence<typename Conv::type>,uint32_t>
load_from_HDF5(const char *file, const char *dir, Conv converter, uint32_t max_num)
{
#ifndef SUPPORT_HDF5
	(void)file;
	(void)dir;
	(void)converter;
	(void)max_num;
	throw std::invalid_argument("HDF5 support is not enabled");
#else
	auto [buffer,bound] = read_array_from_HDF5<typename Conv::type>(file, dir);
	const auto dim = bound[1];

	size_t n = std::min(bound[0], max_num);
	parlay::sequence<typename Conv::type> ps(n);
	parlay::parallel_for(0, n, [&](uint32_t i){
		// TODO: may cause temporary memory usage as twice as the size of `buffer`
		// May be solved by designing an iterator that reads data from HDF5 gradually
		ps[i] = converter(i, &buffer[i*dim], &buffer[(i+1)*dim]);
	});
	return {std::move(ps), dim};
#endif
}

template<typename Src, class Conv>
inline std::pair<parlay::sequence<typename Conv::type>,uint32_t>
load_from_bin(const char *file, Conv converter, uint32_t max_num)
{
	auto [fileptr, length] = mmapStringFromFile(file); (void)length;
	const uint32_t n = std::min(max_num, *((uint32_t*)fileptr));
    const uint32_t dim = *((uint32_t*)(fileptr+sizeof(n)));
    const size_t vector_size = sizeof(Src)*dim;
    const size_t header_size = sizeof(n)+sizeof(dim);

	typedef ptr_mapped<const Src,ptr_mapped_src::PERSISTENT> type_ptr;
	parlay::sequence<typename Conv::type> ps(n);
	parlay::parallel_for(0, n, [&,fp=fileptr](uint32_t i){
		const Src *coord = (const Src*)(fp+header_size+i*vector_size);
		ps[i] = converter(i, type_ptr(coord), type_ptr(coord+dim));
	});

	return {std::move(ps), dim};
}
/*
template<typename Src=void, class Conv>
inline auto load_point(const char *file, file_format input_format, Conv converter, size_t max_num=0, std::any aux={})
{
	if(!max_num)
		max_num = std::numeric_limits<decltype(max_num)>::max();

	switch(input_format)
	{
	case file_format::VEC:
		return load_from_vec<Src>(file, converter, max_num);
	case file_format::HDF5:
		return load_from_HDF5(file, std::any_cast<const char*>(aux), converter, max_num);
	case file_format::BIN:
		return load_from_bin<Src>(file, converter, max_num);
	default:
		__builtin_unreachable();
	}
}
*/
template<class Conv>
inline auto load_point(const char *input_name, Conv converter, size_t max_num=0)
{
	auto buffer = std::make_unique<char[]>(strlen(input_name)+1);
	strcpy(buffer.get(), input_name);

	char *splitter = strchr(buffer.get(), ':');
	if(splitter==nullptr)
		throw std::invalid_argument("The input spec is not specified");

	*(splitter++) = '\0';
	const char *file = buffer.get();
	const char *input_spec = splitter;

	if(!max_num)
		max_num = std::numeric_limits<decltype(max_num)>::max();

	if(input_spec[0]=='/')
		return load_from_HDF5(file, input_spec, converter, max_num);
	if(!strcmp(input_spec,"fvecs"))
		return load_from_vec<float>(file, converter, max_num);
	if(!strcmp(input_spec,"bvecs"))
		return load_from_vec<uint8_t>(file, converter, max_num);
	if(!strcmp(input_spec,"ivecs"))
		return load_from_vec<int32_t>(file, converter, max_num);
	if(!strcmp(input_spec,"u8bin"))
		return load_from_bin<uint8_t>(file, converter, max_num);
	if(!strcmp(input_spec,"i8bin"))
		return load_from_bin<int8_t>(file, converter, max_num);
	if(!strcmp(input_spec,"ibin"))
		return load_from_bin<int32_t>(file, converter, max_num);
	if(!strcmp(input_spec,"fbin"))
		return load_from_bin<float>(file, converter, max_num);

	throw std::invalid_argument("Unsupported input spec");
}

#endif // __TYPE_POINT_HPP_

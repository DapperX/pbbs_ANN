// This code is part of the Problem Based Benchmark Suite (PBBS)
// Copyright (c) 2011 Guy Blelloch and the PBBS team
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the
// "Software"), to deal in the Software without restriction, including
// without limitation the rights (to use, copy, modify, merge, publish,
// distribute, sublicense, and/or sell copies of the Software, and to
// permit persons to whom the Software is furnished to do so, subject to
// the following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
// NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
// LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
// OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
// WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#include <algorithm>
#include "parlay/parallel.h"
#include "parlay/primitives.h"
#include "common/geometry.h"
#include "index.h"
#include "../utils/NSGDist.h"

bool report_stats = true;

template<class fvec_point>
void ANN(parlay::sequence<fvec_point*> &v, int k, int maxDeg, int beamSize, double alpha, parlay::sequence<fvec_point*> &q) {
  parlay::internal::timer t("ANN",report_stats);
  {
    unsigned d = (v[0]->coordinates).size()/4;
    using findex = knn_index<fvec_point>;
    findex I(maxDeg, beamSize, k, alpha, d);
    I.build_index(v, true);
    t.next("Built index");
    I.searchNeighbors(q, v);
    t.next("Found nearest neighbors");
  };
}


template<class fvec_point>
void ANN(parlay::sequence<fvec_point*> &v, int k, int maxDeg, int beamSize, double alpha) {
  parlay::internal::timer t("ANN",report_stats);
  {
    unsigned d = (v[0]->coordinates).size()/4;
    using findex = knn_index<fvec_point>;
    findex I(maxDeg, beamSize, k, alpha, d);
    I.build_index(v);
    t.next("Built index");
  };
}
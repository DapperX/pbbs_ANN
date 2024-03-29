---
title: Burrows Wheeler Decode
---


# Burrows Wheeler Decode (BWD)

  This benchmark does an inverse Burrows-Wheeler transform.
  It takes a sequence of characters as input, which have been ordered by a
  Burrows-Wheeler transform.

  The specific Burrows-Wheeler transform we use is to sort each
  character in a string by the string that appears immediately after
  it.  To identify the front, the string is padded with a null
  character at the front (i.e.  when written and read from file should
  be read as a binary file).  As an example consider the string
  "abcabcab".  After padding (marked with $), we have the 
  characters with their following string:

```
    $ abcabcab
    a bcabcab
    b cabcab
    c abcab
    a bcab
    b cab
    c ab
    a b
    b 
```

  Now if we sort the characters by their string, we get

```
     b 
     c ab
     c abcab
     $ abcabcab  
     a b
     a bcab
     a bcabcab
     b cab
     b cabcab
```

Hence we output `bcc$aaabb`.  This string uniquely defines the
original string which can be found using the inverse BW transform.
Converting it back is the task of this benchmark.  The standard
algorithm is to sort the characters which then links each character
with its previous character.  This forms a linked list of length n,
which needs to be followed.  Details can be found in descriptions of
the BW transform.

We supply code for encoding a string into the BW format as described.
It can be found in `algorithm/bw_encode.h`.

### Default Input Distributions

We use three strings for the large input:

- A string of length 250,000,000 characters generated by the trigram 
distribution.  Should be generated using `trigramString 250000000 <filename>`.

- `etext99` : Approximately 100 Million characters from the Project Gutenberg project. 

- `wikipedia250M.txt` : 250 Million characters taken from wikipedia

And three for the small input:

- A string of length 25,000,000 characters generated by the trigram 
distribution.  Should be generated using `trigramString 25000000
<filename>`.

- `chr22.dna` : A dna string.

- `wikisamp.xml` : a smaller sample from wikipedia.

### Input and Output File Formats 

The input is a binary file containing exactly one null character 
corresponding to the start.  The output is a binary file not 
containing any null characters.  It will be one character shorter than 
the input (null character removed).  It must correspond to the 
original string that generated the input file by the algorithm 
described above. 


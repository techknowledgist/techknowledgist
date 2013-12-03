This has an old version of the runtime code used for the phase 1 evaluation. In
the evulation, we needed to lookup a technology in the ontology and then create
a fact file with the results. In addition, for the multilingual evaluation some
html files needed to be produced.

The ontologies back then were tiny and lookup could be done with an in-memory
prefix trie. In addition, there was a serious problem in that lookup found
things it was not supposed to find. For example, if we had a string "we used a
quatum computer" and "computer" was in the ontology then it would be extracted
as the technology, even if "quatum computer" was a term in its own right (but
just not frequent enough to make it into the ontology).

Lookup code for phase 2 is added to ontology/runtime.


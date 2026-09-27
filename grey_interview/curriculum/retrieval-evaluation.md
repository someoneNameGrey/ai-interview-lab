# Retrieval metrics and diagnosis

Skip basic RAG plumbing and diagnose evidence quality. Define relevance at document or chunk level, duplicates and incomplete labels before comparing chunk sizes. Split related queries/documents together. Include exact identifiers, synonyms, missing evidence, contradictory/stale policy and access restrictions.

Recall@K = relevant retrieved / all labeled relevant. Precision@K = relevant in top K / K, with a declared rule for fewer results. MRR averages 1/(rank of first relevant), using zero if absent. NDCG compares discounted graded relevance with the ideal ranking; state gain and discount conventions.

## Worked example
Relevant documents are A and C; top three are B, A, C. Recall@3 is 1, Precision@3 is 2/3 and reciprocal rank is 1/2. This still does not prove that the generated answer uses A or C correctly. Report answer correctness, claim support and abstention separately. For no-relevant-answer cases, separate abstention scoring from undefined recall/normalized gain.

Compare dense baseline, lexical/dense hybrid retrieval, reranking and query rewriting one change at a time. Select context under a token budget; larger context can add noise. Embedding choice, chunk boundaries and freshness all affect results.

## Evidence gate
Use at least 50 queries, 30 development / 20 held-out by family. Produce ranking calculations, ablations, latency/cost and ten failures traced to indexing, access filtering, retrieval, ranking, context selection or generation. Support S1 starts here.


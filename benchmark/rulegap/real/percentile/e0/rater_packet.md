# Rater packet: percentile_slo_real_v1

## Instructions

You are a careful engineer reading one line of a service-level objective. Judge only from the words of the line and ordinary statistics vocabulary. Ignore any team convention or tool default.

For each candidate meaning below, mark whether a careful reader could defend it from the rule text alone. Do not consult any other material. Then note any meaning you think is missing.

## Rule text

> 90% of requests faster than 450 ms

## "requests"

| # | Candidate meaning | Defensible (Y/N) | Comment |
|---|---|---|---|
| 1 | every request in the log |  |  |
| 2 | every request that returned successfully |  |  |

Missing meanings:

## "90% of requests faster than 450 ms"

| # | Candidate meaning | Defensible (Y/N) | Comment |
|---|---|---|---|
| 1 | at least that share of the requests, counted one by one, were faster than the threshold |  |  |
| 2 | the percentile at that level, computed as the inverse of the empirical distribution, averaging the two samples at a step, is below the threshold |  |  |
| 3 | the percentile at that level, computed as the sample whose rank is nearest to n times p, is below the threshold |  |  |
| 4 | the percentile at that level, computed as the smallest sample such that at least that share of samples is at or below it, is below the threshold |  |  |
| 5 | the percentile at that level, computed as the value at position (n + 1) times p, interpolating between ranked samples, is below the threshold |  |  |
| 6 | the percentile at that level, computed as the value at position (n + 1/3) times p plus 1/3, interpolating between ranked samples, is below the threshold |  |  |
| 7 | the percentile at that level, computed as the value at position (n + 1/4) times p plus 3/8, interpolating between ranked samples, is below the threshold |  |  |
| 8 | the percentile at that level, computed as the value at position (n - 1) times p plus 1, interpolating between ranked samples, is below the threshold |  |  |
| 9 | the percentile at that level, computed as the value at position n times p plus one half, interpolating between ranked samples, is below the threshold |  |  |
| 10 | the percentile at that level, computed as the value at position n times p, interpolating between ranked samples, is below the threshold |  |  |

Missing meanings:


# xan Aggregation Functions Reference

Used with `xan agg`, `xan groupby`, and `xan window`.

Note: Most functions ignore empty values. Functions on numbers error on non-numeric strings.
To include nulls: `mean(number || 0)`. Expressions returning lists are treated as multiplexed rows.

## Contents
- [Counting](#counting)
- [Numerical](#numerical)
- [Statistical](#statistical)
- [String/Value](#stringvalue)
- [DateTime](#datetime)
- [Top/Argmax](#topargmax)

## Counting

- **count**(expr?) - count truthy values (or all rows if omitted)
- **cardinality**(expr) - count distinct values
- **approx_cardinality**(expr) - approximate distinct count (HyperLogLog++)

## Numerical

- **sum**(expr) - sum (Kahan-Babuska for precision)
- **min**(expr), **max**(expr) - numerical min/max
- **mean**(expr) / **avg**(expr) - average

## Statistical

- **median**(expr), **median_high**(expr), **median_low**(expr)
- **quantile**(expr, q), **approx_quantile**(expr, p) - t-digest approximation
- **q1**(expr), **q2**(expr), **q3**(expr) - quartiles
- **stddev**(expr) / **stddev_pop**(expr) - population std dev
- **stddev_sample**(expr) - sample std dev (Bessel's correction)
- **var**(expr) / **var_pop**(expr) - population variance
- **var_sample**(expr) - sample variance
- **rms**(expr) - root mean square
- **covariance**(expr1, expr2) / **covariance_pop** - population covariance
- **covariance_sample**(expr1, expr2) - sample covariance
- **correlation**(expr1, expr2) - Pearson correlation

## String/Value

- **first**(expr), **last**(expr) - first/last non-empty
- **lex_first**(expr), **lex_last**(expr) - lexicographical first/last
- **mode**(expr) - most common value
- **values**(expr, sep?) - all values joined by `|` or custom separator
- **distinct_values**(expr, sep?) - sorted distinct values joined
- **most_common**(k, expr, sep?) - top k most common values
- **most_common_counts**(k, expr, sep?) - counts for top k
- **type**(expr), **types**(expr) - detected type(s)

## Boolean

- **all**(expr) - true if all truthy
- **any**(expr) - true if any truthy
- **ratio**(expr, decimals?) - ratio of truthy (0-1)
- **percentage**(expr, decimals?) - percentage of truthy

## DateTime

- **earliest**(expr), **latest**(expr) - min/max datetime
- **count_seconds**(expr), **count_hours**(expr), **count_days**(expr), **count_years**(expr) - time span

## Top/Argmax

- **argmin**(expr, result_expr?) - row index (or result) where expr is minimized
- **argmax**(expr, result_expr?) - row index (or result) where expr is maximized
- **top**(k, expr, sep?) - top k values joined
- **argtop**(k, expr, result_expr?, sep?) - indices/results for top k

## Examples

```bash
# Basic aggregation
xan agg 'count(), sum(sales), mean(price)' data.csv

# Group by with multiple aggregations
xan groupby category 'sum(sales) as total, count() as n, mean(price) as avg' data.csv

# Get row where max occurs
xan agg 'argmax(score, name) as top_scorer' data.csv

# Distinct values per group
xan groupby region 'distinct_values(product) as products' data.csv

# Statistical summary
xan agg 'mean(x), stddev(x), median(x), q1(x), q3(x)' data.csv

# Correlation between columns
xan agg 'correlation(height, weight)' data.csv
```

# xan Expression Functions Reference

## Contents
- [Operators](#operators)
- [Boolean & Branching](#boolean--branching)
- [Comparison](#comparison)
- [Arithmetics](#arithmetics)
- [Formatting](#formatting)
- [Strings](#strings)
- [Lists](#lists)
- [Maps](#maps)
- [Dates & Time](#dates--time)
- [URLs & Web](#urls--web)
- [IO & Paths](#io--paths)
- [Randomness & Hashing](#randomness--hashing)

## Operators

### Numerical comparison
```
x == y, x != y, x < y, x <= y, x > y, x >= y
```

### String/sequence comparison
```
x eq y, x ne y, x lt y, x le y, x gt y, x ge y
```

### Arithmetic
```
x + y, x - y, x * y, x / y, x % y, x // y (int div), x ** y (power)
```

### String/sequence
```
x ++ y  (concatenation)
```

### Logical
```
x && y, x and y, x || y, x or y, x in y, x not in y, !x
```

### Indexing & Slicing
```
x[y], x[start:end], x[:end], x[start:], x[-1]
```

### Pipeline
```
trim(name) | len(_)    # _ refers to left-hand result
trim(name) | len       # elision for unary functions
```

## Boolean & Branching

- **if**(cond, then, else?) - conditional
- **unless**(cond, then, else?) - inverted conditional
- **and**(a, b, *n), **or**(a, b, *n), **not**(a)
- **try**(expr) - return null on error

## Comparison

- **eq**(s1, s2), **ne**(s1, s2) - string equality/inequality
- **gt**(s1, s2), **ge**(s1, s2), **lt**(s1, s2), **le**(s1, s2) - string comparison

## Arithmetics

- **abs**(x), **neg**(x), **sqrt**(x)
- **add**(x, y, *n), **sub**(x, y, *n), **mul**(x, y, *n), **div**(x, y, *n)
- **idiv**(x, y), **mod**(x, y), **pow**(x, y)
- **ceil**(x, unit?), **floor**(x, unit?), **round**(x, unit?), **trunc**(x, unit?)
- **log**(x, base?), **log2**(x), **log10**(x)
- **min**(x, y, *n), **max**(x, y, *n) - also work on lists
- **argmin**(numbers, labels?), **argmax**(numbers, labels?)
- **int**(any), **float**(any) - casting

## Formatting

- **fmt**(string, *args) - `fmt("{} {}", first, last)`
- **printf**(format, *args) - C-style formatting
- **lower**(s), **upper**(s)
- **trim**(s, chars?), **ltrim**(s, chars?), **rtrim**(s, chars?)
- **pad**(s, width, char?), **lpad**(s, width, char?), **rpad**(s, width, char?)
- **numfmt**(n, thousands_sep=",", comma=false, significance=5)
- **to_fixed**(n, precision)
- **bytesize**(s) - human-readable bytes
- **escape_regex**(s)

## Strings

- **len**(s) - character count
- **count**(s, substring), **count**(s, regex) - occurrence count
- **contains**(s, substring), **contains**(s, regex)
- **startswith**(s, prefix), **endswith**(s, suffix)
- **split**(s, sep, max?), **split**(s, regex, max?)
- **replace**(s, old, new), **replace**(s, regex, replacement)
- **match**(s, regex, group) - extract regex match
- **concat**(s, *strings)

## Strings, Lists, Maps

- **first**(seq), **last**(seq)
- **get**(seq, index, default?), **get**(map, key, default?)
- **slice**(seq, start, end?)

## Lists

- **len**(list)
- **compact**(list) - drop falsey values
- **join**(list, sep)
- **map**(list, lambda) - `map(nums, x => x + 1)`
- **filter**(list, lambda) - `filter(names, n => startswith(n, "A"))`
- **find**(list, lambda), **find_index**(list, lambda)
- **all**(list, lambda), **any**(list, lambda)
- **sum**(numbers), **mean**(numbers)
- **index_by**(list, key) - list of maps to indexed map

## Maps

- **keys**(map), **values**(map)

## Dates & Time

- **datetime**(s, format?, timezone?) - parse datetime
- **timestamp**(n), **timestamp_ms**(n) - POSIX timestamp to datetime
- **strftime**(dt, format) - format datetime
- **year**(dt), **month**(dt), **year_month**(dt), **year_month_day**(dt), **month_day**(dt)
- **earliest**(dt1, dt2, *n), **latest**(dt1, dt2, *n)
- **to_timezone**(dt, tz_in, tz_out), **to_local_timezone**(dt)

## URLs & Web

- **urljoin**(base, path)
- **lru**(url) - URL to LRU format
- **html_unescape**(s)
- **mime_ext**(mimetype)
- **parse_dataurl**(s) - returns [mimetype, bytes]

## Fuzzy Matching

- **fingerprint**(s) - normalize, dedupe, sort words
- **unidecode**(s) - convert to ASCII
- **s_stemmer**(s), **carry_stemmer**(s) - stemming

## Utils

- **col**(name_or_pos, nth?) - access column by name/index
- **col?**(name_or_pos, nth?) - same, returns null if missing
- **header**(name_or_pos, nth?) - get header name
- **cols**(from?, to?) - list of cell values
- **headers**(from?, to?) - list of header names
- **index**() - current row index
- **typeof**(value)
- **regex**(s) - parse string as regex dynamically
- **err**(msg) - raise custom error

## IO & Paths

- **read**(path, encoding?, errors?) - read file
- **read_json**(path), **read_csv**(path)
- **parse_json**(s), **parse_py_literal**(s)
- **write**(content, path)
- **copy**(src, dst), **move**(src, dst)
- **abspath**(s), **basename**(path, suffix?), **dirname**(path), **ext**(path)
- **pathjoin**(s, *strings) / **pjoin**
- **isfile**(path), **filesize**(path)
- **cmd**(program, args) - run subprocess
- **shell**(command) - run shell command
- **shlex_split**(s) - split command line

## Randomness & Hashing

- **random**() - float 0-1
- **uuid**() - UUID v4
- **md5**(s) - MD5 hash hex

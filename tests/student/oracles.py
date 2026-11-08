"""Small independent reference models. Built-in search is test-only."""

from functools import cache, cmp_to_key


def subsequence(sequence, text):
    cursor = 0
    for character in text:
        if cursor < len(sequence) and sequence[cursor] == character:
            cursor += 1
    return cursor == len(sequence)


def lcs_length(a, b):
    if len(a) > len(b):
        a, b = b, a
    best = 0
    for mask in range(1 << len(a)):
        candidate = ''.join(c for i, c in enumerate(a) if mask & (1 << i))
        if len(candidate) > best and subsequence(candidate, b):
            best = len(candidate)
    return best


@cache
def merge_cost(sizes):
    if len(sizes) < 2:
        return 0
    return min(sizes[i] + sizes[i + 1] +
               merge_cost(sizes[:i] + (sizes[i] + sizes[i + 1],) + sizes[i + 2:])
               for i in range(len(sizes) - 1))


def tree_weight(weights, edges):
    best = 0
    for mask in range(1 << len(weights)):
        if all(not (mask & (1 << u) and mask & (1 << v)) for u, v in edges):
            best = max(best, sum(w for i, w in enumerate(weights) if mask & (1 << i)))
    return best


def positions(text, pattern):
    if not pattern:
        return list(range(len(text) + 1))
    result = []
    start = text.find(pattern)
    while start != -1:
        result.append(start)
        start = text.find(pattern, start + 1)
    return result


def suffix_result(text):
    """Literal suffix comparator: no prefix doubling and no Kasai reuse."""
    n = len(text)

    def compare(a, b):
        while a < n and b < n:
            if text[a] != text[b]:
                return -1 if text[a] < text[b] else 1
            a += 1
            b += 1
        return (a < n) - (b < n)

    sa = sorted(range(n), key=cmp_to_key(compare))
    lcp = [0] * n
    for i in range(1, n):
        a, b, common = sa[i - 1], sa[i], 0
        while a + common < n and b + common < n and text[a + common] == text[b + common]:
            common += 1
        lcp[i] = common
    longest = max(lcp, default=0)
    index = lcp.index(longest) if n else 0
    return {"sa": sa, "lcp": lcp, "repeated": text[sa[index]:sa[index] + longest] if n else ""}


def aho_counts(patterns, texts):
    return [[len(positions(text, pattern)) for pattern in patterns] for text in texts]

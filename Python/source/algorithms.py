"""Dynamic programming and string algorithms for the supplied JSONL adapter.

All request state is local. Witness reconstruction and tree traversal use
explicit stacks, and the implementations require only the standard library.
"""

from array import array


def lcs(request):
    """Prefix DP with a full table for reconstruction of one optimal LCS."""
    a, b = request["a"], request["b"]
    n, m = len(a), len(b)
    if not n or not m:
        return {"length": 0, "sequence": ""}
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        previous, row = dp[i - 1], dp[i]
        character = a[i - 1]
        for j in range(1, m + 1):
            if character == b[j - 1]:
                row[j] = previous[j - 1] + 1
            else:
                row[j] = max(previous[j], row[j - 1])
    characters = []
    i, j = n, m
    while i and j:
        if a[i - 1] == b[j - 1]:
            characters.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    characters.reverse()
    return {"length": dp[n][m], "sequence": "".join(characters)}


def merge(request):
    """Interval DP; output child merges before their parent merge."""
    sizes = request["sizes"]
    n = len(sizes)
    if n <= 1:
        return {"cost": 0, "plan": []}
    prefix = [0]
    for size in sizes:
        prefix.append(prefix[-1] + size)
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for left in range(n - length + 1):
            right = left + length - 1
            interval_size = prefix[right + 1] - prefix[left]
            best = dp[left][left] + dp[left + 1][right] + interval_size
            best_split = left
            for middle in range(left + 1, right):
                candidate = dp[left][middle] + dp[middle + 1][right] + interval_size
                if candidate < best:
                    best, best_split = candidate, middle
            dp[left][right] = best
            split[left][right] = best_split
    plan = []
    stack = [(0, n - 1, False)]
    while stack:
        left, right, children_done = stack.pop()
        if left == right:
            continue
        middle = split[left][right]
        if children_done:
            plan.append([left, middle, right])
        else:
            stack.append((left, right, True))
            stack.append((middle + 1, right, False))
            stack.append((left, middle, False))
    return {"cost": dp[0][n - 1], "plan": plan}


def tree(request):
    """Maximum weight independent set via iterative take/skip tree DP."""
    n = request["n"]
    if not n:
        return {"weight": 0, "selected": []}
    adjacency = [[] for _ in range(n)]
    for u, v in request["edges"]:
        adjacency[u].append(v)
        adjacency[v].append(u)
    parent = [-1] * n
    order = [0]
    for vertex in order:
        for neighbour in adjacency[vertex]:
            if neighbour != parent[vertex]:
                parent[neighbour] = vertex
                order.append(neighbour)
    take = list(request["weights"])
    skip = [0] * n
    for vertex in reversed(order):
        ancestor = parent[vertex]
        if ancestor != -1:
            take[ancestor] += skip[vertex]
            skip[ancestor] += max(take[vertex], skip[vertex])
    selected = []
    stack = [(0, False)]
    while stack:
        vertex, parent_taken = stack.pop()
        choose = not parent_taken and take[vertex] > skip[vertex]
        if choose:
            selected.append(vertex)
        for neighbour in adjacency[vertex]:
            if neighbour != parent[vertex]:
                stack.append((neighbour, choose))
    return {"weight": max(take[0], skip[0]), "selected": selected}


def naive(request):
    """Check every valid start by individual character comparisons."""
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if not m:
        return {"positions": list(range(n + 1))}
    positions = []
    for start in range(n - m + 1):
        matched = 0
        while matched < m and text[start + matched] == pattern[matched]:
            matched += 1
        if matched == m:
            positions.append(start)
    return {"positions": positions}


def kmp(request):
    """Prefix-function KMP; prefix fallback retains overlapping matches."""
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if not m:
        return {"positions": list(range(n + 1))}
    if m > n:
        return {"positions": []}
    pi = [0] * m
    matched = 0
    for i in range(1, m):
        while matched and pattern[i] != pattern[matched]:
            matched = pi[matched - 1]
        if pattern[i] == pattern[matched]:
            matched += 1
        pi[i] = matched
    positions = []
    matched = 0
    for i, character in enumerate(text):
        while matched and character != pattern[matched]:
            matched = pi[matched - 1]
        if character == pattern[matched]:
            matched += 1
        if matched == m:
            positions.append(i - m + 1)
            matched = pi[matched - 1]
    return {"positions": positions}


def rk(request):
    """Base-31/mod-101 rolling hash, with exact candidate verification."""
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if not m:
        return {"positions": list(range(n + 1))}
    if m > n:
        return {"positions": []}
    base, modulus = 31, 101
    high_power = pow(base, m - 1, modulus)
    pattern_hash = window_hash = 0
    for i in range(m):
        pattern_hash = (pattern_hash * base + ord(pattern[i])) % modulus
        window_hash = (window_hash * base + ord(text[i])) % modulus
    positions = []
    for start in range(n - m + 1):
        if window_hash == pattern_hash:
            matched = 0
            while matched < m and text[start + matched] == pattern[matched]:
                matched += 1
            if matched == m:
                positions.append(start)
        if start < n - m:
            window_hash = ((window_hash - ord(text[start]) * high_power) * base
                           + ord(text[start + m])) % modulus
    return {"positions": positions}


def suffix(request):
    """Prefix-doubling suffix array and predecessor-form Kasai LCP."""
    text = request["text"]
    n = len(text)
    if not n:
        return {"sa": [], "lcp": [], "repeated": ""}
    sa = list(range(n))
    ranks = [ord(character) for character in text]
    width = 1
    while width < n:
        sa.sort(key=lambda i: (ranks[i], ranks[i + width] if i + width < n else -1))
        next_ranks = [0] * n
        for position in range(1, n):
            previous, current = sa[position - 1], sa[position]
            previous_pair = (ranks[previous], ranks[previous + width] if previous + width < n else -1)
            current_pair = (ranks[current], ranks[current + width] if current + width < n else -1)
            next_ranks[current] = next_ranks[previous] + (current_pair != previous_pair)
        ranks = next_ranks
        if ranks[sa[-1]] == n - 1:
            break
        width *= 2
    inverse = [0] * n
    for position, start in enumerate(sa):
        inverse[start] = position
    lcp = [0] * n
    common = best_length = best_start = 0
    for start in range(n):
        position = inverse[start]
        if position == 0:
            common = 0
            continue
        previous = sa[position - 1]
        while start + common < n and previous + common < n and text[start + common] == text[previous + common]:
            common += 1
        lcp[position] = common
        if common > best_length:
            best_length, best_start = common, start
        if common:
            common -= 1
    return {"sa": sa, "lcp": lcp, "repeated": text[best_start:best_start + best_length]}


def aho(request):
    """One ASCII automaton; aggregate visits backward along failure links.

    Compact signed-integer arrays hold 95 transitions per trie state. Duplicate
    dictionary entries share terminal states but retain distinct output columns.
    """
    patterns, texts = request["patterns"], request["texts"]
    if not texts:
        return {"counts": []}
    if not patterns:
        return {"counts": [[] for _ in texts]}
    alphabet_size = 95
    transitions = [array("i", [0]) * alphabet_size]
    failure = [0]
    terminals = []
    for pattern in patterns:
        state = 0
        for character in pattern:
            symbol = ord(character) - 32
            child = transitions[state][symbol]
            if child == 0:
                child = len(transitions)
                transitions[state][symbol] = child
                transitions.append(array("i", [0]) * alphabet_size)
                failure.append(0)
            state = child
        terminals.append(state)

    # Root's missing transitions already point to root; its children fail there.
    breadth_first = [child for child in transitions[0] if child]
    for state in breadth_first:
        row = transitions[state]
        fallback = transitions[failure[state]]
        for symbol in range(alphabet_size):
            child = row[symbol]
            if child:
                failure[child] = fallback[symbol]
                breadth_first.append(child)
            else:
                row[symbol] = fallback[symbol]

    counts = []
    for text in texts:
        visits = [0] * len(transitions)
        state = 0
        for character in text:
            state = transitions[state][ord(character) - 32]
            visits[state] += 1
        for state in reversed(breadth_first):
            visits[failure[state]] += visits[state]
        counts.append([visits[terminal] for terminal in terminals])
    return {"counts": counts}

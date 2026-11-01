# SPDX-License-Identifier: MPL-2.0
"""Deterministic polynomial assignment; no AP, cosmetic or process RNG.

The minimum-cost Hungarian algorithm is O(n^3). A separate augmenting-path
feasibility pass supplies a Hall-deficient witness instead of hidden fallback.
Seed costs are not a uniform distribution over all valid perfect matchings.
"""
from hashlib import sha256
import json
VERSION = 'm222-matching-1'

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')

def solve(seed, content_ids, destination_ids, allowed, *, domain='adjacent-worlds-1', equivalence=None):
    """Return destination -> content, minimizing self matches before seeded cost.

    Allowed is a mapping of destination ID to iterable content IDs. Every input
    is normalized by stable ID. World-distance is deliberately NOT a cost.
    """
    if not isinstance(seed, str) or not seed:
        raise ValueError('Nonempty string seed required')
    cs, ds = (list(content_ids), list(destination_ids))
    if not cs or len(cs) != len(ds) or len(cs) != len(set(cs)) or (len(ds) != len(set(ds))) or any((not isinstance(x, str) or not x for x in cs + ds)):
        raise ValueError('Matching requires equal, nonempty sets of unique stable IDs')
    cs.sort()
    ds.sort()
    n = len(cs)
    if equivalence is not None and (set(equivalence) != set(cs) | set(ds) or any((not isinstance(v, str) or not v for v in equivalence.values()))):
        raise ValueError('Gameplay equivalence must cover every stable content/host ID')
    if set(allowed) != set(ds):
        raise ValueError('Allowed graph must cover exactly the destination IDs')
    ci = {c: j for j, c in enumerate(cs)}
    edges = []
    for d in ds:
        values = list(allowed[d])
        if any((c not in ci for c in values)):
            raise ValueError('Unknown allowed content at ' + d)
        edges.append(sorted({ci[c] for c in values}))
    match = [-1] * n

    def augment(i, seen):
        for j in edges[i]:
            if j in seen:
                continue
            seen.add(j)
            if match[j] == -1 or augment(match[j], seen):
                match[j] = i
                return True
        return False
    for i in range(n):
        augment(i, set())
    matched = set(match) - {-1}
    if len(matched) != n:
        left = set(range(n)) - matched
        right = set()
        pending = list(sorted(left))
        while pending:
            i = pending.pop()
            for j in edges[i]:
                if j in right:
                    continue
                right.add(j)
                if match[j] >= 0 and match[j] not in left:
                    left.add(match[j])
                    pending.append(match[j])
        detail = dict(destinations=[ds[i] for i in sorted(left)], eligible_contents=[cs[j] for j in sorted(right)], required=len(left), available=len(right))
        raise ValueError('Assignment infeasible; Hall-deficient set: ' + json.dumps(detail, sort_keys=True))
    spread = 1 << 64
    self_cost = n * spread
    infinity = (n + 1) * (self_cost + spread)
    cost = [[infinity] * n for _ in ds]
    for i, d in enumerate(ds):
        for j in edges[i]:
            c = cs[j]
            random_cost = int.from_bytes(sha256(canonical([VERSION, domain, seed, d, c])).digest()[:8], 'big')
            retained = d == c if equivalence is None else equivalence[d] == equivalence[c]
            cost[i][j] = (self_cost if retained else 0) + random_cost
    u = [0] * (n + 1)
    v = [0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [infinity] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = infinity
            j1 = 0
            for j in range(1, n + 1):
                if used[j]:
                    continue
                cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            if j1 == 0 or delta >= infinity:
                raise ValueError('Feasible matching unexpectedly exhausted')
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    result = {ds[p[j] - 1]: cs[j - 1] for j in range(1, n + 1)}
    if any((ci[result[d]] not in edges[i] for i, d in enumerate(ds))):
        raise ValueError('Matching selected forbidden pair')
    return dict(sorted(result.items()))

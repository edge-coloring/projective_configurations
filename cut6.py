import glob
import heapq
import argparse
import os
from collections import deque


#
def ReadPrimalFromFile(filePath: str):
    with open(filePath, "r") as f:
        f.readline()
        n, r = map(int, f.readline().split())
        G = [[] for _ in range(n-r)]
        degree = [0 for _ in range(n-r)]
        for i in range(n-r):
            v, d, *us = map(int, f.readline().split())
            degree[i] = d
            G[v-r-1] = list(map(lambda x: x-1,us))
        return n, r, G, degree
    assert False


# 
def LabelEdges(n:int, r: int, G: "list[list[int]]"):
    edges = set()
    for i in range(r):
        edges.add((i, (i + 1) % r))
        edges.add(((i + 1) % r, i))
    for i in range(n - r):
        for j in G[i]:
            edges.add((i + r, j))
            edges.add((j, i + r))
    def is3Cycle(i: int, j: int, k: int):
        return (i, j) in edges and (j, k) in edges and (k, i) in edges
    triangles = set()
    for i in range(n):
        for j in range(i):
            for k in range(j):
                if is3Cycle(k, j, i):
                    triangles.add((k, j, i))
    triangles = sorted(list(triangles))
    edgeIndexes = {}
    def addEdge(x, y):
        if x > y: x, y = y, x
        if (x, y) not in edgeIndexes:
            edgeIndexes[(x, y)] = len(edgeIndexes)
    for i in range(r):
        addEdge(i, (i + 1) % r)
    for a,b,c in triangles:
        addEdge(a, b)
        addEdge(b, c)
        addEdge(c, a)
    return edgeIndexes


# 
def reconstructG(n: int, r: int, G: list):
    newG = [[] for _ in range(n)]
    for i in range(r):
        newG[i].append((i+1) % r)
        newG[(i+1) % r].append(i)
    for i in range(n-r):
        v = i+r
        for u in G[i]:
            if u < v:
                newG[v].append(u)
                newG[u].append(v)
    return newG


# グラフ G 上で s から t の最短経路を列挙する。 
def shortestPaths(n: int, G: list, s: int, t: int):
    dist = [1000 for _ in range(n)]
    dist[s] = 0

    heap = []
    heapq.heappush(heap, (0, s))
    while heap:
        d, v = heapq.heappop(heap)
        for u in G[v]:
            if dist[v] + 1 < dist[u]:
                dist[u] = dist[v] + 1
                heapq.heappush(heap, (dist[u], u))

    paths = [[] for _ in range(n)]
    paths[s].append([s])

    heapq.heappush(heap, s)
    while heap:
        v = heapq.heappop(heap)
        for u in G[v]:
            if dist[u] == dist[v] + 1:
                paths[u].extend([path + [u] for path in paths[v]])
                heapq.heappush(heap, u)
    
    unique_paths = []
    for path in paths[t]:
        if path in unique_paths:
            continue
        unique_paths.append(path)
    return unique_paths


# contEdges の辺を距離にカウントしないような最短経路を求める。
def WF(n: int, r: int, G: list, contEdges: list, edgeIndexes: dict):
    dist = [[300 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for i in range(r):
        dist[i][(i+1) % r] = 1
        dist[(i+1) % r][i] = 1
    for i in range(n-r):
        for v in G[i]:
            if v < i+r:
                assert (v, i+r) in edgeIndexes
                idx = edgeIndexes[(v, i+r)]
                if str(idx) in contEdges:
                    dist[i+r][v] = 0
                    dist[v][i+r] = 0
                else:
                    dist[i+r][v] = 1
                    dist[v][i+r] = 1
    
    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][k] + dist[k][j], dist[i][j])
    return dist


# abpath; ring の頂点 a,b を繋ぐ configuration 上の path
# abpath によって configuration が2つに分断されるが、そのうち ring の a+1,a+2,...,b-1 の頂点を含む側の頂点数を計算する。
def sizeOfVertices(n: int, r: int, allG: list, abpath: list):
    seen = [-1 for _ in range(n)]
    def dfs(v: int):
        if seen[v] >= 0:
            return
        seen[v] = 1
        for u in allG[v]:
            dfs(u)
        return
            
    for v in abpath:
        seen[v] = 0
    
    a = abpath[0]
    b = abpath[-1]

    i = a+1
    while i != b:
        dfs(i)
        i = (i+1) % r
    
    s = 0
    t = 0
    for v in range(n):
        if v < r and seen[v] == 1:
            s += 1
        elif v >= r and seen[v] == 1:
            t += 1

    return s, t


def isContradiction(cutSize: int, sz: int, use7cut = False):
    return (cutSize <= 4 and sz >= 1) or \
        (cutSize == 5 and sz >= 2) or \
        (cutSize == 6 and sz >= 4) or \
        (use7cut and cutSize == 7 and sz >= 5)


def forbiddenCycle(n: int, r: int, allG: list, a: int, b: int, k: int, cutSize: int):
    assert cutSize == 6 or cutSize == 7
    b_ = b if a < b else b + r
    q = b_ - a

    if q == k:
        return False
    elif q < k:
        # D := C - P + Q
        return True
    else:
        abpaths = shortestPaths(n, allG, a, b)
        m = len(abpaths[0]) - 1
        for R in abpaths:
            if all([v < r for v in R]):
                continue
            # E := P + R
            s, t = sizeOfVertices(n, r, allG, R)
            sz = (s - (k-1) + 1) // 2 + t
            if isContradiction(k+m, sz, cutSize == 7):
                return True
        return False


def forbiddenCycleOneEdge(n: int, r: int, allG: list, a: int, b: int, k: int, cutSize: int):
    assert cutSize == 6 or cutSize == 7
    b_ = b if a < b else b + r
    q = b_ - a

    # D := C - P + Q + one edge
    Q = [v%r for v in range(a, b_+1)]
    Q.reverse()
    s, t = sizeOfVertices(n, r, allG, Q)
    sz = (s - (cutSize - k - 1) + 1) // 2 + t
    if isContradiction(cutSize - k + q + 1, sz, cutSize == 7):
        return True

    abpaths = shortestPaths(n, allG, a, b)
    m = len(abpaths[0]) - 1
    for R in abpaths:
        # E := P + R + one edge
        s, t = sizeOfVertices(n, r, allG, R)
        sz = (s - (k - 1) + 1) // 2 + t
        if isContradiction(k + m + 1, sz, cutSize == 7):
            return True

    return False
    

def isValid(n: int, r: int, allG: list, vs: list, lens: list, cutSize: int):
    assert len(vs) == len(lens)
    assert cutSize == sum(lens)

    m = len(vs)
    for i in range(m):
        if forbiddenCycle(n, r, allG, vs[i], vs[(i+1) % m], lens[i], cutSize) or \
           forbiddenCycle(n, r, allG, vs[(i+1) % m], vs[i], cutSize - lens[i], cutSize):
            return False
    return True


def isValid232_1(n: int, r: int, allG: list, a: int, b: int, c: int):
    if forbiddenCycleOneEdge(n, r, allG, a, b, 2, 7) or \
       forbiddenCycleOneEdge(n, r, allG, b, a, 5, 7) or \
       forbiddenCycle(n, r, allG, b, c, 3, 7) or \
       forbiddenCycle(n, r, allG, c, b, 4, 7) or \
       forbiddenCycleOneEdge(n, r, allG, c, a, 2, 7) or \
       forbiddenCycleOneEdge(n, r, allG, a, c, 5, 7):
        return False
    return True

def isValid232_2(n: int, r: int, allG: list, a: int, b: int, c: int, d: int):
    if forbiddenCycleOneEdge(n, r, allG, a, b, 2, 7) or \
       forbiddenCycleOneEdge(n, r, allG, b, a, 5, 7) or \
       forbiddenCycle(n, r, allG, b, c, 3, 7) or \
       forbiddenCycle(n, r, allG, c, b, 4, 7) or \
       forbiddenCycleOneEdge(n, r, allG, c, d, 2, 7) or \
       forbiddenCycleOneEdge(n, r, allG, d, c, 5, 7):
        return False
    return True

def isValid3121_L(n: int, r: int, allG: list, a: int, b: int, c: int, d: int):
    if forbiddenCycle(n, r, allG, a, b, 3, 7) or \
       forbiddenCycle(n, r, allG, b, a, 4, 7) or \
       forbiddenCycleOneEdge(n, r, allG, b, c, 1, 7) or \
       forbiddenCycleOneEdge(n, r, allG, c, b, 6, 7) or \
       forbiddenCycleOneEdge(n, r, allG, c, d, 2, 7) or \
       forbiddenCycleOneEdge(n, r, allG, d, c, 5, 7) or \
       forbiddenCycle(n, r, allG, d, a, 1, 7) or \
       forbiddenCycle(n, r, allG, a, d, 6, 7):
        return False
    return True

def isValid3121_R(n: int, r: int, allG: list, a: int, b: int, c: int, d: int):
    if forbiddenCycle(n, r, allG, a, b, 3, 7) or \
       forbiddenCycle(n, r, allG, b, a, 4, 7) or \
       forbiddenCycle(n, r, allG, b, c, 1, 7) or \
       forbiddenCycle(n, r, allG, c, b, 6, 7) or \
       forbiddenCycleOneEdge(n, r, allG, c, d, 2, 7) or \
       forbiddenCycleOneEdge(n, r, allG, d, c, 5, 7) or \
       forbiddenCycleOneEdge(n, r, allG, d, a, 1, 7) or \
       forbiddenCycleOneEdge(n, r, allG, a, d, 6, 7):
        return False
    return True


# a,b,c,d は ring にその順に並んでいる頂点
# dist[a][b] = 0
# dist[c][d] = 0
def find_ab0_cd0(n: int, r: int, contract_dist: list):
    abcds = []
    for a in range(r):
        for b in range(a+1, r):
            if contract_dist[a][b] == 0:
                for c in range(b+1, r):
                    for d in range(c+1, r):
                        if contract_dist[c][d] == 0:
                            abcds.append((a, b, c, d))
                for c in range(a+1, b):
                    for d in range(c+1, b):
                        if contract_dist[c][d] == 0:
                            abcds.append((b, a, c, d))
    return abcds


# a,b,c は ring にその順に並んでいる頂点
# dist[a][b] = 0
# dist[a][c] = 1
# dist[b][c] = 1
def find_ab0_ac1_bc1(n: int, r: int, contract_dist: list):
    abcs = []
    for a in range(r):
        for b in range(a+1, r):
            if contract_dist[a][b] == 0:
                for c in range(a+1, b):
                    if contract_dist[a][c] == 1 and contract_dist[b][c] == 1:
                        abcs.append((b, a, c))
                for c in range(b+1, a+r):
                    if contract_dist[a][c%r] == 1 and contract_dist[b][c%r] == 1:
                        abcs.append((a, b, c%r))
    return abcs


# a,b,c は ring にその順に並んでいる頂点
# dist[a][b] = 0
# dist[a][c] = 0
# dist[b][c] = 0
def find_ab0_ac0_bc0(n: int, r: int, contract_dist: list):
    abcs = []
    for a in range(r):
        for b in range(a+1, r):
            if contract_dist[a][b] == 0:
                for c in range(b+1, r):
                    if contract_dist[a][c] == 0 and contract_dist[b][c] == 0:
                        abcs.append((a, b, c))
    return abcs


# a,b,c,d は ring にその順に並んでいる頂点
# dist[a][b] = 0
# dist[c][d] = 1
def find_ab0_cd1(n: int, r: int, contract_dist: list):
    abcds = []
    for a in range(r):
        for b in range(a+1, r):
            if contract_dist[a][b] == 0:
                for c in range(b+1, a+r):
                    for d in range(c+1, a+r):
                        if contract_dist[c%r][d%r] == 1:
                            abcds.append((a, b, c%r, d%r))
                for c in range(a+1, b):
                    for d in range(c+1, b):
                        if contract_dist[c][d] == 1:
                            abcds.append((b, a, c, d))
    return abcds

# a,b,c,d は ring にその順に並んでいる頂点
# dist[a][b] = 0
# dist[b][c] = 0
# dist[c][d] = 0
def find_ab0_bc0_cd0(n: int, r: int, contract_dist: list):
    abcds = []
    for a in range(r):
        for b in range(a+1, r):
            if contract_dist[a][b] == 0:
                for c in range(b+1, r):
                    if contract_dist[b][c] == 0:
                        for d in range(c+1, r):
                            if contract_dist[c][d] == 0:
                                abcds.append((a, b, c, d))
    return abcds



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The configuration file')
    parser.add_argument("-e", "--edges", nargs="+")
    args = parser.parse_args()

    path = args.file
    edges = args.edges

    n, r, G, degree = ReadPrimalFromFile(path)
    edgeIndexes = LabelEdges(n, r, G)

    contract_dist = WF(n, r, G, edges, edgeIndexes)
    allG = reconstructG(n, r, G)

    ab0_cd0s = find_ab0_cd0(n, r, contract_dist)
    ab0_ac1_bc1s = find_ab0_ac1_bc1(n, r, contract_dist)
    ab0_ac0_bc0s = find_ab0_ac0_bc0(n, r, contract_dist)
    ab0_cd1s = find_ab0_cd1(n, r, contract_dist)
    ab0_bc0_cd0s = find_ab0_bc0_cd0(n, r, contract_dist)

    # 6cut-1
    for a, b, c, d in ab0_cd0s:
        if isValid(n, r, allG, [a,b,c,d], [2,1,2,1], 6):
            print(f"6cut-1 (2121) {a, b, c, d} is dangerous in {path}")

    # 6cut-2
    for a, b, c in ab0_ac0_bc0s:
        if isValid(n, r, allG, [a,b,c], [2,2,2], 6):
            print(f"6cut-2 (222) {a, b, c} is dangerous in {path}")

    # 7cut-1
    for a, b, c in ab0_ac0_bc0s:
        if isValid(n, r, allG, [a,b,c], [3,2,2], 7):
            print(f"7cut-1 (322) {a, b, c} is dangerous in {path}")
        if isValid(n, r, allG, [a,b,c], [2,3,2], 7):
            print(f"7cut-1 (232) {a, b, c} is dangerous in {path}")
        if isValid(n, r, allG, [a,b,c], [2,2,3], 7):
            print(f"7cut-1 (223) {a, b, c} is dangerous in {path}")

    # 7cut-2
    for a, b, c, d in ab0_cd0s:
        if isValid(n, r, allG, [a,b,c,d], [3,1,2,1], 7):
            print(f"7cut-2 (3121) {a, b, c, d} is dangerous in {path}")
        if isValid(n, r, allG, [a,b,c,d], [2,1,3,1], 7):
            print(f"7cut-2 (2131) {a, b, c, d} is dangerous in {path}")
    
    # 7cut-3
    for a, b, c in ab0_ac1_bc1s:
        if isValid(n, r, allG, [a,b,c], [3,2,2], 7):
            print(f"7cut-3 (322) {a, b, c} is dangerous in {path}")
    for a, b, c in ab0_ac0_bc0s:
        if isValid232_1(n, r, allG, a, b, c):
            print(f"7cut-3 (232_1) {a, b, c} is dangerous in {path}")
        if isValid232_1(n, r, allG, b, c, a):
            print(f"7cut-3 (232_1) {b, c, a} is dangerous in {path}")
        if isValid232_1(n, r, allG, c, a, b):
            print(f"7cut-3 (232_1) {c, a, b} is dangerous in {path}")
    for a, b, c, d in ab0_bc0_cd0s:
        if isValid232_2(n, r, allG, a, b, c, d):
            print(f"7cut-3 (232_2) {a, b, c, d} is dangerous in {path}")
        if isValid232_2(n, r, allG, b, c, d, a):
            print(f"7cut-3 (232_2) {b, c, d, a} is dangerous in {path}")
        if isValid232_2(n, r, allG, c, d, a, b):
            print(f"7cut-3 (232_2) {c, d, a, b} is dangerous in {path}")
        if isValid232_2(n, r, allG, d, a, b, c):
            print(f"7cut-3 (232_2) {d, a, b, c} is dangerous in {path}")

    # 7cut-4
    for a, b, c, d in ab0_cd1s:
        if isValid(n, r, allG, [a,b,c,d], [3,1,2,1], 7):
            print(f"7cut-4 (3121) {a, b, c, d} is dangerous in {path}")
    for a, b, c, d in ab0_cd0s:
        if isValid3121_L(n, r, allG, a, b, c, d):
            print(f"7cut-4 (3121_L) {a, b, c, d} is dangerous in {path}")
        if isValid3121_L(n, r, allG, c, d, a, b):
            print(f"7cut-4 (3121_L) {c, d, a, b} is dangerous in {path}")
        if isValid3121_R(n, r, allG, a, b, c, d):
            print(f"7cut-4 (3121_R) {a, b, c, d} is dangerous in {path}")
        if isValid3121_R(n, r, allG, c, d, a, b):
            print(f"7cut-4 (3121_R) {c, d, a, b} is dangerous in {path}")
    
if __name__ == "__main__":
    main()
    
   

   

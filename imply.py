import argparse
import math
import os
import copy


class UnionFind:
    def __init__(self, n):
        self.n = n
        self.par = [-1 for _ in range(n)]
    def find(self, u):
        if self.par[u] < 0:
            return u
        self.par[u] = self.find(self.par[u])
        return self.par[u]
    def unite(self, u, v):
        u = self.find(u)
        v = self.find(v)
        if u == v:
            return
        if self.par[u] > self.par[v]:
            u, v = v, u
        self.par[u] += self.par[v]
        self.par[v] = u
        return
    def same(self, u, v):
        return self.find(u) == self.find(v)


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


def hasCutVertex(n: int, r: int, G: list):
    num = [-1 for _ in range(n)]
    low = [-1 for _ in range(n)]
    def dfs(v: int, par: int, order: int):
        has_cutvertex = False
        num[v] = order
        order += 1
        low[v] = num[v]
        n_child = 0
        for u in G[v-r]:
            if u == par:
                continue
            if u < r:
                continue
            if num[u] != -1:
                low[v] = min(low[v], num[u])
                continue
            n_child += 1
            order, b = dfs(u, v, order)
            has_cutvertex = has_cutvertex or b
            low[v] = min(low[v], low[u])
            if par != -1 and num[v] <= low[u]:
                has_cutvertex = True
        if par == -1 and n_child >= 2:
            has_cutvertex = True
        return order, has_cutvertex
    _, res = dfs(r, -1, 0)
    return res
            

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


def makeUF(n: int, contEdges: list, edgeIndexes: dict):
    uf = UnionFind(n)
    for e, idx in edgeIndexes.items():
        if str(idx) in contEdges:
            uf.unite(e[0], e[1])
    return uf


def verticesOfRingAdjacent(n: int, r: int, G: list, u: int):
    vertices = list(filter(lambda x: x < r, G[u]))
    vertices.sort()
    for i in range(1, len(vertices)):
        if vertices[i] - vertices[i - 1] != 1:
            vertices = vertices[i:] + vertices[:i]
            break
    for i in range(1, len(vertices)):
        assert vertices[i] - vertices[i - 1] == 1 or (vertices[i - 1] == r - 1 and vertices[i] == 0), \
            f"vertices are not place in order of ring.\n G: {G}\n u: {u}"
    return vertices


def getVertex(n: int, r: int, G: list, degree: list, contEdges: list, edgeIndexes: dict):
    uf = makeUF(n, contEdges, edgeIndexes)
    # vs1 は次数が 5 より大きく、ring に 3 本の辺が出ており、そのうち、中央の辺を縮約している conf の点 v の集合。
    vs1 = []
    # vs2 は次数が 5 より大きく、ring に 3 本の辺が出ており、そのうち、端の2辺が伸びる頂点を同じ頂点とするように縮約している conf の点 v の集合。
    vs2 = []
    # vs3 は次数が 5 より大きく、ring に 3 本の辺が出ており、そのうち、vs1, vs2 にも属さない conf の点 v の集合
    vs3 = []
    for i in range(n-r):
        ring = verticesOfRingAdjacent(n, r, G, i)
        if len(ring) == 3 and degree[i] > 5:
            # 3 -> 2 imply
            assert (ring[1], i+r) in edgeIndexes
            idx = edgeIndexes[(ring[1], i+r)]

            flg = True
            if str(idx) in contEdges:
                vs1.append(i+r)
                flg = False

            if uf.same(ring[0], ring[2]):
                vs2.append(i+r)
                flg = False

            if flg:
                vs3.append(i+r)
            
    return vs1, vs2, vs3


def genConf(n: int, r: int, G: list, degree: list, vs: list, filename: str, outputDir: str):
    m = len(vs)
    for bit in range(1, 1 << m):
        newN = n
        newR = r
        newDegree = degree.copy()
        removed = set()
        for i in range(m):
            if (bit >> i & 1) > 0:
                v = vs[i]
                ring = verticesOfRingAdjacent(n, r, G, v-r)
                assert len(ring) == 3
                removed.add(ring[1])
                newDegree[v-r] -= 1
                newN -= 1
                newR -= 1
        newVid = [-1 for _ in range(n)]
        vid = 0
        for i in range(n):
            if i in removed:
                continue
            newVid[i] = vid
            vid += 1
        assert vid == newN
        conf_txt = "\n"
        conf_txt += f"{newN} {newR}\n"
        for i in range(newN-newR):
            conf_txt += f"{newR+i+1} {newDegree[i]}"
            for u in G[i]:
                if u in removed:
                    continue
                conf_txt += f" {newVid[u]+1}"
            conf_txt += "\n"
        with open(os.path.join(outputDir, f"{bit}-{filename}"), 'w') as f:
            f.write(conf_txt)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("level", help="specify 1 or 2", type=int)
    parser.add_argument("inputPath", help="An input primal configuration file")
    parser.add_argument("outputDir", help="A directory where configuration files that to be checked by reducible checker are emitted")
    parser.add_argument("outputDir2", help="A directory where configuration files that to be checked by Petersen (K6) checker and 6,7cut checker are emitted")
    parser.add_argument("edges", help="Contraction edges", nargs="+")
    args = parser.parse_args()
    assert args.level == 1 or args.level == 2
    
    n, r, G, degree = ReadPrimalFromFile(args.inputPath)
    if hasCutVertex(n, r, G):
        exit(0)
    edgeIndexes = LabelEdges(n, r, G)
    vs1, vs2, vs3 = getVertex(n, r, G, degree, args.edges, edgeIndexes)

    if len(vs2) > 0 or (len(vs1) > 0 and len(args.edges) - len(vs1) == 0):
        if args.level == 1:
            vs = vs1 + vs2
        else:
            assert args.level == 2
            vs = vs1 + vs2 + vs3
        filename = os.path.basename(args.inputPath)
        # needs reducible check
        # 3 -> 2 に変えてできる conf ファイルを出力する。
        genConf(n, r, G, degree, vs, filename, args.outputDir)
    elif len(args.edges) >= 5 and len(vs1)+len(vs2)+len(vs3) > 0:
        # needs safe reducible check (Petersen and 6,7cut check)
        # 3 -> 2 に変えてできる conf ファイルを出力する。
        vs = vs1 + vs2 + vs3
        filename = os.path.basename(args.inputPath)
        genConf(n, r, G, degree, vs, filename, args.outputDir2)
    

    
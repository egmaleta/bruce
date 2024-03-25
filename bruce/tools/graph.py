from bruce.ast import TypeNode


class Graph:
    def __init__(self, types: list[TypeNode]):
        self.types = types
        self.edges = {}
        
        for t in types:
            self.edges[t.type] = []
            
        for t in types:
            if t.parent_type:
                self.edges[t.parent_type].append(t.type)
                
    def __str__(self):
        s = ""
        for t in self.types:
            s += f"{t.type} -> {self.edges[t.type]}\n"
        return s
    
    def __repr__(self):
        return self.__str__()
    
def topological_order(types: list[TypeNode]):
    def dfs(node, graph: Graph):
        visited[node] = True
        for neighbor in graph.edges[node]:
            if neighbor and not visited[neighbor]:
                dfs(neighbor, graph)
        order.append(node)
        indexs_after.append(indexs_before[node])
        
    graph = Graph(types)
    
    visited = {}
    indexs_before = {}
    indexs_after = []
    backward_edge = False
    
    for i, t in enumerate(graph.types):
        visited[t.type] = False
        indexs_before[t.type] = i
    
    order = []
        
    for t in graph.types:
        if not visited[t.type]:
            dfs(t.type, graph)
        else:
            backward_edge = True
            
    order = order[::-1]
    indexs_after = indexs_after[::-1]
    
    return [types[i] for i in indexs_after] if not backward_edge else []
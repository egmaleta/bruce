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
            
def topological_order(types: list[TypeNode]):
    def dfs(node, graph: Graph):
        visited[node] = True
        for neighbor in graph.edges[node]:
            if neighbor and not visited[neighbor]:
                dfs(neighbor, graph)
        order.append(node)
        
    graph = Graph(types)
    
    visited = {}
    backward_edge = False
    
    for t in graph.types:
        visited[t.type] = False
    
    order = []
        
    for t in graph.types:
        if not visited[t.type]:
            dfs(t.type, graph)
        else:
            backward_edge = True
            
    return order[::-1] if not backward_edge else []
                
    def __str__(self):
        s = ""
        for t in self.types:
            s += f"{t.type} -> {self.edges[t.type]}\n"
        return s
    
    def __repr__(self):
        return self.__str__()
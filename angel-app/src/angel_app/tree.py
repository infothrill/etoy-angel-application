import os
import stat


infinity = -1

def treeWalker(node, getChildren, toEvaluate):
    """
    A generator that (lazily, recursively) applies an operation to a tree structure.
    
    @param node the tree node where we start
    @param getChildren a function f such that f(node) returns the child nodes of node
    @param toEvaluate a function g such that result, newCarryAlong = g(node, carryAlong)
    @returns an iterator over the results of applying toEvaluate to every node in the tree
    
    @see walkTest() for an example.
    """
    
    yield toEvaluate(node)
    for child in getChildren(node):
        for result in treeWalker(child, getChildren, toEvaluate):
            yield result


        
def walkTest(root = os.getcwd()):
    """
    A walk that prints all the relative path of all files in a file system rooted 
    at the current directory with respect to that directory. 
    
    What does this mean?
    For each node, we want to generate the relative path with respect to the relative
    path of the parent node, so we want to carry along the path with respect to the
    root node that we have traversed so far.
    """
    
    def te(node):
        root, visitedNodes, name = node[:3] 
        return os.sep.join(visitedNodes + [name])
    
    def absPath(node):
        return os.sep.join(
                               [node[0]] + node[1] + [node[2]]
                               )
    
    def isdir(path):
        """
        @param path the absolute (?) path of the file
        """
        return stat.S_ISDIR(os.stat(
                                    path
                                    )[stat.ST_MODE])
        
    def gc(node):
        
        root, visitedNodes, name, depth = node
        
        if depth > 10:
            raise StopIteration
        
        ab = absPath(node)
        if not isdir(ab): return []
        

        return [
                (
                 root,
                 visitedNodes + [name],
                 cc,
                 depth + 1
                 )
                for cc in
                os.listdir(ab)]

    return treeWalker((root, [], "", 0), gc, te)

if __name__ == "__main__":
    for rr in walkTest():
        print rr
    
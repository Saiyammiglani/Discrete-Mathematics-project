"""Short theory notes shown beside results (FR-16)."""

THEORY = {
    "properties": (
        "**Handshaking Lemma:** the degrees add up to twice the number of links. "
        "**Connected** means a path joins every pair of devices (found with BFS). "
        "The number of independent cycles is |E| − |V| + C; the graph is acyclic exactly when it is 0."
    ),
    "kruskal": (
        "**Kruskal** sorts links by cost and adds each one unless it joins two devices already "
        "connected. That rejected link is the heaviest on a cycle, and the **cycle property** says "
        "such a link is never needed. Union-find makes each check almost O(1); total O(E log E)."
    ),
    "prim": (
        "**Prim** grows one tree and always adds the cheapest link leaving it. This is the "
        "**cut property**: the lightest link across the cut (tree, rest) belongs to some MST. "
        "With a binary heap it runs in O(E log V)."
    ),
    "compare": (
        "A tree on n vertices has exactly n − 1 edges. Both algorithms give the same total weight; "
        "the tree itself may differ when weights tie, because an MST is not always unique."
    ),
    "vulnerability": (
        "A **bridge** is a link whose removal disconnects the graph; a **cut vertex** is a device "
        "whose removal does. Every edge of a tree is a bridge, so the cheapest design is also the "
        "most fragile. Found with Tarjan's DFS in O(V + E)."
    ),
}

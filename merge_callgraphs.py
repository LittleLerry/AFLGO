#!/usr/bin/env python3

import argparse
import networkx as nx

#* $AFLGO/distance/distance_calculator/merge_callgraphs.py -o callgraph.dot $(ls callgraph.*)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--out', type=str, required=True, help="Path to output dot file.")
    parser.add_argument('dot', nargs='+', help="Path to input dot files.")

    args = parser.parse_args()

    #* callgraph.xxx.dot

    #* nx.drawing.nx_pydot.read_dot(dot) reads the dot file specified by dot and converts it into a NetworkX graph object. 
    # The nx_pydot module in NetworkX provides functions to read and write graph representations in the DOT format.

    #* nx.DiGraph(...) creates a new instance of a directed graph (DiGraph) using the NetworkX library.

    #* G.update(...) updates an existing graph object G by incorporating the newly created graph from the dot file.
    #  This means that the graph G is modified by adding nodes and edges from the dot file's graph.

    G = nx.DiGraph()
    for dot in args.dot:
        G.update(nx.DiGraph(nx.drawing.nx_pydot.read_dot(dot)))

    #* nx.drawing.nx_pydot.write_dot(G, f) writes the graph represented by the NetworkX graph object G to the file object f
    #* in the DOT format using the write_dot() function from the nx_pydot module in NetworkX. This function converts the NetworkX 
    #* graph into a DOT representation and writes it to the specified file.
    with open(args.out, 'w') as f:
        nx.drawing.nx_pydot.write_dot(G, f)


# Main function
if __name__ == '__main__':
    main()

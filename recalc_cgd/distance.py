#!/usr/bin/env python3
# ./distance_a.py -d ./dot-files/callgraph.dot -t ./Ftargets.txt -n ./Fnames.txt -o a.txt -e extra.txt
# extra.txt is something like:
# {xmlAddID},{good_function}
# {xmlAddID},{bad_function}
import time
import argparse
import collections
import functools
import networkx as nx


class memoize:
  # From https://github.com/S2E/s2e-env/blob/master/s2e_env/utils/memoize.py

  def __init__(self, func):
    self._func = func
    self._cache = {}

  def __call__(self, *args):
    if not isinstance(args, collections.abc.Hashable):
      return self._func(args)

    if args in self._cache:
      return self._cache[args]

    value = self._func(*args)
    self._cache[args] = value
    return value

  def __repr__(self):
    # Return the function's docstring
    return self._func.__doc__

  def __get__(self, obj, objtype):
    # Support instance methods
    return functools.partial(self.__call__, obj)


#################################
# Get graph node name
#################################
def node_name (name):
  if is_cg:
    return "\"{%s}\"" % name
  else:
    return "\"{%s:" % name

#################################
# Find the graph node for a name
#################################
@memoize
def find_nodes (name):
  n_name = node_name (name)
  return [n for n, d in G.nodes(data=True) if n_name in d.get('label', '')]

##################################
# Calculate Distance
##################################

def fast_distance():
  if is_cg:
    # G is CG
    GR = nx.DiGraph.reverse(G)
    solution = {}
    # calc dis for all nodes in dist.items()
    # t is lable
    for t in targets:
      try:
        _ , dist = nx.dijkstra_predecessor_and_distance(GR, t)
        for nn, dst in dist.items():
          if nn in solution:
            d, i = solution[nn]
            d += 1.0 / (1.0 + dst)
            i += 1
            solution[nn] = [d,i]
          else:
            solution[nn] = [1.0 / (1.0 + dst),1]
      except nx.NetworkXNoPath:
          pass
    with open(args.out, "w") as out, open(args.names, "r") as f:
      for line in f.readlines():
        true_name = line.strip()
        D = -1
        for node_index in find_nodes(true_name):
          if node_index in solution:
            d , i = solution[node_index]
            if (D == -1 or D > i/d):
              D = i/d  
        if D != -1:
          out.write (true_name)
          out.write (",")
          out.write (str(D))
          out.write ("\n")
  else:
    # G is CFG
    GR = nx.DiGraph.reverse(G)
    solution = {}
    # init for Transfer BB Set or Target BB Set
    for true_name in bb_distance.keys():
      for node_index in find_nodes(true_name):
        # -1 indicates that it is special one
        solution[node_index] = [(10 * bb_distance[true_name]),-1]
  
    # distribute contribution
    for target_true_name, bb_d in bb_distance.items():
      k = len(find_nodes(target_true_name))
      if(k > 0):
        for node_index in find_nodes(target_true_name):
          try:
            _ , dist = nx.dijkstra_predecessor_and_distance(GR, node_index)
            for nn, dst in dist.items():
              if nn in solution:
                d, i = solution[nn]
              if (i != -1):
                d += 1.0 / ((1.0 + dst + 10*bb_d)*k)
                i += 1
                solution[nn] = [d,i]
              else:
                solution[nn] = [1.0 / ((1.0 + dst + 10*bb_d)*k),1]
          except nx.NetworkXNoPath:
            pass
      
    # output
    with open(args.out, "w") as out, open(args.names, "r") as f:
      for line in f.readlines():
        true_name = line.strip()
        D = -1
        for node_index in find_nodes(true_name):
          if node_index in solution:
            d , i = solution[node_index]
            if (i == -1):
              D = d
            elif (D == -1 or D > i/d):
              D = i/d  
        if D != -1:
          out.write (true_name)
          out.write (",")
          out.write (str(D))
          out.write ("\n")
##################################
# Main function
##################################
if __name__ == '__main__':
  parser = argparse.ArgumentParser ()
  parser.add_argument ('-d', '--dot', type=str, required=True, help="Path to dot-file representing the graph.")
  parser.add_argument ('-t', '--targets', type=str, required=True, help="Path to file specifying Target nodes.")
  parser.add_argument ('-o', '--out', type=str, required=True, help="Path to output file containing distance for each node.")
  parser.add_argument ('-n', '--names', type=str, required=True, help="Path to file containing name for each node.")
  parser.add_argument ('-c', '--cg_distance', type=str, help="Path to file containing call graph distance.")
  parser.add_argument ('-s', '--cg_callsites', type=str, help="Path to file containing mapping between basic blocks and called functions.")
  parser.add_argument ('-e', '--extra_function_calls', type=str, help="Path to file containing function caller and callee")# formart {f_1},{f_2}

  args = parser.parse_args ()

  print ("\nParsing %s .." % args.dot)
  G = nx.DiGraph(nx.drawing.nx_pydot.read_dot(args.dot))
  # label to index mapping
  label_to_index = {G.nodes[node]['label'].strip('"'): node for node in G.nodes()}
  # print(label_to_index)
  # print (G)

  is_cg = "Call graph" in str(G)
  print ("\nWorking in %s mode.." % ("CG" if is_cg else "CFG"))
  # add extra edges for G
  if is_cg and (args.extra_function_calls is not None):
      with open(args.extra_function_calls, 'r') as f:
        for l in f.readlines():
          s = l.strip().split(",")
          caller = label_to_index.get(s[0])
          callee = label_to_index.get(s[1])
          if ((caller is not None) and (callee is not None) and (caller != callee)):
              G.add_edge(caller, callee)
              print(str(caller)+"["+s[0]+"] and "+str(callee)+"["+s[1]+"] added")

  # Process as ControlFlowGraph
  caller = ""
  cg_distance = {}
  bb_distance = {}
  if not is_cg :

    if args.cg_distance is None:
      print ("Specify file containing CG-level distance (-c).")
      exit(1)

    elif args.cg_callsites is None:
      print ("Specify file containing mapping between basic blocks and called functions (-s).")
      exit(1)

    else:

      caller = args.dot.split(".")
      caller = caller[len(caller)-2]
      print ("Loading cg_distance for function '%s'.." % caller)

      with open(args.cg_distance, 'r') as f:
        for l in f.readlines():
          s = l.strip().split(",")
          cg_distance[s[0]] = float(s[1])

      if not cg_distance:
        print ("Call graph distance file is empty.")
        exit(0)

      with open(args.cg_callsites, 'r') as f:
        for l in f.readlines():
          s = l.strip().split(",")
          if find_nodes(s[0]):
            if s[1] in cg_distance:
              if s[0] in bb_distance:
                if bb_distance[s[0]] > cg_distance[s[1]]:
                  bb_distance[s[0]] = cg_distance[s[1]]
              else:
                bb_distance[s[0]] = cg_distance[s[1]]

      print ("Adding target BBs (if any)..")
      with open(args.targets, "r") as f:
        for l in f.readlines ():
          s = l.strip().split("/");
          line = s[len(s) - 1]
          if find_nodes(line):
            bb_distance[line] = 0
            print ("Added target BB %s!" % line)

  # Process as CallGraph
  else:

    print ("Loading targets..")
    with open(args.targets, "r") as f:
      targets = []
      for line in f.readlines ():
        line = line.strip ()
        for target in find_nodes(line):
          targets.append (target)

    if (not targets and is_cg):
      print ("No targets available")
      exit(0)

  print ("Calculating distance..")
  fast_distance()

#draw the map!
import sys
import pprint
import datetime
import re
import csv
import ast
import os
import math
import json
import string
import ast
import copy
import importlib
import gc

from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import box
from shapely.ops import cascaded_union

import numpy as np
from proc_polystr import poly_to_coords

import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.cm
import matplotlib as mpl

from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import box
from shapely.ops import cascaded_union

from matplotlib.patches import Polygon as pgn
from matplotlib.collections import PatchCollection



import whereami
from setup_target import *
from figure_helper import *
from county_lookup import *

import networkx as nx
import community
import itertools
from operator import itemgetter
from networkx.algorithms import community as cm

def heaviest(G):
	u, v, w = max(G.edges(data='weight'), key=itemgetter(2))
	return (u, v)

if len(sys.argv) < 9:
	print( "usage: python3 draw_network.py connections_file partition_file output_file size target_poly min_self min_connection max_node node_factor" )
	print( "size = X or dbfile. If X is an integer uses and X x X grid, otherwise uses polygons in dbfilename." )
	print( "target_poly = file containing outline polygon. To use default (e.g. continental US) set to none, otherwise should be map_levelX_commY.txt" )
	print( "min_self = minimum number of self mentions for a grid cell to be shown. Try 0" )
	print( "min_connection = minimum number of mentions for an edge to shown. Try 100" )
	print( "max_node = max_size of a node. Try 400" )
	print( "node_factor = Scaling factor for node sizes. Try 0.01" )
	sys.exit(1);
	
	 
G=nx.Graph()
confilename = sys.argv[1];
partfilename = sys.argv[2];
outfilename = sys.argv[3];
size = sys.argv[4]
target_poly = sys.argv[5]
min_self = 0;
min_connection = 100;
max_node = 400;
min_self = int(sys.argv[6])
min_connection = int(sys.argv[7])
max_node = int(sys.argv[8])
node_factor = float(sys.argv[9])


dbfilename = "";
try:
	size = int(size);	
	#print("interpreting", poly_type, "as gridsize");
except:
	dbfilename = size;
	#print("interpreting", poly_type, "as polygon database");
	county = county_lookup(dbfilename);


target, dims = get_target(whereami.meta_location)

if target_poly != "none":
	targetfilename = target_poly;
	target2, dims = get_place(targetfilename)
else:
	target2, dims = get_target(whereami.meta_location)
		

connections = {}
with open(confilename, 'r') as infile:
	for line in infile:
		connections = json.loads(line);

partition = {}
with open(partfilename, 'r') as infile:
	for line in infile:
		partition = json.loads(line);

vmax = float(len(set(partition.values())))
vmin = 0;
			
#regions, target2, dims = get_regions()
#com_lab = uk_label_community(partition, dims, target2, size)
#target, dims = get_target(whereami.meta_location)

################
##set up graph##
################
	
for i in connections: 

	##eliminate nodes with no self connections (usually sparsely populated)
	if (i not in connections[i]) or (connections[i][i] <= min_self): continue;

	for j in connections[i]:
		if j != i:
			if not G.has_edge(i,j): #symmetric

				##don't join to eliminated nodes
				if (j not in connections) or (j not in connections[j]) or (connections[j][j] <= min_self): continue;
				ew = connections[i][j];
				if (j in connections) and (i in connections[j]):
					ew += connections[j][i]
				if ew <= min_connection: continue;	
						
				G.add_edge( i, j, weight = ew )


solitary=[ n for n,d in G.degree if d==0 ] #should be 0
G.remove_nodes_from(solitary)
#print(solitary)
#pos = nx.circular_layout(G) #just to get a filled data structure
print(len(G.nodes), "nodes in G");

print( "mean degree " + str(1.0*sum([ d for n,d in G.degree ])/len(G.nodes)) )
print( "mean weighted degree " + str(1.0*sum([ d for n,d in G.degree(weight="weight") ])/len(G.nodes)) )
print( str(len(G.edges)) +  " edges " + str(len(G.nodes)) +  " nodes")
print( "density " + str(len(G.edges)/( 0.5*(len(G.nodes)-1)*len(G.nodes))))


emap = matplotlib.cm.binary
ews = [ G[u][v]['weight'] for u,v in G.edges()]
sedges = sorted(ews)
max_edge = sedges[-1]
min_edge = sedges[0];

cols = [ 'r', 'g', 'b', 'yellow', 'm', 'c', 'lightpink', 'saddlebrown', 'orange', 'olive', 'moccasin', 'chartreuse', 'violet', 'chocolate', 'teal', 'grey' ]


fig = plt.figure(figsize=(12, 12))
ax = fig.add_subplot(111)
setup_figure(ax, dims, target, zorder = 1)
plt.axis("off")	

node_size = [];
node_list = [];
edge_list = [];
node_color = [];
pos = {}
for box_id, box_number, mp in generate_land(dims, target2, size, contains=False):

	if str(box_id) in partition and str(box_id) in G.nodes:
		
		xmin, ymin, xmax, ymax = box_to_coords(mp)
		if target2.intersects(mp):
			pos[str(box_id)] = np.array([ 0.5*(xmin+xmax), 0.5*(ymin+ymax)])


			n = str(box_id);
			node_list.append(n)
			if n in connections:
				if n in connections[n]:
					node_size.append( min( max_node, node_factor*(connections[n][n]) ) );
				else: #no self edge
					node_size.append(0);
			else: #no self edge
				node_size.append(0);

			node_color.append( cols[ partition[ str(n) ] % len(cols) ]  );

for n in node_list:
	for j in G[n]:
		if j in node_list:
			edge_list.append( (n, j) )

print("include", len(node_list) )	
		
"""		
cb = 0;
for box_id, box_number, mp in generate_land(dims, target2, size, contains=False):

	xmin, ymin, xmax, ymax = box_to_coords(mp)

	if str(box_id) in partition:
		##draw costal edges
		mp = box(xmin, ymin, xmax, ymax);
		if target2.contains(mp):
			patch = mpl.patches.Rectangle( (xmin, ymin) , (xmax-xmin), (ymax-ymin), edgecolor='k', linestyle='dashed', facecolor='none', alpha=0.5, zorder=0  );
			ax.add_patch(patch)
			cb += 1
		else:
			poly = target2.intersection(mp)
			polys = poly_to_coords(poly)
			for p in polys:
				patch = pgn(p[0], edgecolor='k', linestyle='dashed', facecolor='none', alpha=0.5, zorder=0  );
				ax.add_patch(patch)
				cb += 1

print(cb, "boxes")
print(len(G.nodes), "nodes");
print(len(node_list), "unodes");
"""

#nx.draw_networkx_edges(G, pos, edge_cmap=emap, edge_vmin=min_edge,edge_vmax=max_edge, width=0.01)
nx.draw_networkx_edges(G, pos, width=0.1, alpha=1, edgelist=edge_list)
nx.draw_networkx_nodes(G, pos, nodelist=node_list, node_size=node_size, node_color=node_color)

plt.savefig(outfilename);
#plt.show();
plt.close();	

	



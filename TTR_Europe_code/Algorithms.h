// Here are the algorithms for the weighted map, some stuff here......
// This file will contain the 1 city to 1 city finding, then multi-city linking, then both given links taken
// All of them will take in a tuple that encodes weights assigned to different attributes, likely planning a null entry to default to trains used,
// But options for, ex a tunnel counts as one extra will be available...


#ifndef ALGORITHMS_H
#define ALGORITHMS_H
#include <string>
#include <priority_queue>
#include <unordered_map>
#include <tuple>
#include <vector>
using namespace std

class Algorithm (
	public:
		/**
		* Contructor, doesn't have any fields...
		*/
		Algorithm();

		/**
		* Returns the shortest path from city 1 to city 2, given a weighing system
		* @param city1 The name of the source city
		* @param city2 The name of the destination city
		* @param weight The tuple outlining wieghing system
		* @return The list of city pairs to connect
		*/
		vector<tuple<string, string>> one_city_shortest_path(string const & city1, string const & city2, tuple<int, int, int, int, int> weight);

		/**
		* Returns the shortest connecting path between all given cities, given a weighing system
		* @param city_list The names of the cities to connect
		* @param weight The tuple outlining weighing system
		* @return The list of city pairs to connect
		*/
		vector<tuple<string, string>> multi_city_shortest_path(vector<string> city_list, tuple<int, int, int, int, int> weight);

		// More to come, likely a rewrite of the above two with certain exclusions in the algorithm... 
		// But this is probably fine for now...
);
#endif

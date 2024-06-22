// This is a file holding the information on the actual game board of Ticket To Ride Europe

#ifndef BOARD_H
#define BOARD_H

#include <string>
#include <vector>
#include <tuple>
#include <unordered_map>
using namespace std;

class Board {
	public:
		unordered_map<string, vector<tuple<int, string, int, string, bool, bool>>> board;
		
		/**
		* Constructor, initializes a fully ready TTR Europe Board, with all cities/connections
		*/
		Board();

		/**
		* Return number of neighbors of a particular city
		* @param city The name of the start city
		* @return The number of neighbors of that city
		*/
		int num_neighbors(string const & city);

		/**
		* Return a vector of the neighbors of a particular city
		* @param city The name of the start city
		* @return The vector of that city's neighbors
		*/
		vector<string> neighbors(string const & city);

		/**
		* Return the connection info for the indicated cities
		* @param city1 The name of the source city
		* @param city2 The name of the destination city
		* @return The tuple containing the connection info
		*/
		tuple<int, int, string, bool, bool> edge_data(string const & city1, string const & city2);
};
#endif

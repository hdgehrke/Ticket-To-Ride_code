// This is a file containing information about the routes in Ticket To Ride Europe

#ifndef ROUTES_H
#define ROUTES_H
#include <string>
#include <tuple>
#include <vector>
using namespace std;

class Routes {
	public:
		vector<tuple<string, string, int, bool>> routes;

		/**
		* Initializes the Routes object, fills in known info
		*/
		Routes();

		/**
		* Returns a list of routes that include the specified city
		* @param city The city from which to find routes
		* @return The routes out of city
		*/
		vector<tuple<string, string, int, bool>> routes_out(string const & city);

		/**
		* Returns the score of the route between specified cities, 0 if no route found
		* @param city1 The first specified city
		* @param city2 The second specified city
		* @return The score of the route, if found, if not, 0
		*/
		int route_score(string const & city1, string const & city2);
};
#endif

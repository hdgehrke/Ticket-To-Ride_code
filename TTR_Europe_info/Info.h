// This file contains misc info about Ticket To Ride Europe

#ifndef INFO_H
#define INFO_H
#include <unordered_map>
#include <string>
using namespace std;

class Info {
	public:
		int numTrains;
		int numStations;
		int numRoutes;
		int numCards;
		int longBonus;
		unordered_map<int, int> trainScoring;
		unordered_map<string, int> colorCardCount;

		/**
		* Initializes Info object, known data
		*/
		Info();
};
#endif

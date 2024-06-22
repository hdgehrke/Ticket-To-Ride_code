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
		map<int, int> trainScoring;
		map<string, int> colorCardCount;

		/**
		* Initializes Info object, known data
		*/
		Info();
};
#endif

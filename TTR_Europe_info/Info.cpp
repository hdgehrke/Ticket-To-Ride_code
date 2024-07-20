#include "Info.h"

Info::Info() {
	numTrains = 45;
	numStations = 3;
	numRoutes = 46;
	numCards = 158;
	longBonus = 10;
	trainScoring[1] = 1;
	trainScoring[2] = 2;
	trainScoring[3] = 4;
	trainScoring[4] = 7;
	trainScoring[6] = 15;
	trainScoring[8] = 21;
	colorCardCount["P"] = 12;
	colorCardCount["W"] = 12;
	colorCardCount["B"] = 12;
	colorCardCount["Y"] = 12;
	colorCardCount["O"] = 12;
	colorCardCount["K"] = 12;
	colorCardCount["R"] = 12;
	colorCardCount["G"] = 12;
	colorCardCount["L"] = 14;
}

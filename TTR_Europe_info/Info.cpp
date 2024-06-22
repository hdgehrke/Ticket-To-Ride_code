#include "Info.h"

Info::Info() {
	numTrains = 45;
	numStations = 3;
	numRoutes = 46;
	numCards = 158;
	longBonus = 10;
	trainScoring = {{1,1},{2,2},{3,4},{4,7},{6,15},{8,21}};
	colorCardCount = {{"P",12},{"W",12},{"B",12},{"Y",12},{"O",12},{"K",12},{"R",12},{"G",12},{"L",14}};
}

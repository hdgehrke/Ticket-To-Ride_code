#include "Routes.h"

Routes::Routes() {
	routes.push_back(make_tuple("Kobenhavn", "Erzurum", 21, true));
	routes.push_back(make_tuple("Cadiz", "Stockholm", 21, true));
	routes.push_back(make_tuple("Edinburgh", "Athina", 21, true));
	routes.push_back(make_tuple("Brest", "Petrograd", 20, true));
	routes.push_back(make_tuple("Palermo", "Moskva", 20, true));
	routes.push_back(make_tuple("Lisboa", "Danzic", 20, true));
	routes.push_back(make_tuple("Frankfurt", "Smolensk", 13, false));
	routes.push_back(make_tuple("Berlin", "Moskva", 12, false));
	routes.push_back(make_tuple("Amsterdam", "Wilno", 12, false));
	routes.push_back(make_tuple("Stockholm", "Wien", 11, false));
	routes.push_back(make_tuple("Athina", "Wilno", 11, false));
	routes.push_back(make_tuple("Angora", "Kharkov", 10, false));
	routes.push_back(make_tuple("Venezia", "Constantinople", 10, false));
	routes.push_back(make_tuple("Riga", "Bucuresti", 10, false));
	routes.push_back(make_tuple("London", "Wien", 10, false));
	routes.push_back(make_tuple("Essen", "Kyiv", 10, false));
	routes.push_back(make_tuple("Berlin", "Roma", 9, false));
	routes.push_back(make_tuple("Bruxelles", "Danzic", 9, false));
	routes.push_back(make_tuple("Madrid", "Zurich", 8, false));
	routes.push_back(make_tuple("Kyiv", "Sochi", 8, false));
	routes.push_back(make_tuple("Palermo", "Constantinople", 8, false));
	routes.push_back(make_tuple("Barcelona", "Munchen", 8, false));
	routes.push_back(make_tuple("Brest", "Venezia", 8, false));
	routes.push_back(make_tuple("Madrid", "Dieppe", 8, false));
	routes.push_back(make_tuple("Sarajevo", "Sevastopol", 8, false));
	routes.push_back(make_tuple("Smolensk", "Rostov", 8, false));
	routes.push_back(make_tuple("Marseille", "Essen", 8, false));
	routes.push_back(make_tuple("Barcelona", "Bruxelles", 8, false));
	routes.push_back(make_tuple("Roma", "Smyrna", 8, false));
	routes.push_back(make_tuple("Paris", "Wien", 8, false));
	routes.push_back(make_tuple("Berlin", "Bucresti", 8, false));
	routes.push_back(make_tuple("Brest", "Marseille", 7, false));
	routes.push_back(make_tuple("Edinburgh", "Paris", 7, false));
	routes.push_back(make_tuple("Amsterdam", "Pamplona", 7, false));
	routes.push_back(make_tuple("Paris", "Zagrab", 7, false));
	routes.push_back(make_tuple("London", "Berlin", 7, false));
	routes.push_back(make_tuple("Kyiv", "Petrograd", 6, false));
	routes.push_back(make_tuple("Zurich", "Brindisi", 6, false));
	routes.push_back(make_tuple("Zagrab", "Brindisi", 6, false));
	routes.push_back(make_tuple("Zurich", "Budapest", 6, false));
	routes.push_back(make_tuple("Warszawa", "Smolensk", 6, false));
	routes.push_back(make_tuple("Erzurum", "Rostov", 5, false));
	routes.push_back(make_tuple("Frankfurt", "Kobenhavn", 5, false));
	routes.push_back(make_tuple("Budapest", "Sofia", 5, false));
	routes.push_back(make_tuple("Athina", "Angora", 5, false));
	routes.push_back(make_tuple("Sofia", "Smyrna", 5, false));
}

vector<tuple<string, string, int, bool>> Routes::routes_out(string const & city) {
	vector<tuple<string, string, int, bool>> toReturn;
	for (auto route : routes) {
		if ((city == get<0>(route)) || (city == get<1>(route))) {
			toReturn.push_back(route);
		}
	}
	return toReturn;
}

int Routes::route_score(string const & city1, string const & city2) {
	if (city1 == city2) { return 0; }
	for (auto route : routes_out(city1)) {
		if ((city2 == get<0>(route)) || (city2 == get<1>(route))) {
			return get<2>(route); // return the number attached
		}
	}
	return 0; // not found
}

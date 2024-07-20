#include "Board.h"

Board::Board() {
	board["Cadiz"].push_back(make_tuple(3, "Madrid", 0, "O", false, false));
	board["Cadiz"].push_back(make_tuple(2, "Lisboa", 0, "B", false, false));
	board["Lisboa"].push_back(make_tuple(2, "Cadiz", 0, "B", false, false));
	board["Lisboa"].push_back(make_tuple(3, "Madrid", 0, "P", false, false));
	board["Madrid"].push_back(make_tuple(3, "Lisboa", 0, "P", false, false));
	board["Madrid"].push_back(make_tuple(3, "Cadiz", 0, "O", false, false));
	board["Madrid"].push_back(make_tuple(2, "Bacelona", 0, "Y", false, false));
	board["Madrid"].push_back(make_tuple(3, "Pamplona", 0, "KW", true, true));
	board["Barcelona"].push_back(make_tuple(2, "Madrid", 0, "Y", false, false));
	board["Barcelona"].push_back(make_tuple(2, "Pamplona", 0, "X", true, false));
	board["Barcelona"].push_back(make_tuple(4, "Marseille", 0, "X", false, false));
	board["Pamplona"].push_back(make_tuple(2, "Barcelona", 0, "X", true, false));
	board["Pamplona"].push_back(make_tuple(3, "Madrid", 0, "KW", true, true));
	board["Pamplona"].push_back(make_tuple(4, "Brest", 0, "P", false, false));
	board["Pamplona"].push_back(make_tuple(4, "Paris", 0, "GB", false, true));
	board["Pamplona"].push_back(make_tuple(4, "Marseille", 0, "R", false, false));
	board["Marseille"].push_back(make_tuple(4, "Barcelona", 0, "X", false, false));
	board["Marseille"].push_back(make_tuple(4, "Pamplona", 0, "R", false, false));
	board["Marseille"].push_back(make_tuple(4, "Paris", 0, "X", false, false));
	board["Marseille"].push_back(make_tuple(2, "Zurich", 0, "P", true, false));
	board["Marseille"].push_back(make_tuple(4, "Roma", 0, "X", true, false));
	board["Brest"].push_back(make_tuple(4, "Pamplona", 0, "P", false, false));
	board["Brest"].push_back(make_tuple(3, "Paris", 0, "K", false, false));
	board["Brest"].push_back(make_tuple(2, "Dieppe", 0, "O", false, false));
	board["Paris"].push_back(make_tuple(3, "Brest", 0, "K", false, false));
	board["Paris"].push_back(make_tuple(4, "Pamplona", 0, "BG", false, true));
	board["Paris"].push_back(make_tuple(4, "Marseille", 0, "X", false, false));
	board["Paris"].push_back(make_tuple(3, "Zurich", 0, "X", true, false));
	board["Paris"].push_back(make_tuple(3, "Frankfurt", 0, "WO", false, true));
	board["Paris"].push_back(make_tuple(2, "Bruxelles", 0, "YR", false, true));
	board["Paris"].push_back(make_tuple(1, "Dieppe", 0, "P", false, false));
	board["Dieppe"].push_back(make_tuple(1, "Paris", 0, "P", false, false));
	board["Dieppe"].push_back(make_tuple(2, "Brest", 0, "O", false, false));
	board["Dieppe"].push_back(make_tuple(2, "London", 1, "XX", false, true));
	board["Dieppe"].push_back(make_tuple(2, "Bruxelles", 0, "G", false, false));
	board["London"].push_back(make_tuple(2, "Amsterdam", 2, "X", false, false));
	board["London"].push_back(make_tuple(2, "Dieppe", 1, "X", false, true));
	board["London"].push_back(make_tuple(4, "Edinburgh", 0, "OK", false, true));
	board["Edinburgh"].push_back(make_tuple(4, "London", 0, "OK", false, true));
	board["Amsterdam"].push_back(make_tuple(2, "London", 2, "X", false, false));
	board["Amsterdam"].push_back(make_tuple(3, "Essen", 0, "Y", false, false));
	board["Amsterdam"].push_back(make_tuple(2, "Frankfurt", 0, "W", false, false));
	board["Amsterdam"].push_back(make_tuple(1, "Bruxelles", 0, "K", false, false));
	board["Bruxelles"].push_back(make_tuple(1, "Amsterdam", 0, "K", false, false));
	board["Bruxelles"].push_back(make_tuple(2, "Dieppe", 0, "G", false, false));
	board["Bruxelles"].push_back(make_tuple(2, "Paris", 0, "RY", false, true));
	board["Bruxelles"].push_back(make_tuple(2, "Frankfurt", 0, "B", false, false));
	board["Zurich"].push_back(make_tuple(3, "Paris", 0, "X", true, false));
	board["Zurich"].push_back(make_tuple(2, "Marseille", 0, "P", true, false));
	board["Zurich"].push_back(make_tuple(2, "Venezia", 0, "G", true, false));
	board["Zurich"].push_back(make_tuple(2, "Munchen", 0, "Y", true, false));
	board["Frankfurt"].push_back(make_tuple(3, "Paris", 0, "WO", false, true));
	board["Frankfurt"].push_back(make_tuple(2, "Bruxelles", 0, "B", false, false));
	board["Frankfurt"].push_back(make_tuple(2, "Amsterdam", 0, "W", false, false));
	board["Frankfurt"].push_back(make_tuple(2, "Essen", 0, "G", false, false));
	board["Frankfurt"].push_back(make_tuple(3, "Berlin", 0, "RK", false, true));
	board["Frankfurt"].push_back(make_tuple(2, "Munchen", 0, "P", false, false));
	board["Essen"].push_back(make_tuple(3, "Amsterdam", 0, "Y", false, false));
	board["Essen"].push_back(make_tuple(2, "Frankfurt", 0, "G", false, false));
	board["Essen"].push_back(make_tuple(2, "Berlin", 0, "B", false, false));
	board["Essen"].push_back(make_tuple(3, "Kobenhavn", 1, "XX", false, true));
	board["Kobenhavn"].push_back(make_tuple(3, "Essen", 1, "XX", false, true));
	board["Kobenhavn"].push_back(make_tuple(3, "Stockholm", 0, "WY", false, true));
	board["Stockholm"].push_back(make_tuple(3, "Kobenhavn", 0, "WY", false, true));
	board["Stockholm"].push_back(make_tuple(8, "Petrograd", 0, "X", true, false));
	board["Berlin"].push_back(make_tuple(2, "Essen", 0, "B", false, false));
	board["Berlin"].push_back(make_tuple(3, "Frankfurt", 0, "RK", false, true));
	board["Berlin"].push_back(make_tuple(3, "Wien", 0, "G", false, false));
	board["Berlin"].push_back(make_tuple(4, "Warszawa", 0, "PY", false, true));
	board["Berlin"].push_back(make_tuple(4, "Danzic", 0, "X", false, false));
	board["Munchen"].push_back(make_tuple(3, "Wien", 0, "O", false, false));
	board["Munchen"].push_back(make_tuple(2, "Frankfurt", 0, "P", false, false));
	board["Munchen"].push_back(make_tuple(2, "Zurich", 0, "Y", true, false));
	board["Munchen"].push_back(make_tuple(2, "Venezia", 0, "B", true, false));
	board["Venezia"].push_back(make_tuple(2, "Munchen", 0, "B", true, false));
	board["Venezia"].push_back(make_tuple(2, "Zurich", 0, "G", true, false));
	board["Venezia"].push_back(make_tuple(2, "Zagrab", 0, "X", false, false));
	board["Venezia"].push_back(make_tuple(2, "Roma", 0, "K", false, false));
	board["Roma"].push_back(make_tuple(4, "Marseille", 0, "X", true, false));
	board["Roma"].push_back(make_tuple(2, "Venezia", 0, "K", false, false));
	board["Roma"].push_back(make_tuple(2, "Brindisi", 0, "W", false, false));
	board["Roma"].push_back(make_tuple(4, "Palermo", 1, "X", false, false));
	board["Palermo"].push_back(make_tuple(4, "Roma", 1, "X", false, false));
	board["Palermo"].push_back(make_tuple(6, "Smyrna", 2, "X", false, false));
	board["Palermo"].push_back(make_tuple(3, "Brindisi", 1, "X", false, false));
	board["Brindisi"].push_back(make_tuple(3, "Palermo", 1, "X", false, false));
	board["Brindisi"].push_back(make_tuple(2, "Roma", 0, "W", false, false));
	board["Brindisi"].push_back(make_tuple(4, "Athina", 1, "X", false, false));
	board["Athina"].push_back(make_tuple(4, "Brindisi", 1, "X", false, false));
	board["Athina"].push_back(make_tuple(4, "Sarajevo", 0, "G", false, false));
	board["Athina"].push_back(make_tuple(3, "Sofia", 0, "P", false, false));
	board["Athina"].push_back(make_tuple(2, "Smyrna", 1, "X", false, false));
	board["Smyrna"].push_back(make_tuple(2, "Athina", 1, "X", false, false));
	board["Smyrna"].push_back(make_tuple(2, "Constantinople", 0, "X", true, false));
	board["Smyrna"].push_back(make_tuple(3, "Angora", 0, "O", true, false));
	board["Smyrna"].push_back(make_tuple(6, "Palermo", 2, "X", false, false));
	board["Zagrab"].push_back(make_tuple(2, "Venezia", 0, "X", false, false));
	board["Zagrab"].push_back(make_tuple(3, "Sarajevo", 0, "R", false, false));
	board["Zagrab"].push_back(make_tuple(2, "Budapest", 0, "O", false, false));
	board["Zagrab"].push_back(make_tuple(2, "Wien", 0, "X", false, false));
	board["Wien"].push_back(make_tuple(2, "Zagrab", 0, "X", false, false));
	board["Wien"].push_back(make_tuple(3, "Munchen", 0, "O", false, false));
	board["Wien"].push_back(make_tuple(3, "Berlin", 0, "G", false, false));
	board["Wien"].push_back(make_tuple(4, "Warszawa", 0, "B", false, false));
	board["Wien"].push_back(make_tuple(1, "Budapest", 0, "WR", false, true));
	board["Petrograd"].push_back(make_tuple(8, "Stockholm", 0, "X", true, false));
	board["Petrograd"].push_back(make_tuple(4, "Riga", 0, "X", false, false));
	board["Petrograd"].push_back(make_tuple(4, "Wilno", 0, "B", false, false));
	board["Petrograd"].push_back(make_tuple(4, "Moskva", 0, "W", false, false));
	board["Danzic"].push_back(make_tuple(4, "Berlin", 0, "X", false, false));
	board["Danzic"].push_back(make_tuple(3, "Riga", 0, "K", false, false));
	board["Danzic"].push_back(make_tuple(2, "Warszawa", 0, "X", false, false));
	board["Warszawa"].push_back(make_tuple(2, "Danzic", 0, "X", false, false));
	board["Warszawa"].push_back(make_tuple(4, "Berlin", 0, "PY", false, true));
	board["Warszawa"].push_back(make_tuple(4, "Wien", 0, "B", false, false));
	board["Warszawa"].push_back(make_tuple(4, "Kyiv", 0, "X", false, false));
	board["Warszawa"].push_back(make_tuple(3, "Wilno", 0, "R", false, false));
	board["Budapest"].push_back(make_tuple(6, "Kyiv", 0, "X", true, false));
	board["Budapest"].push_back(make_tuple(1, "Wien", 0, "RW", false, true));
	board["Budapest"].push_back(make_tuple(2, "Zabreb", 0, "O", false, false));
	board["Budapest"].push_back(make_tuple(4, "Bucuresti", 0, "X", true, false));
	board["Budapest"].push_back(make_tuple(3, "Sarajevo", 0, "P", false, false));
	board["Sarajevo"].push_back(make_tuple(3, "Budapest", 0, "P", false, false));
	board["Sarajevo"].push_back(make_tuple(3, "Zagrab", 0, "R", false, false));
	board["Sarajevo"].push_back(make_tuple(4, "Athina", 0, "G", false, false));
	board["Sarajevo"].push_back(make_tuple(2, "Sofia", 0, "X", true, false));
	board["Sofia"].push_back(make_tuple(2, "Sarajevo", 0, "X", true, false));
	board["Sofia"].push_back(make_tuple(3, "Athina", 0, "P", false, false));
	board["Sofia"].push_back(make_tuple(3, "Constantinople", 0, "B", false, false));
	board["Sofia"].push_back(make_tuple(2, "Bucuresti", 0, "X", true, false));
	board["Riga"].push_back(make_tuple(3, "Danzic", 0, "K", false, false));
	board["Riga"].push_back(make_tuple(4, "Petrograd", 0, "X", false, false));
	board["Riga"].push_back(make_tuple(4, "Wilno", 0, "G", false, false));
	board["Wilno"].push_back(make_tuple(4, "Riga", 0, "G", false, false));
	board["Wilno"].push_back(make_tuple(3, "Warszawa", 0, "R", false, false));
	board["Wilno"].push_back(make_tuple(3, "Smolensk", 0, "Y", false, false));
	board["Wilno"].push_back(make_tuple(4, "Petrograd", 0, "B", false, false));
	board["Wilno"].push_back(make_tuple(2, "Kyiv", 0, "X", false, false));
	board["Moskva"].push_back(make_tuple(4, "Petrograd", 0, "W", false, false));
	board["Moskva"].push_back(make_tuple(4, "Kharkov", 0, "X", false, false));
	board["Moskva"].push_back(make_tuple(2, "Smolensk", 0, "O", false, false));
	board["Smolensk"].push_back(make_tuple(2, "Moskva", 0, "O", false, false));
	board["Smolensk"].push_back(make_tuple(3, "Wilno", 0, "Y", false, false));
	board["Smolensk"].push_back(make_tuple(3, "Kyiv", 0, "R", false, false));
	board["Kyiv"].push_back(make_tuple(3, "Smolensk", 0, "R", false, false));
	board["Kyiv"].push_back(make_tuple(4, "Kharkov", 0, "X", false, false));
	board["Kyiv"].push_back(make_tuple(2, "Wilno", 0, "X", false, false));
	board["Kyiv"].push_back(make_tuple(6, "Budapest", 0, "X", true, false));
	board["Kyiv"].push_back(make_tuple(4, "Warszawa", 0, "X", false, false));
	board["Kyiv"].push_back(make_tuple(4, "Bucuresti", 0, "X", false, false));
	board["Bucuresti"].push_back(make_tuple(4, "Kyiv", 0, "X", false, false));
	board["Bucuresti"].push_back(make_tuple(4, "Sevastopol", 0, "W", false, false));
	board["Bucuresti"].push_back(make_tuple(4, "Budapest", 0, "X", true, false));
	board["Bucuresti"].push_back(make_tuple(2, "Sofia", 0, "X", true, false));
	board["Bucuresti"].push_back(make_tuple(3, "Constantinople", 0, "Y", false, false));
	board["Constantinople"].push_back(make_tuple(3, "Bucuresti", 0, "Y", false, false));
	board["Constantinople"].push_back(make_tuple(4, "Sevastopol", 2, "X", false, false));
	board["Constantinople"].push_back(make_tuple(3, "Sofia", 0, "B", false, false));
	board["Constantinople"].push_back(make_tuple(2, "Smyrna", 0, "X", true, false));
	board["Constantinople"].push_back(make_tuple(2, "Angora", 0, "X", true, false));
	board["Angora"].push_back(make_tuple(2, "Constantinople", 0, "X", true, false));
	board["Angora"].push_back(make_tuple(3, "Smyrna", 0, "O", true, false));
	board["Angora"].push_back(make_tuple(3, "Erzurum", 0, "K", false, false));
	board["Erzurum"].push_back(make_tuple(3, "Angora", 0, "K", false, false));
	board["Erzurum"].push_back(make_tuple(3, "Sochi", 0, "R", true, false));
	board["Erzurum"].push_back(make_tuple(4, "Sevastopol", 2, "X", false, false));
	board["Sevastopol"].push_back(make_tuple(4, "Erzurum", 2, "X", false, false));
	board["Sevastopol"].push_back(make_tuple(4, "Constantinople", 2, "X", false, false));
	board["Sevastopol"].push_back(make_tuple(4, "Bucuresti", 0, "W", false, false));
	board["Sevastopol"].push_back(make_tuple(4, "Rostov", 0, "X", false, false));
	board["Sevastopol"].push_back(make_tuple(2, "Sochi", 1, "X", false, false));
	board["Sochi"].push_back(make_tuple(2, "Sevastopol", 1, "X", false, false));
	board["Sochi"].push_back(make_tuple(3, "Erzurum", 0, "R", true, false));
	board["Sochi"].push_back(make_tuple(2, "Rostov", 0, "X", false, false));
	board["Rostov"].push_back(make_tuple(2, "Sochi", 0, "X", false, false));
	board["Rostov"].push_back(make_tuple(4, "Sevastopol", 0, "X", false, false));
	board["Rostov"].push_back(make_tuple(2, "Kharkov", 0, "G", false, false));
	board["Kharkov"].push_back(make_tuple(2, "Rostov", 0, "G", false, false));
	board["Kharkov"].push_back(make_tuple(4, "Moskva", 0, "X", false, false));
	board["Kharkov"].push_back(make_tuple(4, "Kyiv", 0, "X", false, false));
}

int Board::num_neighbors(string const & city) {
	return board[city].size();
}

vector<string> Board::neighbors(string const & city) {
	vector<string> toReturn;
	for (auto tupe : board[city]) {
		toReturn.push_back(get<1>(tupe));
	}
	return toReturn;
}

tuple<int, int, string, bool, bool> Board::edge_data(string const & city1, string const & city2) {
	tuple<int, int, string, bool, bool> toReturn;
	for (auto tupe : board[city1]) {
		if (get<1>(tupe) == city2) { // match found
			toReturn = make_tuple(get<0>(tupe), get<2>(tupe), get<3>(tupe), get<4>(tupe), get<5>(tupe));
		}
	}
	return toReturn; // will return whatever null value toReturn is initialized as if no match found
}

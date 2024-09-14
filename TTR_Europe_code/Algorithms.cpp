// .cpp file for algorithms....

#include ALGORITHMS_H

Algorithms::Algorithms() {}

vecotr<tuple<string, string>> Algorithms::one_city_shortest_path(string const & city1, string const & city2, tuple<int, int, int, int, int> weight) {
	// pseudocode because i cannot recall c++ syntax for queues... fml
	
	// Whip up a priority_queue with tuple<string, string, int> and int dist as the sortable thing...
	// Whip up a vector of tuple<string, string> to hold the result stuffs
	// Ugh need to take in a board fml...
	// Loop through board -> make tuples of curr, prev, dist, sort on dist, initialize to city, "", max(int)
	// Or whip up a map instead???
	// Either way: struct[city1] = (city1, city1, 0)
	// Start while loop while queue not empty:
	//	/ curr = queue.top();
	//	/ queue.pop();
	//	/ for neigh in board.neighbors(curr[0]) {
	//	/	/ new_dist = curr[2] + wiegh(board.edge_data(curr[0],neigh), weight) <- this weights and updates dist
	// 	/ 	/ if new_dist < struct[neigh][2] { struct[neigh][2] = new_dist } <- found shorter distance
	// 	/ 	/ OH: before doing this, make sure neigh hasn't been visited (if it has the if won't ever be true, but make it faster lmao...
	// 	/ Maybe this before the for??
	// 	/ if curr[0] == city2 { break } <- relevant info should be fine...
	// Maybe preprosses to make sure both cities are in the board?
	// Go through struct, starting with city2, and load up struct[_][0],[1] into a tuple, and plop that tuple onto to_return
	// return
	// include smth about if wieght==null -> (1,0,0,0,0)...}
}

vector<tuple<string, string>> Algorithms::multi_city_shortest_path(vector<string> city_list, tuple<int, int, int, int, int> weight, Board::Board board) {}

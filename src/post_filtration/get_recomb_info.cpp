#include "get_recomb_info.hpp"
#include "src/mutation_annotated_tree.hpp"
#include "src/ripples/util/text_parser.hpp"
#include <algorithm>
#include <array>
#include <boost/algorithm/string/join.hpp>
#include <boost/iostreams/filter/gzip.hpp>
#include <boost/iostreams/filter/lzma.hpp>
#include <boost/iostreams/filter/zlib.hpp>
#include <boost/iostreams/filtering_stream.hpp>
#include <boost/tokenizer.hpp>
#include <ctime>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <string_view>
#include <time.h>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

std::vector<std::string> get_node_mutations(MAT::Tree &T,
                                            const std::string &node_id) {
    MAT::Node *node = T.get_node(node_id);
    if (!node) {
        printf("[Error] Node id is null: %s\n", node_id.c_str());
        exit(1);
    }

    // Stack for last-in first-out ordering
    std::stack<std::string> mutation_stack;
    std::unordered_set<int> positions_seen;
    std::vector<MAT::Mutation> curr_node_mutations = node->mutations;

    if (curr_node_mutations.size() > 0) {
        // Number of mutations on the current code
        size_t num_mutations = curr_node_mutations.size();

        for (size_t k = 0; k < num_mutations; k++) {
            mutation_stack.push(curr_node_mutations[k].get_string());
            int pos = std::stoi(curr_node_mutations[k].get_string().substr(
                1, curr_node_mutations[k].get_string().size() - 2));
            positions_seen.insert(pos);
        }
    }

    // Mutations on the ancestors of node
    for (auto anc_node : T.rsearch(node_id)) {
        curr_node_mutations = anc_node->mutations;

        if (curr_node_mutations.size() > 0) {
            size_t num_mutations = curr_node_mutations.size();
            for (size_t k = 0; k < num_mutations; k++) {
                // Get the position of this mutation
                int pos = std::stoi(curr_node_mutations[k].get_string().substr(
                    1, curr_node_mutations[k].get_string().size() - 2));
                // If a mutation at this position has not already been seen, add
                // to stack
                if (positions_seen.find(pos) == positions_seen.end()) {
                    mutation_stack.push(curr_node_mutations[k].get_string());
                    positions_seen.insert(pos);
                }
            }
        }
    }
    // Pop all the mutations from the stack and copy into a vector
    std::vector<std::string> mut_v{};
    mut_v.reserve(mutation_stack.size());

    while (mutation_stack.size()) {
        mut_v.push_back(mutation_stack.top());
        mutation_stack.pop();
    }
    return mut_v;
}

// Expected format for string date: "2022-08-14"
// Returns int vector of size 3 [year, month, day]
std::vector<std::string> format_date(std::string date) {
    int date_length = 10; // Only accepting dates in format, eg) 2022-11-09
    if (date.length() != date_length) {
        std::cout << "[ERROR]: Date incorrectly formatted: " << date << "\n";
        throw std::runtime_error("ERROR: format_date() function. Date not in "
                                 "correct format (date.length() = 10)");
    }
    std::string delimiter = "-";
    std::vector<std::string> year_month_day;
    int i = 0;
    std::string token;
    while ((i = date.find(delimiter)) != std::string::npos) {
        token = date.substr(0, i);
        year_month_day.push_back(token);
        date = date.substr(i + 1, date.length());
    }
    year_month_day.push_back(date);

    return year_month_day;
}

std::set<int> parse_informative_sites(std::string sites) {
    using char_tokenizer = boost::tokenizer<boost::char_separator<char>>;
    char_tokenizer tokenizer(sites, boost::char_separator<char>(","));

    std::set<int> positions;
    for (auto it = tokenizer.begin(); it != tokenizer.end(); ++it) {
        positions.insert(std::stoi(*it));
    }
    return positions;
}

template <typename T>
bool check_rmnm_site_helper(const T &vec, const T &rmnm_vec) {
    for (const auto &mut : rmnm_vec) {
        // If affected MNS not in vec of node mutations
        if (std::find(vec.begin(), vec.end(), mut) == vec.end()) {
            // Specific known RMNM not present at node
            return false;
        }
    }
    return true;
}

bool verify_mutations(int position_idx, std::vector<std::string> &mut_vec) {
    using mutations = const std::vector<std::string>;
    std::array<mutations, 18> known_rmnms = {
        mutations{"C21302T", "C21304A", "G21305A"},
        mutations{"C21304A", "G21305A"},
        mutations{"A28877T", "G28878C"},
        mutations{"G27382C", "A27383T", "T27384C"},
        mutations{"T26491C", "A26492T", "T26497C"},
        mutations{"G27758A", "T27760A"},
        mutations{"T27875C", "C27881T", "G27882", "C27883T"},
        mutations{"C27881T", "G27882C", "C27883T"},
        mutations{"C25162A", "C25163A"},
        mutations{"T21294A", "G21295A", "G21296A"},
        mutations{"A27038T", "T27039A", "C27040A"},
        mutations{"A21550C", "A21551T"},
        mutations{"C13423A", "C13424A"},
        mutations{"A4576T", "T4579A"},
        mutations{"A20284T", "T20285C"},
        mutations{"A507T", "T508C", "G509A"},
        mutations{"T28881A", "G28882A", "G28883C"},
        mutations{"T21994C", "T21995C"}};

    for (const auto &mut : known_rmnms[position_idx]) {
        if (std::find(mut_vec.begin(), mut_vec.end(), mut) == mut_vec.end()) {
            return false;
        }
    }
    return true;
}

bool check_rmns_positions(std::set<int> &informative_sites,
                          std::vector<std::string> &mut_vec) {
    if (informative_sites.empty()) {
        return false;
    }
    using positions = const std::set<int>;
    std::array<positions, 18> known_rmnms = {
        positions{21302, 21304, 21305},
        positions{21304, 21305},
        positions{28877, 28878},
        positions{27382, 27383, 27384},
        positions{26491, 26492, 26497},
        positions{27758, 27760},
        positions{27875, 27881, 27882, 27883},
        positions{27881, 27882, 27883},
        positions{25162, 25163},
        positions{21294, 21295, 21296},
        positions{27038, 27039, 27040},
        positions{21550, 21551},
        positions{13423, 13424},
        positions{4576, 4579},
        positions{20284, 20285},
        positions{507, 508, 509},
        positions{28881, 28882, 28883},
        positions{21994, 21995}};

    int rmnms_index = 0;
    // Check any of the known RMNMs found in set of node mutations
    for (const auto &sites : known_rmnms) {
        if (check_rmnm_site_helper(informative_sites, sites)) {
            if (verify_mutations(rmnms_index, mut_vec)) {
                return true;
            }
        }
        ++rmnms_index;
    }
    // Node does not contain any known RMNMs
    return false;
}

// Check if recombinant contains highly recurrent multi-nucleotide
// substitutions
bool check_rmnm_sites(const std::vector<std::string> &mut_vec) {
    if (mut_vec.empty()) {
        return false;
    }

    using mutations = const std::vector<std::string>;
    std::array<mutations, 15> known_rmnms = {
        mutations{"C21302T", "C21304A", "G21305A"},
        mutations{"C21304A", "G21305A"},
        mutations{"A28877T", "G28878C"},
        mutations{"G27382C", "A27383T", "T27384C"},
        mutations{"T26491C", "A26492T", "T26497C"},
        mutations{"G27758A", "T27760A"},
        mutations{"T27875C", "C27881T", "G27882", "C27883T"},
        mutations{"C27881T", "G27882C", "C27883T"},
        mutations{"C25162A", "C25163A"},
        mutations{"T21294A", "G21295A", "G21296A"},
        mutations{"A27038T", "T27039A", "C27040A"},
        mutations{"A21550C", "A21551T"},
        mutations{"C13423A", "C13424A"},
        mutations{"A4576T", "T4579A"},
        mutations{"A20284T", "T20285C"}};

    // Check any of the known RMNMs found in set of node mutations
    for (const auto &muts : known_rmnms) {
        if (check_rmnm_site_helper(mut_vec, muts)) {
            return true;
        }
    }
    // Node does not contain any known RMNMs
    return false;
}

//   Calculate elapsed days from given date to present date.
int elapsed_days(std::string tree_date, std::string inferred_recomb_date) {

    // Parse format of MAT tree date
    auto year_month_day = format_date(tree_date);
    int year = stoi(year_month_day[0]) - 1900; // Years since 1900
    int month = stoi(year_month_day[1]) - 1; // Months since January – [0, 11]
    int day = stoi(year_month_day[2]);       // Day of the month – [1, 31]

    struct std::tm x = {0, 0, 0, day, month, year};
    std::time_t date_1 = std::mktime(&x);

    // Parse format of recombinant node inferred date
    auto _year_month_day = format_date(inferred_recomb_date);
    int _year = stoi(_year_month_day[0]) - 1900; // Years since 1900
    int _month = stoi(_year_month_day[1]) - 1; // Months since January – [0, 11]
    int _day = stoi(_year_month_day[2]);       // Day of the month – [1, 31]

    struct std::tm y = {0, 0, 0, _day, _month, _year};
    std::time_t date_2 = std::mktime(&y);

    // Implicit conversion to int to get elapsed days only
    return std::difftime(date_1, date_2) / (60 * 60 * 24);
}

static void
write_descendants(const std::unordered_set<std::string> &internal_nodes,
                  MAT::Tree &T, std::ostream &descendants_outfile,
                  std::ostream &samples_outfile) {

    auto dfs_ordered_nodes = T.depth_first_expansion();
    std::vector<size_t> to_output_dfs_ids;
    to_output_dfs_ids.reserve(internal_nodes.size());

    for (const auto &node_name : internal_nodes) {
        auto node = T.get_node(node_name);
        to_output_dfs_ids.push_back(node->dfs_idx);
    }
    std::sort(to_output_dfs_ids.begin(), to_output_dfs_ids.end());
    for (auto node_id : to_output_dfs_ids) {
        // Get all node descendants, no max
        auto n = dfs_ordered_nodes[node_id];
        std::vector<std::string> descendants;
        descendants.reserve(n->dfs_end_idx - n->dfs_idx);
        for (size_t idx = n->dfs_idx; idx < n->dfs_end_idx; idx++) {
            if (dfs_ordered_nodes[idx]->is_leaf()) {
                descendants.push_back(dfs_ordered_nodes[idx]->identifier);
            }
        }
        auto descendants_csl = boost::algorithm::join(descendants, ", ");
        // 1st Column: node_id
        descendants_outfile << n->identifier << "\t";
        // 2nd column: comma separated list of descendants for node_id
        descendants_outfile << descendants_csl << "\t";
        // 3rd column: descendant count for node_id
        descendants_outfile << descendants.size() << "\n";
        samples_outfile << n->identifier << "\n";
    }
}

static void write_single_recomb(std::ofstream &outfile, const Recombinant &r,
                                Recomb_Samples &rs,
                                std::unordered_set<std::string> &internal_nodes,
                                MAT::Tree &T, float recomb_rank) {
    // Write recomb node clade and lineage
    // Lookup recomb node and check it exists in tree
    auto recomb = T.get_node(r.recomb_node_id);
    if (recomb == NULL) {
        std::cout << "3. Recomb node is NULL, not finding recomb node id: "
                  << r.recomb_node_id << "\n";
        exit(1);
    }
    // Lookup donor node and check it exists in tree
    auto donor = T.get_node(r.donor_node_id);
    if (donor == NULL) {
        std::cout << "Donor node is NULL, not finding donor node id"
                  << "\n";
        exit(1);
    }
    // Lookup acceptor node and check it exists in tree
    auto acceptor = T.get_node(r.acceptor_node_id);
    if (acceptor == NULL) {
        std::cout << "Acceptor node is NULL, not finding acceptor node id"
                  << "\n";
        exit(1);
    }

    outfile << r.recomb_node_id << "\t";

    // Write donor node id
    outfile << r.donor_node_id << "\t";

    // Write acceptor node id
    outfile << r.acceptor_node_id << "\t";

    // Write number of recombinant descendants
    outfile << T.get_num_leaves(recomb) << "\t";

    // Write number of donor descendants
    outfile << T.get_num_leaves(donor) << "\t";

    // Write number of acceptor descendants
    outfile << T.get_num_leaves(acceptor) << "\t";

    //  Write recombinant node breakpoint intervals
    outfile << std::get<0>(r.breakpoint_intervals) << "\t";
    outfile << std::get<1>(r.breakpoint_intervals) << "\t";

    internal_nodes.insert(r.recomb_node_id);
    internal_nodes.insert(r.donor_node_id);
    internal_nodes.insert(r.acceptor_node_id);
    // Get recomb clade (nextstrain) and lineage (pangolin designation)
    auto recomb_clade = T.get_clade_assignment(recomb, 0);
    auto recomb_lineage = T.get_clade_assignment(recomb, 1);
    outfile << recomb_clade << "\t";
    outfile << recomb_lineage << "\t";

    // Get donor clade (nextstrain) and lineage (pangolin designation)
    // get_clade_assignment(node, 0) returns nextstrain
    // get_clade_assignment(node, 1) returns pangolin
    auto donor_clade = T.get_clade_assignment(donor, 0);
    auto donor_lineage = T.get_clade_assignment(donor, 1);
    outfile << donor_clade << "\t";
    outfile << donor_lineage << "\t";

    // Get acceptor clade (nextstrain) and lineage (pangolin
    // designation)
    auto acceptor_clade = T.get_clade_assignment(acceptor, 0);
    auto acceptor_lineage = T.get_clade_assignment(acceptor, 1);
    outfile << acceptor_clade << "\t";
    outfile << acceptor_lineage << "\t";

    // Write recombinant node Chronumental inferred date
    outfile << r.inferred_date << "\t";

    // Write recombinant node ranking score (increasing order)
    outfile << recomb_rank << "\t";

    // Find representative sample with no (or minimal) number of
    // additional mutations compared to internal trio node
    auto recomb_rep_sample = find_representative_sample(T, r.recomb_node_id);

    // Only show representative descendant in table
    outfile << recomb_rep_sample << "\t";

    // Write informative sequence
    outfile << r.informative_seq << "\t";

    // Write 3SEQ (M, N, K) values
    outfile << r.mnk_3seq_values << "\t";

    // Write 3SEQ P-value
    outfile << r.p_value_3seq << "\t";

    outfile << r.original_parsimony << "\t";
    outfile << r.parsimony_improvement << "\t";
    outfile << r.informative_position << "\t";
    outfile << r.filter << "\t";

    outfile << rs.earliest_sequence << "\t";
    outfile << rs.latest_sequence << "\t";
    for (const auto &c : rs.circulating_countries) {
        outfile << c + ",";
    }
    outfile << "\t";
    for (const auto &s : rs.sampled_descendants) {
        outfile << s + ",";
    }
    outfile << "\n";
}

void write_recombination_list(
    MAT::Tree &T, std::vector<Recombinant> &recombinants,
    std::vector<Ranked_Recombinant> &ranked_recombs,
    std::unordered_map<std::string, Recomb_Samples> &recomb_samples,
    std::ofstream &outfile, std::ofstream &desc_outfile,
    std::vector<std::string> &header_list, boost::filesystem::path path) {

    // Add header for outfile
    for (std::vector<std::string>::iterator it = header_list.begin();
         it != header_list.end(); ++it) {
        if (it == std::prev(header_list.end())) {
            outfile << *it << "\n";
            break;
        }
        outfile << *it << "\t";
    }
    // Print number of internal nodes we have
    std::cout << "Ranked recomb size *3: " << ranked_recombs.size() * 3 << "\n";

    // Create samples output file with the name of all recombinant nodes
    std::string samples_file = "all_trio_nodes.txt";
    std::ofstream samples_outfile{path / samples_file};
    if (!samples_outfile) {
        throw std::runtime_error(
            "ERROR: Cannot create sample nodes output file.");
    }

    std::unordered_set<std::string> internal_nodes;
    internal_nodes.reserve(ranked_recombs.size() * 3);

    for (const auto &rr : ranked_recombs) {
        // Get the Recombinant node and write
        Recombinant r = recombinants[rr.id];
        Recomb_Samples rs = recomb_samples.at(r.recomb_node_id);
        write_single_recomb(outfile, r, rs, internal_nodes, T, rr.recomb_rank);
    }

    for (const auto &node_id : internal_nodes) {
        samples_outfile << node_id << "\n";
    }
    outfile.close();
    samples_outfile.close();
}

static Recombinant parse_recomb(text_parser &results) {
    auto recomb_id = std::string{results.get_value(0)};
    if (std::isdigit(recomb_id.at(0)) == 1) {
        recomb_id = "node_" + recomb_id;
    }
    // Create new recombinant node
    Recombinant r = Recombinant(recomb_id);

    // Get original parsimony and parsimony score improvement
    int org_parsimony = stoi(std::string{results.get_value(9)});
    int result_parsimony = stoi(std::string{results.get_value(11)});
    int parsimony_improvement = org_parsimony - result_parsimony;
    r.original_parsimony = org_parsimony;
    r.parsimony_improvement = parsimony_improvement;

    // Get breakpoint intervals for the recombinant node id
    std::tuple<std::string_view, std::string_view> bp(results.get_value(1),
                                                      results.get_value(2));
    r.breakpoint_intervals = bp;

    // Get donor/acceptor node ids
    auto donor_id = std::string{results.get_value(3)};
    if (std::isdigit(donor_id.at(0)) == 1) {
        donor_id = "node_" + donor_id;
    }

    auto acceptor_id = std::string{results.get_value(6)};
    if (std::isdigit(acceptor_id.at(0)) == 1) {
        acceptor_id = "node_" + acceptor_id;
    }
    // Record recomb/donor/acceptor node ids for ranking
    r.recomb_node_id = recomb_id;
    r.donor_node_id = donor_id;
    r.acceptor_node_id = acceptor_id;

    // Get informative site from filtration results file,
    // which is at column 16
    r.informative_seq = std::string{results.get_value(16)};
    // Get informative site positions from filtration results file,
    r.informative_position = std::string{results.get_value(15)};
    // Get 3SEQ M, N, K values from filtration results file
    std::string mnk_values = "(";
    mnk_values += std::string{results.get_value(17)} + ", ";
    mnk_values += std::string{results.get_value(18)} + ", ";
    mnk_values += std::string{results.get_value(19)} + ")";
    r.mnk_3seq_values = mnk_values;

    // Get 3SEQ P-value from filtration results file
    r.p_value_3seq = std::string{results.get_value(20)};

    // Get descendants from filtration results file
    r.descendants = std::string{results.get_value(14)};
    r.filter = std::string{results.get_value(21)};
    return r;
}

void get_recombination_info(
    MAT::Tree &T, std::string tree_date,
    std::unordered_map<std::string, std::string> &node_to_inferred_date,
    std::string filtered_recomb_file, std::ofstream &outfile,
    std::ofstream &desc_outfile, std::vector<std::string> &header_list,
    bool weight_by_samples,
    std::unordered_map<std::string, Descendant> &descendant_map,
    boost::filesystem::path path) {

    std::cout << "Opening results file: " << filtered_recomb_file << "\n";
    text_parser results(filtered_recomb_file);

    // Keep track of all trio node ids
    std::vector<std::string> trio_node_ids;

    // Keep track of all recomb_node_ids and their associated rank
    std::vector<Recombinant> recombinants;
    std::vector<Ranked_Recombinant> ranked_recombs;

    // Recomb node id: Recomb_Samples
    std::unordered_map<std::string, Recomb_Samples> recomb_samples;

    int num_rmnm = 0;

    // Get each detected recombinant node from filtration pipeline output
    for (; !results.done(); results.next_line()) {
        auto r = parse_recomb(results);

        std::set<int> positions =
            parse_informative_sites(r.informative_position);

        std::vector<std::string> recomb_mutations =
            get_node_mutations(T, r.recomb_node_id);

        if (check_rmns_positions(positions, recomb_mutations)) {
            r.filter += "RMNM,";
            num_rmnm++;
        }

        // Record recombinant node id
        trio_node_ids.push_back(r.recomb_node_id);
        // Record acceptor node id
        trio_node_ids.push_back(r.donor_node_id);
        // Record acceptor node id
        trio_node_ids.push_back(r.acceptor_node_id);

        // Get the recombinant node, and make sure id exists in tree
        auto recomb = T.get_node(r.recomb_node_id);
        if (recomb == NULL) {
            std::cout << "1. Recomb node is NULL, not finding recomb node id: "
                      << r.recomb_node_id << "\n";
            exit(1);
        }
        // Get number of descendants for recombinant node
        size_t recomb_num_descendants = T.get_num_leaves(recomb);

        // Parse dates only from Chronumental inferred dates dictionary
        std::string inferred_recomb_date =
            std::string{node_to_inferred_date.at(r.recomb_node_id)};
        int space_index = inferred_recomb_date.find(" ", 0);
        inferred_recomb_date = inferred_recomb_date.substr(0, space_index);
        r.inferred_date = inferred_recomb_date;

        // Calculate number of elapsed days since input tree date
        int days = elapsed_days(tree_date, inferred_recomb_date);

        Ranked_Recombinant rr = Ranked_Recombinant(recombinants.size());
        // Use default ranking method:
        // 2^-m(R) * sigma(2^-m(s)), for all s in S (set of samples)
        auto weight = [](const int days) {
            int weight = 0;
            for (int i = 30; i < days; i += 30) {
                ++weight;
            }
            return weight;
        };

        float recomb_rank = 0.0;
        float sequence_weight = 0.0;
        Recomb_Samples rs = Recomb_Samples(0.0);
        int min_days = INT_MAX;
        int max_days = 0;
        std::string earliest_desc;
        std::string latest_desc;
        std::string earliest_country;
        std::string latest_country;
        std::unordered_set<std::string> circulating_countries;

        if (weight_by_samples) {
            std::vector<std::string> desc_vec =
                get_node_descendants(T, r.recomb_node_id);
            rs.sampled_descendants =
                sample_descendants(T, r.recomb_node_id, desc_vec);

            for (const auto &d : desc_vec) {
                //  Check if descendant is not missing in metadata
                if (descendant_map.find(d) == descendant_map.end())
                    continue;
                Descendant desc = descendant_map.at(d);
                std::string sample_date = desc.date;
                circulating_countries.insert(desc.country);
                //  Calculate number of months since sample was first
                //  sequenced (0-index)
                // Only accepting dates in format, eg) 2022-11-09
                if (sample_date.length() != 10)
                    continue;
                int _days = elapsed_days(tree_date, sample_date);
                if (_days > max_days) {
                    max_days = _days;
                    earliest_desc = d;
                    earliest_country = desc.country;
                }
                if (_days < min_days) {
                    min_days = _days;
                    latest_desc = d;
                    latest_country = desc.country;
                }
                sequence_weight += pow(2, -weight(_days));
            }
            rs.sequence_weight = sequence_weight;
            rs.earliest_sequence = earliest_desc;
            rs.earliest_country = earliest_country;
            rs.latest_sequence = latest_desc;
            rs.latest_country = latest_country;
            rs.circulating_countries = circulating_countries;
            recomb_samples.insert({r.recomb_node_id, rs});

            // Generate recombinant ranking score
            recomb_rank =
                default_recombinant_rank(weight(days), sequence_weight);
        }
        // Use alternative ranking method, weight by recombinant recency
        else {
            // TODO: NOTE, alternate ranking method experimental
            // Generate recombinant ranking score
            recomb_rank = alternate_recombinant_rank(
                days, recomb_num_descendants, weight(days));
        }

        r.recomb_rank = recomb_rank;
        rr.recomb_rank = recomb_rank;
        // Add recombination information to collection of detected
        // recombinants
        recombinants.push_back(r);

        // Keep track of rank score for each detected recombinant
        ranked_recombs.push_back(rr);
    }

    // Sort the recombinants by max score
    std::sort(ranked_recombs.begin(), ranked_recombs.end(),
              [](const Ranked_Recombinant &a, const Ranked_Recombinant &b) {
                  return a.recomb_rank > b.recomb_rank;
              });

    // Write all final recombinants to output file, in ranked order
    write_recombination_list(T, recombinants, ranked_recombs, recomb_samples,
                             outfile, desc_outfile, header_list, path);
}

void get_recombination_info_using_descendants(
    MAT::Tree &T, std::string tree_date, std::string filtered_recomb_file,
    std::unordered_map<std::string, std::string> &descendant_to_date,
    std::ofstream &outfile, std::ofstream &desc_outfile,
    std::vector<std::string> &header_list, bool weight_by_samples,
    boost::filesystem::path path) {

    std::cout << "Opening results file: " << filtered_recomb_file << "\n";
    text_parser results(filtered_recomb_file);

    // Keep track of all recomb_node_ids and their associated rank
    std::vector<Recombinant> recombinants;
    std::vector<Ranked_Recombinant> ranked_recombs;

    // Recomb node id: Recomb_Samples
    std::unordered_map<std::string, Recomb_Samples> recomb_samples;

    // Get each detected recombinant node from filtration pipeline output
    for (; !results.done(); results.next_line()) {

        Recombinant r = parse_recomb(results);
        auto recomb = T.get_node(r.recomb_node_id);
        if (recomb == NULL) {
            std::cout << "2. Recomb node is NULL, not finding recomb node id: "
                      << r.recomb_node_id << "\n";
            exit(1);
        }
        // Get number of descendants for recombinant node
        size_t recomb_num_descendants = T.get_num_leaves(recomb);

        // Get all descendants for recombinant node
        auto descendants_vec = T.get_leaves(r.recomb_node_id);
        if (descendants_vec.size() == 0) {
            std::cout << "RECOMB NODE ID with no descendants"
                      << r.recomb_node_id << "\n";
            throw std::runtime_error(
                "ERROR: Recombinant node doesn't have any descendants.");
        }
        // Use earliest date of recomb node descendants (earliest_days) as
        // proxy for inferred recomb note date
        int earliest_days = 0;
        std::string earliest_descendant = "";
        for (auto node : descendants_vec) {
            const std::string &n = node->identifier;
            if (descendant_to_date[n].size() != 10) {
                continue;
            }
            int desc_days =
                elapsed_days(tree_date, std::string{descendant_to_date[n]});
            //  Ties don't matter, we just want earliest date
            if (desc_days > earliest_days) {
                earliest_descendant = node->identifier;
                earliest_days = desc_days;
            }
        }
        // Weight sequence by recency
        auto weight = [](const int days) {
            int weight = 0;
            for (int i = 30; i < days; i += 30) {
                ++weight;
            }
            return weight;
        };

        Ranked_Recombinant rr = Ranked_Recombinant(recombinants.size());
        // Generate recombinant ranking score, using earliest date from set
        // of recomb node descendants
        auto recomb_rank = alternate_recombinant_rank(
            earliest_days, recomb_num_descendants, weight(earliest_days));

        if (recomb_rank == 0.0) {
            // Move to next recombinant, incomplete date information for
            // this recombinant node, for all node descendants in metadata
            continue;
        }
        r.recomb_rank = recomb_rank;
        rr.recomb_rank = recomb_rank;
        // Add recombination information to collection of detected
        // recombinants
        recombinants.push_back(r);

        // Keep track of rank score for each detected recombinant
        ranked_recombs.push_back(rr);
    }
    // Sort the recombinants by max score
    std::sort(ranked_recombs.begin(), ranked_recombs.end(),
              [](const Ranked_Recombinant &a, const Ranked_Recombinant &b) {
                  return a.recomb_rank > b.recomb_rank;
              });

    // Write all final recombinants to output file, in ranked order
    write_recombination_list(T, recombinants, ranked_recombs, recomb_samples,
                             outfile, desc_outfile, header_list, path);
}

// Same preorder traversal as Chronumental performs to map
// from ripples node ids -> Chronumental node ids
void chron_id_mapping(MAT::Tree &T,
                      std::unordered_map<std::string, std::string> &id_map) {
    MAT::Node *root = T.root;
    std::stack<MAT::Node *> s;
    std::vector<MAT::Node *> preorder;
    if (root == NULL) {
        std::cout << "ERROR: Empty tree!"
                  << "\n";
        exit(1);
    }
    s.push(root);
    while (!s.empty()) {
        auto node = s.top();
        s.pop();
        preorder.push_back(node);
        for (auto &child : node->children) {
            s.push(child);
        }
    }
    auto dfs = T.depth_first_expansion();
    if (dfs.size() != preorder.size()) {
        std::cout << "ERROR: Traversal sizes not matching."
                  << "\n";
        exit(1);
    }
    id_map.reserve(dfs.size());
    for (size_t i = 0; i < dfs.size(); ++i) {
        id_map.insert({dfs[i]->identifier, preorder[i]->identifier});
    }
}

//  Extract two columns from a TSV file to act as dictionary,
//  one as key, the other as value
void tsv_to_dict(std::string tsv_file,
                 std::unordered_map<std::string, std::string> &map, int key_col,
                 int val_col, bool header) {
    text_parser file_handle(tsv_file);

    // If file has header, skip over first header line
    // Assuming header is just a single first line in TSV file
    if (header == true) {
        file_handle.next_line();
    }

    for (; !file_handle.done(); file_handle.next_line()) {
        std::string_view key = file_handle.get_value(key_col);
        std::string_view value = file_handle.get_value(val_col);
        map.insert({std::string(key), std::string(value)});
    }
}

void parse_metadata(std::string &tsv_file,
                    std::unordered_map<std::string, Descendant> &map,
                    int key_col, int date_col, int country_col, bool header) {
    text_parser file_handle(tsv_file);

    // If file has header, skip over first header line
    // Assuming header is just a single first line in TSV file
    if (header) {
        file_handle.next_line();
    }

    for (; !file_handle.done(); file_handle.next_line()) {
        std::string desc_name = std::string{file_handle.get_value(key_col)};
        std::string date = std::string{file_handle.get_value(date_col)};
        std::string country = std::string{file_handle.get_value(country_col)};
        Descendant d = Descendant();
        d.date = date;
        d.country = country;
        map.insert({desc_name, d});
    }
}

// Find a sample that is representative of the given internal node,
// meaning that it is a descendant of this internal node and shares no, or
// minimal additional mutations with the internal node
std::string find_representative_sample(MAT::Tree &T,
                                       std::string internal_node_id) {

    // Get internal node
    MAT::Node *internal_node = T.get_node(internal_node_id);

    // Get all the descendant nodes for internal node
    std::vector<MAT::Node *> desc_vec;
    desc_vec = T.get_leaves(internal_node_id);

    std::vector<RepresentativeSample> rep_samples;
    // Go through all of the internal_node descendants and find a sample
    // with no or fewest additional mutations
    for (auto node : desc_vec) {
        RepresentativeSample r = RepresentativeSample(node->identifier);
        r.num_novel_mutations = node->mutations.size();
        rep_samples.push_back(r);
    }
    //  Sort representative samples to see which contains the fewest
    //  additional mutations wrt given internal node
    std::sort(rep_samples.begin(), rep_samples.end(),
              [](const RepresentativeSample &a, const RepresentativeSample &b) {
                  return a.num_novel_mutations < b.num_novel_mutations;
              });

    // Return the sample with fewest additional mutations
    return rep_samples[0].node_id;
}

std::vector<std::string>
sample_descendants(MAT::Tree &T, std::string recomb_node_id,
                   std::vector<std::string> &desc_vec) {

    std::shuffle(desc_vec.begin(), desc_vec.end(),
                 std::default_random_engine(0));

    // Select 10 samples to use for UShER.bio integration on RIVET frontend
    std::vector<std::string> sampled_desc;

    // TODO: Sample at least 2 with LCA
    std::sample(desc_vec.begin(), desc_vec.end(),
                std::back_inserter(sampled_desc), 10,
                std::mt19937{std::random_device{}()});
    return sampled_desc;
}

std::vector<std::string>
get_node_descendants(MAT::Tree &T, const std::string &internal_node_id) {
    std::vector<std::string> descendants;
    auto node = T.get_node(internal_node_id);
    descendants.reserve(T.get_num_leaves(node));

    // Get internal node
    MAT::Node *internal_node = T.get_node(internal_node_id);

    // Get all the descendant nodes for internal node
    std::vector<MAT::Node *> desc_vec;
    desc_vec = T.get_leaves(internal_node_id);
    // Get all descendants node ids
    for (const auto &d : desc_vec) {
        descendants.push_back(d->identifier);
    }
    return descendants;
}

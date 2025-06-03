#include "get_recomb_info.hpp"
#include <boost/filesystem.hpp>
#include <boost/program_options.hpp>
#include <fstream>
#include <iostream>
#include <string>

namespace po = boost::program_options;

int main(int argc, char **argv) {
    uint32_t num_cores = tbb::task_scheduler_init::default_num_threads();
    uint32_t num_threads;
    std::string num_threads_message = "Number of threads to use when possible "
                                      "[DEFAULT uses all available cores, " +
                                      std::to_string(num_cores) +
                                      " detected on this machine]";

    po::options_description desc("optimize options");
    desc.add_options()("input-mat,i", po::value<std::string>()->required(),
                       "Input mutation-annotated tree file [REQUIRED].")(
        "filtered-recombinants,f", po::value<std::string>()->required(),
        "Input file containing filtered recombinants from filtration "
        "pipeline [REQUIRED].")(
        "date,d", po::value<std::string>()->required(),
        "MAT tree date (format: year-month-day, eg. 2022-08-14) [REQUIRED].")(
        "chronumental-dates,c", po::value<std::string>()->default_value(""),
        "If using Chronumental, give output inferred dates file from running "
        "Chronumental. Otherwise earliest date from recombinant node "
        "descendants will be used. ")("metadata,m",
                                      po::value<std::string>()->required(),
                                      "MAT metadata file which contains dates "
                                      "for all descendants. [REQUIRED]")(
        "weight,w", po::bool_switch()->default_value(false),
        "Only use recency of recombinant node, not samples, when calculating "
        "recombinant ranking")(
        "final-recombinants,r", po::value<std::string>()->required(),
        "Output file containing filtered recombinants with all "
        "information needed for RIVET[REQUIRED].")(
        "output-directiory,o", po::value<std::string>()->required(),
        "Output directory to write all output files to[REQUIRED]. ")(
        "threads,T",
        po::value<uint32_t>(&num_threads)->default_value(num_cores),
        num_threads_message.c_str());

    po::options_description all_options;
    all_options.add(desc);
    po::positional_options_description p;
    po::variables_map vm;
    try {
        po::store(po::command_line_parser(argc, argv)
                      .options(all_options)
                      .positional(p)
                      .run(),
                  vm);
        po::notify(vm);
    } catch (std::exception &e) {
        std::cerr << desc << std::endl;
        if (vm.count("help"))
            exit(0);
        else
            exit(1);
    }

    std::string input_mat_filename = vm["input-mat"].as<std::string>();
    std::string filtered_recomb_file =
        vm["filtered-recombinants"].as<std::string>();
    std::string final_recomb_file = vm["final-recombinants"].as<std::string>();
    std::string tree_date = vm["date"].as<std::string>();
    std::string chron_dates_file = vm["chronumental-dates"].as<std::string>();
    std::string metadata_file = vm["metadata"].as<std::string>();
    std::string output_dir = vm["output-directiory"].as<std::string>();
    bool weight_by_samples = vm["weight"].as<bool>();

    // Number of worker threads to use
    tbb::task_scheduler_init init(num_threads);

    if (weight_by_samples) {
        std::cout << "Using default ranking method."
                  << "\n";
    } else {
        std::cout << "Alternative ranking method selected, recency of samples "
                     "not included in ranking recency weight."
                  << "\n";
    }

    // Load input MAT and uncondense tree
    printf("Loading input MAT file\n");
    MAT::Tree T = MAT::load_mutation_annotated_tree(input_mat_filename);
    T.uncondense_leaves();

    // Get number of leaves in the tree
    auto num_leaves = T.get_num_leaves();
    std::cout << "Tree contains: " << num_leaves << " leaves."
              << "\n";

    // Create output file directory
    boost::filesystem::path path(output_dir);
    // Create new recombinant output file
    std::ofstream outfile{final_recomb_file};
    if (!outfile) {
        throw std::runtime_error(
            "ERROR: Cannot create final recombination output file.");
    }
    // Create new descendants output file
    std::ofstream desc_outfile(path / "samples_descendants.txt.xz",
                               std::ios::out | std::ios::binary);
    if (!desc_outfile) {
        throw std::runtime_error(
            "ERROR: Cannot create sample descendants output file. ");
    }

    // Output file columns
    std::vector<std::string> header_list = {"Recombinant Node ID",
                                            "Donor Node ID",
                                            "Acceptor Node ID",
										    "Recombinant Number of Descendants",
											"Donor Number of Descendants",
											"Acceptor Number of Descendants",
                                            "Breakpoint 1 Interval",
                                            "Breakpoint 2 Interval",
                                            "Recombinant Clade",
                                            "Recombinant Lineage",
                                            "Donor Clade",
                                            "Donor Lineage",
                                            "Acceptor Clade",
                                            "Acceptor Lineage",
                                            "Chronumental-inferred origin date",
                                            "Recombinant Ranking Score",
                                            "Representative Descendant",
                                            "Informative Site Sequence",
                                            "3SEQ (M, N, K)",
                                            "3SEQ P-Value",
                                            "Original Parsimony Score",
                                            "Parsimony Score Improvement",
                                            "Informative Site Positions",
                                            "Quality Control (QC) Flags",
                                            "Earliest sequence",
                                            "Most recent sequence",
                                            "Countries circulating",
                                            "Sampled Descendants"};

    std::vector<std::string> trio_node_ids;

    // If Chronumental inferred internal dates file provided, use this method
    if (chron_dates_file != "") {
        std::cout << "Chronumental inferred dates file given: "
                  << chron_dates_file << "\n";
        std::cout << "Using Chronumental for recombinant node ranking."
                  << "\n";

        std::cout << "Loading Chronumental inferred dates file."
                  << "\n";

        // Load inferred dates for internal nodes from Chronumental output
        std::unordered_map<std::string, std::string> node_to_inferred_date;
        node_to_inferred_date.reserve(num_leaves);
        tsv_to_dict(chron_dates_file, node_to_inferred_date, 0, 1, true);

        std::cout << "Loading input metadata file."
                  << "\n";
        // Load MAT metadata into dictionary to get dates for descendants

        // Sample name : Descendant struct (containing extra data about desc)
        std::unordered_map<std::string, Descendant> descendants_map;
        descendants_map.reserve(num_leaves);
        parse_metadata(metadata_file, descendants_map, 0, 2, 3, true);

        std::cout
            << "Fetching information about each recombinant and begin ranking."
            << "\n";
        // NOTE: Chronumental will preserve internal node id naming using Newick
        // generated from  matUtils extract. Get information for each column for
        // all filtered recombinants, including rank score, and output to
        // outfile.  Return a vector of string node ids for all trio nodes
        // (recomb, donor, acceptor)
        // NOW
        get_recombination_info(T, tree_date, node_to_inferred_date,
                               filtered_recomb_file, outfile, desc_outfile,
                               header_list, weight_by_samples, descendants_map,
                               path);
    }
    // If no Chronumental inferred dates file given, use alternate method
    // of chosing recombinant node descendant with earliest date
    else {
        // If Chronumental not used, check to make sure metadata input file
        // given
        if (metadata_file == "") {
            throw std::runtime_error(
                "ERROR: If not using Chronumental (-c flag), then metadata "
                "file must be provided through --metadata (-m) flag");
        }
        if (metadata_file.substr(metadata_file.find_last_of(".") + 1) == "gz") {
            throw std::runtime_error("Input metadata file must be unzipped and "
                                     "provided through --metadata (-m) flag");
        }
        std::cout << "Using alternate earliest descendant date method for "
                     "recombinant node ranking."
                  << "\n";

        // Load MAT metadata into dictionary to get dates for descendants
        std::unordered_map<std::string, std::string> descendant_to_date;
        descendant_to_date.reserve(num_leaves);
        tsv_to_dict(metadata_file, descendant_to_date, 0, 2, true);

        // Get all recombinant node information, rank recombinants and write to
        // given output file, return vector of string node_ids for all trio
        // nodes (recomb, donor, acceptor)
        get_recombination_info_using_descendants(
            T, tree_date, filtered_recomb_file, descendant_to_date, outfile,
            desc_outfile, header_list, weight_by_samples, path);
    }
    std::cout << "Final recombination results written to:  "
              << final_recomb_file << "\n";
    outfile.close();
    desc_outfile.close();
    return 0;
}

// ============================================================================
// FastRegrid CLI executable — main() entry point for IMOGEN/LPJG regridding
//
// Authored at block 8.2.5 (2026-05-26 session 11 day 2) per the wiring plan at
// _chat_artifacts/b8_2_5_switchable_regrid_2026-05-26/B8_2_5_wiring_plan.md.
//
// Forked from ../version_B/LPJG-IMOGEN-COUPLED-MODEL-FRAMEWORK/FastRegrid/FastRegrid/
// FastRegrid.cpp + Linux-adapted: (a) lowercase filenames (Linux case-sensitivity);
// (b) `file_types` extended from 3 to 10 climate variables (T_anom, P_anom,
// SW_anom, DTEMP_anom, Rh_anom, W_anom, Tmin_anom, Tmax_anom, WET, CO2);
// (c) hardcoded Windows paths in main() replaced with CLI-arg parsing.
//
// Usage:
//   IMOGEN year-by-year mode (regrid 5-SSP engine output libraries):
//     fastregrid_example --mode imogen \
//       --input <input-base-dir>  \
//       --output <output-base-dir> \
//       --target-gridlist <gridlist.txt> \
//       --method {NN|IDW} \
//       --first-year <YYYY> --last-year <YYYY>
//       [--max-points N] [--radius KM] [--power P] [--verbose]
//
//   LPJ-GUESS grid-by-time mode (regrid LPJG ecosystem output files):
//     fastregrid_example --mode lpjg \
//       --input <input.out> --output <output.out> \
//       --target-gridlist <gridlist.txt> \
//       --method {NN|IDW} \
//       --first-year <YYYY> --last-year <YYYY>
//
// \author Daniel Bampoh, 2026-05-26 (session 11 day 2 block 8.2.5 Phase C)
// ============================================================================

#include "regrid.h"
#include <iostream>
#include <filesystem>
#include <string>
#include <vector>
#include <cstring>

// Process IMOGEN year-by-year data (per-year directories under input_base
// containing per-variable .dat files; output_base mirrors structure)
void process_imogen(const regrid::Regridder& regridder,
    const std::vector<regrid::GridPoint>& target_grid,
    const std::string& input_base,
    const std::string& output_base,
    int first_year,
    int last_year,
    const std::vector<std::string>& file_types) {
    std::filesystem::create_directories(output_base);
    for (int year = first_year; year <= last_year; ++year) {
        std::string year_dir = input_base + "/" + std::to_string(year);
        std::string out_year_dir = output_base + "/" + std::to_string(year);
        if (!std::filesystem::exists(year_dir)) continue;

        std::filesystem::create_directory(out_year_dir);
        for (const auto& file_type : file_types) {
            std::string in_file = year_dir + "/" + file_type;
            std::string out_file = out_year_dir + "/" + file_type;
            if (!std::filesystem::exists(in_file)) continue;

            std::filesystem::create_directories(std::filesystem::path(out_file).parent_path());
            regridder.regrid_file(in_file, out_file, target_grid, year);
            std::cout << "Processed IMOGEN file: " << in_file << "\n";
        }
    }
}

// Process LPJ-GUESS grid-by-time data (single .out file with all years; output
// mirrors structure)
void process_lpjg(const regrid::Regridder& regridder,
    const std::vector<regrid::GridPoint>& target_grid,
    const std::string& input_file,
    const std::string& output_file,
    int first_year,
    int last_year) {
    std::filesystem::create_directories(std::filesystem::path(output_file).parent_path());
    regridder.regrid_file(input_file, output_file, target_grid, 0, first_year, last_year);
    std::cout << "Processed LPJ-GUESS file: " << input_file << "\n";
}

void print_usage(const char* argv0) {
    std::cerr << "Usage:\n";
    std::cerr << "  IMOGEN year-by-year mode (regrid engine output libraries):\n";
    std::cerr << "    " << argv0 << " --mode imogen \\\n";
    std::cerr << "      --input <input-base-dir>  --output <output-base-dir> \\\n";
    std::cerr << "      --target-gridlist <gridlist.txt> \\\n";
    std::cerr << "      --method {NN|IDW} \\\n";
    std::cerr << "      --first-year <YYYY> --last-year <YYYY>\n";
    std::cerr << "      [--max-points N] [--radius KM] [--power P] [--verbose]\n\n";
    std::cerr << "  LPJ-GUESS grid-by-time mode (regrid LPJG ecosystem output files):\n";
    std::cerr << "    " << argv0 << " --mode lpjg \\\n";
    std::cerr << "      --input <input.out> --output <output.out> \\\n";
    std::cerr << "      --target-gridlist <gridlist.txt> \\\n";
    std::cerr << "      --method {NN|IDW} \\\n";
    std::cerr << "      --first-year <YYYY> --last-year <YYYY>\n";
}

int main(int argc, char* argv[]) {
    std::string mode = "imogen";
    std::string input;
    std::string output;
    std::string gridlist;
    std::string method = "IDW";  // default per FastRegrid version_B
    int first_year = 1900;
    int last_year = 2100;
    int max_points = 5;
    double radius = 100.0;
    double power = 2.0;
    bool verbose = false;

    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    // [Block 8.2.5 (2026-05-26): CLI-arg parsing replaces version_B's
    //  hardcoded Windows paths in main() (C:/GitHub/LPJG-IMOGEN-COUPLED-MODEL-
    //  FRAMEWORK/...). Per the wiring plan §1.2 Phase C source-edit. - DKB]
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--help") == 0 || std::strcmp(argv[i], "-h") == 0) {
            print_usage(argv[0]);
            return 0;
        }
        if (std::strcmp(argv[i], "--mode") == 0 && i + 1 < argc) {
            mode = argv[++i];
        } else if (std::strcmp(argv[i], "--input") == 0 && i + 1 < argc) {
            input = argv[++i];
        } else if (std::strcmp(argv[i], "--output") == 0 && i + 1 < argc) {
            output = argv[++i];
        } else if (std::strcmp(argv[i], "--target-gridlist") == 0 && i + 1 < argc) {
            gridlist = argv[++i];
        } else if (std::strcmp(argv[i], "--method") == 0 && i + 1 < argc) {
            method = argv[++i];
        } else if (std::strcmp(argv[i], "--first-year") == 0 && i + 1 < argc) {
            first_year = std::stoi(argv[++i]);
        } else if (std::strcmp(argv[i], "--last-year") == 0 && i + 1 < argc) {
            last_year = std::stoi(argv[++i]);
        } else if (std::strcmp(argv[i], "--max-points") == 0 && i + 1 < argc) {
            max_points = std::stoi(argv[++i]);
        } else if (std::strcmp(argv[i], "--radius") == 0 && i + 1 < argc) {
            radius = std::stod(argv[++i]);
        } else if (std::strcmp(argv[i], "--power") == 0 && i + 1 < argc) {
            power = std::stod(argv[++i]);
        } else if (std::strcmp(argv[i], "--verbose") == 0) {
            verbose = true;
        } else {
            std::cerr << "ERROR: Unknown argument: " << argv[i] << "\n\n";
            print_usage(argv[0]);
            return 1;
        }
    }

    if (input.empty() || output.empty() || gridlist.empty()) {
        std::cerr << "ERROR: --input, --output, and --target-gridlist are required\n\n";
        print_usage(argv[0]);
        return 1;
    }

    // Configure regridder
    regrid::RegridConfig config;
    if (method == "NN" || method == "nn" || method == "NEAREST_NEIGHBOR") {
        config.interp_method = regrid::InterpolationMethod::NEAREST_NEIGHBOR;
    } else {
        config.interp_method = regrid::InterpolationMethod::INVERSE_DISTANCE_WEIGHTED;
    }
    config.distance_metric = regrid::DistanceMetric::HAVERSINE;
    config.radius = radius;
    config.power = power;
    config.max_points = max_points;
    config.adjust_longitude = true;
    config.precision = 5;
    config.verbose = verbose;
    config.write_mappings = false;  // off by default; can be enabled per-run via flag if needed

    if (mode == "imogen") {
        config.data_layout = regrid::DataLayout::YEAR_BY_YEAR;
    } else if (mode == "lpjg") {
        config.data_layout = regrid::DataLayout::GRID_BY_TIME;
    } else {
        std::cerr << "ERROR: --mode must be 'imogen' or 'lpjg'\n";
        return 1;
    }

    regrid::Regridder regridder(config);
    auto target_grid = regridder.read_grid_list(gridlist);
    std::cout << "Loaded target gridlist: " << gridlist << " (" << target_grid.size() << " points)\n";
    std::cout << "Interpolation method: " << (config.interp_method == regrid::InterpolationMethod::NEAREST_NEIGHBOR ? "NEAREST_NEIGHBOR" : "INVERSE_DISTANCE_WEIGHTED") << "\n";

    // [Block 8.2.5 (2026-05-26): file_types extended from version_B's 3 climate
    //  variables {T_anom, P_anom, SW_anom} to the 9 per-cell climate variables
    //  produced by both the Fortran imogen_lpjg.f engine (δ-B at 3698-grid) and
    //  the C++ port forks/trunk_r13078/modules/climatemodel.cpp::RUN_IMOGEN_
    //  ENGINE() (δ-B-variant at 1631-grid post-block-8.2.4). Per the wiring
    //  plan §1.2 Phase C 10-var extension; Phase C canary surfaced Rule #9
    //  datapoint that CO2.dat is structurally DIFFERENT from the 9 per-cell
    //  climate fields (CO2.dat is a single-line atmospheric concentration
    //  time-series 'YEAR CO2_PPMV ...' not regriddable spatially); CO2.dat
    //  is to be cp'd as-is by the scripts/run_fastregrid.sh wrapper (NOT
    //  passed through this regrid loop which assumes per-cell fields).
    //  Same applies to dtemp_o.dat (ocean temperature timeseries) +
    //  fa_ocean.dat (1D ocean state) which are similarly not per-cell-field-
    //  structured (those weren't in version_B's file_types either).
    //  - DKB block 8.2.5]
    std::vector<std::string> file_types = {
        "T_anom.dat", "P_anom.dat", "SW_anom.dat", "DTEMP_anom.dat",
        "Rh_anom.dat", "W_anom.dat", "Tmin_anom.dat", "Tmax_anom.dat",
        "WET.dat"
    };

    if (mode == "imogen") {
        // Precompute mappings using first-year T_anom.dat as the source-grid sample
        std::string sample_file = input + "/" + std::to_string(first_year) + "/T_anom.dat";
        if (!std::filesystem::exists(sample_file)) {
            std::cerr << "ERROR: sample file for precompute_mappings does not exist: " << sample_file << "\n";
            return 1;
        }
        regridder.precompute_mappings(sample_file, target_grid);
        process_imogen(regridder, target_grid, input, output, first_year, last_year, file_types);
    } else {
        if (!std::filesystem::exists(input)) {
            std::cerr << "ERROR: input file does not exist: " << input << "\n";
            return 1;
        }
        regridder.precompute_mappings(input, target_grid);
        process_lpjg(regridder, target_grid, input, output, first_year, last_year);
    }

    std::cout << "Regridding completed successfully.\n";
    return 0;
}
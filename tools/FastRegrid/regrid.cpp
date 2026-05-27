#define _USE_MATH_DEFINES
#include "regrid.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <cmath>
#include <algorithm>
#include <iomanip>
#include <filesystem>
#include <limits>

namespace regrid {

    constexpr double EARTH_RADIUS_KM = 6371.0;

    // [Block 8.2.5 Phase E δ-B-variant Rule #9 datapoint #33: auto-detect whether
    //  line 1 of an input file is a header (legacy assumption) or actual numeric
    //  data (our IMOGEN engine outputs from both Fortran imogen_lpjg.f and the
    //  C++ port climatemodel.cpp::RUN_IMOGEN_ENGINE() emit pure data with NO
    //  header). Pre-fix, FastRegrid silently treated line 1 as header in both
    //  precompute_mappings (skipped 1 source cell from the regrid pool) and
    //  regrid_file (wrote a "ghost" header row reformatting the source's first
    //  data row into the output). Returns true iff line is parseable as
    //  >=3 whitespace-separated numeric tokens with NO trailing non-numeric
    //  tokens — i.e., a true data row of shape <lon> <lat> <val>...
    //  Header-bearing inputs (e.g., "longitude latitude val1 val2") still
    //  parse as has-header (the first token is non-numeric). - DKB block 8.2.5]
    static bool is_numeric_data_line(const std::string& line) {
        if (line.empty()) return false;
        std::istringstream iss(line);
        double v;
        int count = 0;
        while (iss >> v) ++count;
        return count >= 3 && iss.eof();
    }

    Regridder::Regridder(const RegridConfig& config) : config_(config) {}

    std::vector<GridPoint> Regridder::read_grid_list(const std::string& filename) const {
        if (config_.verbose) std::cout << "Reading grid list: " << filename << std::endl;
        std::vector<GridPoint> grid_list;
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Error: Unable to open grid file: " << filename << std::endl;
            return grid_list;
        }
        std::string line;
        while (std::getline(file, line)) {
            std::istringstream iss(line);
            GridPoint gp;
            if (!(iss >> gp.longitude >> gp.latitude)) {
                if (config_.verbose) std::cerr << "Warning: Skipping malformed line in grid file: " << line << std::endl;
                continue;
            }
            grid_list.push_back(gp);
        }
        file.close();
        if (config_.verbose) std::cout << "Read " << grid_list.size() << " grid points.\n";
        return grid_list;
    }

    double Regridder::compute_distance(const GridPoint& p1, const GridPoint& p2) const {
        double lon1 = adjust_lon(p1.longitude);
        double lat1 = p1.latitude;
        double lon2 = adjust_lon(p2.longitude);
        double lat2 = p2.latitude;

        if (config_.distance_metric == DistanceMetric::EUCLIDEAN) {
            return std::sqrt(std::pow(lon1 - lon2, 2) + std::pow(lat1 - lat2, 2));
        }
        else {
            double dlat = (lat2 - lat1) * M_PI / 180.0;
            double dlon = (lon2 - lon1) * M_PI / 180.0;
            double a = std::pow(std::sin(dlat / 2), 2) +
                std::cos(lat1 * M_PI / 180.0) * std::cos(lat2 * M_PI / 180.0) * std::pow(std::sin(dlon / 2), 2);
            double c = 2 * std::atan2(std::sqrt(a), std::sqrt(1 - a));
            return EARTH_RADIUS_KM * c;
        }
    }

    void Regridder::precompute_mappings(const std::string& source_sample_file,
        const std::vector<GridPoint>& target_grid) {
        if (config_.verbose) std::cout << "Precomputing mappings using: " << source_sample_file << std::endl;
        std::ifstream sample_file(source_sample_file);
        if (!sample_file.is_open()) {
            std::cerr << "Error: Unable to open sample file: " << source_sample_file << std::endl;
            return;
        }

        std::vector<SpatialData> sample_data;
        std::string line;
        // Rule #9 #33 fix: auto-detect line 1 = header vs data; rewind to re-read if data
        std::streampos pos_before_line1 = sample_file.tellg();
        std::getline(sample_file, line);
        if (is_numeric_data_line(line)) {
            sample_file.clear();
            sample_file.seekg(pos_before_line1);
        }
        // else: line 1 was a true header; remain consumed (legacy behavior)
        while (std::getline(sample_file, line)) {
            std::istringstream iss(line);
            SpatialData sd;
            if (config_.data_layout == DataLayout::YEAR_BY_YEAR) {
                if (!(iss >> sd.gridPoint.longitude >> sd.gridPoint.latitude)) {
                    if (config_.verbose) std::cerr << "Warning: Skipping malformed line in sample file: " << line << std::endl;
                    continue;
                }
                sd.time_step = 0;
            }
            else {
                if (!(iss >> sd.gridPoint.longitude >> sd.gridPoint.latitude >> sd.time_step)) {
                    if (config_.verbose) std::cerr << "Warning: Skipping malformed line in sample file: " << line << std::endl;
                    continue;
                }
            }
            double value;
            while (iss >> value) sd.values.push_back(value);
            sample_data.push_back(sd);
        }
        sample_file.close();

        // Extract unique grid points
        std::vector<GridPoint> source_grid;
        std::map<std::pair<double, double>, int> unique_points;
        for (int i = 0; i < sample_data.size(); ++i) {
            auto key = std::make_pair(sample_data[i].gridPoint.longitude, sample_data[i].gridPoint.latitude);
            if (unique_points.find(key) == unique_points.end()) {
                unique_points[key] = i;
                source_grid.push_back({ sample_data[i].gridPoint.longitude, sample_data[i].gridPoint.latitude });
            }
        }

        // Prepare mappings file if requested
        std::ofstream mappings_out;
        if (config_.write_mappings) {
            mappings_out.open(config_.mappings_file);
            if (!mappings_out.is_open()) {
                std::cerr << "Error: Could not open mappings file for writing: " << config_.mappings_file << std::endl;
                config_.write_mappings = false; // Disable to prevent further errors
            }
            else {
                mappings_out << std::setw(12) << "Target_Lon" << std::setw(12) << "Target_Lat"
                    << std::setw(12) << "Source_Lon" << std::setw(12) << "Source_Lat"
                    << std::setw(10) << "Distance" << "\n";
                mappings_out << std::string(58, '-') << "\n";
            }
        }

        if (config_.interp_method == InterpolationMethod::NEAREST_NEIGHBOR) {
            for (int i = 0; i < target_grid.size(); ++i) {
                double min_dist = std::numeric_limits<double>::max();
                int closest_idx = -1;
                for (int j = 0; j < source_grid.size(); ++j) {
                    double dist = compute_distance(target_grid[i], source_grid[j]);
                    if (dist < min_dist) {
                        min_dist = dist;
                        closest_idx = unique_points[{source_grid[j].longitude, source_grid[j].latitude}];
                    }
                }
                nn_mapping_[i] = closest_idx;

                if (config_.write_mappings) {
                    const auto& target = target_grid[i];
                    const auto& source = sample_data[closest_idx];
                    mappings_out << std::setw(12) << std::fixed << std::setprecision(2) << target.longitude
                        << std::setw(12) << target.latitude
                        << std::setw(12) << source.gridPoint.longitude
                        << std::setw(12) << source.gridPoint.latitude
                        << std::setw(10) << min_dist << "\n";
                    mappings_out << std::string(58, '-') << "\n";
                }
            }
        }
        else {
            for (int i = 0; i < target_grid.size(); ++i) {
                std::vector<std::pair<double, int>> distances;
                for (int j = 0; j < source_grid.size(); ++j) {
                    double dist = compute_distance(target_grid[i], source_grid[j]);
                    if (config_.radius > 0 && dist <= config_.radius) {
                        distances.emplace_back(dist, unique_points[{source_grid[j].longitude, source_grid[j].latitude}]);
                    }
                    else if (config_.radius == 0) {
                        distances.emplace_back(dist, unique_points[{source_grid[j].longitude, source_grid[j].latitude}]);
                    }
                }
                std::sort(distances.begin(), distances.end());
                std::vector<int> indices;
                for (int k = 0; k < std::min(config_.max_points, static_cast<int>(distances.size())); ++k) {
                    indices.push_back(distances[k].second);
                    if (config_.write_mappings) {
                        const auto& target = target_grid[i];
                        const auto& source = sample_data[distances[k].second];
                        mappings_out << std::setw(12) << std::fixed << std::setprecision(2) << target.longitude
                            << std::setw(12) << target.latitude
                            << std::setw(12) << source.gridPoint.longitude
                            << std::setw(12) << source.gridPoint.latitude
                            << std::setw(10) << distances[k].first << "\n";
                    }
                }
                idw_mapping_[i] = indices;
                if (config_.write_mappings) {
                    mappings_out << std::string(58, '-') << "\n";
                }
            }
        }

        if (config_.write_mappings) {
            mappings_out.close();
        }
        if (config_.verbose) std::cout << "Mappings precomputed for " << target_grid.size() << " target points.\n";
    }

    void Regridder::regrid_file(const std::string& input_file,
        const std::string& output_file,
        const std::vector<GridPoint>& target_grid,
        int time_step,
        int first_time_step,
        int last_time_step) const {
        if (config_.verbose) std::cout << "Regridding file: " << input_file << " -> " << output_file << std::endl;
        std::ifstream in_file(input_file);
        std::ofstream out_file(output_file);
        if (!in_file.is_open() || !out_file.is_open()) {
            std::cerr << "Error: Unable to open files: " << input_file << " or " << output_file << std::endl;
            return;
        }

        // Rule #9 #33 fix: auto-detect line 1 = header vs data
        std::streampos pos_before_line1 = in_file.tellg();
        std::string first_line;
        std::getline(in_file, first_line);
        if (is_numeric_data_line(first_line)) {
            // Line 1 is data, NOT header; rewind so the data-read loop sees it.
            // Do NOT emit a header to the output (preserves no-header input shape).
            in_file.clear();
            in_file.seekg(pos_before_line1);
        } else {
            // Line 1 was a true header; emit reformatted header (legacy behavior)
            std::istringstream header_stream(first_line);
            std::vector<std::string> headers;
            std::string header;
            while (header_stream >> header) headers.push_back(header);
            write_headers(out_file, headers);
        }

        if (config_.data_layout == DataLayout::YEAR_BY_YEAR) {
            std::vector<SpatialData> year_data;
            std::string line;
            while (std::getline(in_file, line)) {
                std::istringstream iss(line);
                SpatialData sd;
                if (!(iss >> sd.gridPoint.longitude >> sd.gridPoint.latitude)) {
                    if (config_.verbose) std::cerr << "Warning: Skipping malformed line: " << line << std::endl;
                    continue;
                }
                sd.time_step = time_step;
                double value;
                while (iss >> value) sd.values.push_back(value);
                year_data.push_back(sd);
            }
            in_file.close();

            for (int i = 0; i < target_grid.size(); ++i) {
                SpatialData result;
                if (config_.interp_method == InterpolationMethod::NEAREST_NEIGHBOR) {
                    result = interpolate_nn(target_grid[i], year_data[nn_mapping_.at(i)]);
                }
                else {
                    result = interpolate_idw(target_grid[i], year_data, idw_mapping_.at(i));
                }
                out_file << std::fixed << std::setprecision(config_.precision)
                    << std::setw(12) << adjust_lon(result.gridPoint.longitude)
                    << std::setw(12) << result.gridPoint.latitude;
                for (const auto& val : result.values) {
                    out_file << std::setw(12) << val;
                }
                out_file << "\n";
            }
        }
        else { // GRID_BY_TIME
            std::vector<SpatialData> grid_cell_data;
            double prev_lon = std::numeric_limits<double>::quiet_NaN();
            double prev_lat = std::numeric_limits<double>::quiet_NaN();

            std::string line;
            while (std::getline(in_file, line)) {
                std::istringstream iss(line);
                SpatialData sd;
                if (!(iss >> sd.gridPoint.longitude >> sd.gridPoint.latitude >> sd.time_step)) {
                    if (config_.verbose) std::cerr << "Warning: Skipping malformed line: " << line << std::endl;
                    continue;
                }
                double value;
                while (iss >> value) sd.values.push_back(value);

                if (last_time_step >= 0 && (sd.time_step < first_time_step || sd.time_step > last_time_step)) {
                    continue;
                }

                if (!std::isnan(prev_lon) && (sd.gridPoint.longitude != prev_lon || sd.gridPoint.latitude != prev_lat)) {
                    for (int i = 0; i < target_grid.size(); ++i) {
                        SpatialData result;
                        if (config_.interp_method == InterpolationMethod::NEAREST_NEIGHBOR) {
                            result = interpolate_nn(target_grid[i], grid_cell_data[nn_mapping_.at(i)]);
                        }
                        else {
                            result = interpolate_idw(target_grid[i], grid_cell_data, idw_mapping_.at(i));
                        }
                        out_file << std::fixed << std::setprecision(config_.precision)
                            << std::setw(12) << adjust_lon(result.gridPoint.longitude)
                            << std::setw(12) << result.gridPoint.latitude
                            << std::setw(8) << result.time_step;
                        for (const auto& val : result.values) {
                            out_file << std::setw(12) << val;
                        }
                        out_file << "\n";
                    }
                    grid_cell_data.clear();
                }

                grid_cell_data.push_back(sd);
                prev_lon = sd.gridPoint.longitude;
                prev_lat = sd.gridPoint.latitude;
            }

            if (!grid_cell_data.empty()) {
                for (int i = 0; i < target_grid.size(); ++i) {
                    SpatialData result;
                    if (config_.interp_method == InterpolationMethod::NEAREST_NEIGHBOR) {
                        result = interpolate_nn(target_grid[i], grid_cell_data[nn_mapping_.at(i)]);
                    }
                    else {
                        result = interpolate_idw(target_grid[i], grid_cell_data, idw_mapping_.at(i));
                    }
                    out_file << std::fixed << std::setprecision(config_.precision)
                        << std::setw(12) << adjust_lon(result.gridPoint.longitude)
                        << std::setw(12) << result.gridPoint.latitude
                        << std::setw(8) << result.time_step;
                    for (const auto& val : result.values) {
                        out_file << std::setw(12) << val;
                    }
                    out_file << "\n";
                }
            }
        }

        in_file.close();
        out_file.close();
        if (config_.verbose) std::cout << "Completed regridding: " << output_file << "\n";
    }

    SpatialData Regridder::interpolate_nn(const GridPoint& target, const SpatialData& source) const {
        SpatialData result = source;
        result.gridPoint.longitude = target.longitude;
        result.gridPoint.latitude = target.latitude;
        return result;
    }

    SpatialData Regridder::interpolate_idw(const GridPoint& target,
        const std::vector<SpatialData>& source_chunk,
        const std::vector<int>& closest_indices) const {
        SpatialData result{ target.longitude, target.latitude, source_chunk[0].time_step,
                           std::vector<double>(source_chunk[0].values.size(), 0.0) };
        double weight_sum = 0.0;

        for (int idx : closest_indices) {
            double dist = compute_distance(target, { source_chunk[idx].gridPoint.longitude, source_chunk[idx].gridPoint.latitude });
            if (dist < 1e-6) return interpolate_nn(target, source_chunk[idx]);
            double weight = 1.0 / std::pow(dist, config_.power);
            weight_sum += weight;
            for (size_t i = 0; i < source_chunk[idx].values.size(); ++i) {
                result.values[i] += weight * source_chunk[idx].values[i];
            }
        }

        if (weight_sum > 0) {
            for (auto& val : result.values) val /= weight_sum;
        }
        else {
            return interpolate_nn(target, source_chunk[closest_indices[0]]);
        }
        return result;
    }

    double Regridder::adjust_lon(double lon) const {
        return (config_.adjust_longitude && lon > 180) ? (lon - 360) : lon;
    }

    void Regridder::write_headers(std::ofstream& out, const std::vector<std::string>& headers) const {
        for (size_t i = 0; i < headers.size(); ++i) {
            out << std::setw(12) << headers[i];
        }
        out << "\n";
    }

} // namespace regrid
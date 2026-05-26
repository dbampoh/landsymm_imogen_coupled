#ifndef REGRID_H
#define REGRID_H

#include <vector>
#include <string>
#include <map>
#include <fstream>

namespace regrid {

    /// @brief Represents a single grid point with longitude and latitude.
    struct GridPoint {
        double longitude;
        double latitude;
    };

    /// @brief Represents spatial data with location, time step, and values.
    struct SpatialData {
        GridPoint gridPoint;
        int time_step; ///< Year or other time identifier
        std::vector<double> values; ///< Data values (e.g., climate anomalies, vegetation metrics)
    };

    /// @brief Interpolation method options.
    enum class InterpolationMethod {
        NEAREST_NEIGHBOR,
        INVERSE_DISTANCE_WEIGHTED
    };

    /// @brief Distance metric options.
    enum class DistanceMetric {
        EUCLIDEAN,
        HAVERSINE
    };

    /// @brief Data layout options for input files.
    enum class DataLayout {
        YEAR_BY_YEAR,  ///< IMOGEN: data for one year, all grid cells
        GRID_BY_TIME   ///< LPJ-GUESS: data for one grid cell, all years
    };

    /// @brief Configuration for regridding.
    struct RegridConfig {
        InterpolationMethod interp_method = InterpolationMethod::INVERSE_DISTANCE_WEIGHTED;
        DistanceMetric distance_metric = DistanceMetric::HAVERSINE;
        DataLayout data_layout = DataLayout::GRID_BY_TIME;
        double radius = 100.0;        ///< Radius for IDW (km for Haversine, degrees for Euclidean)
        double power = 2.0;           ///< IDW weighting power
        int max_points = 5;           ///< Max points for IDW
        bool adjust_longitude = true; ///< Adjust longitude from 0-360 to -180-180
        int precision = 5;            ///< Output decimal precision
        bool verbose = false;         ///< Enable verbose logging
        bool write_mappings = false;  ///< Write closest points to file
        std::string mappings_file = "mappings.txt"; ///< Output file for mappings
    };

    /// @brief Core regridding class.
    class Regridder {
    public:
        /// @brief Constructs a Regridder with the given configuration.
        explicit Regridder(const RegridConfig& config = RegridConfig());

        /// @brief Reads a target grid from a file.
        /// @param filename Path to the grid file (format: longitude latitude per line).
        /// @return Vector of GridPoint objects.
        std::vector<GridPoint> read_grid_list(const std::string& filename) const;

        /// @brief Precomputes mappings from target to source grid points.
        /// @param source_sample_file Path to a sample input file to extract source grid.
        /// @param target_grid Target grid points.
        void precompute_mappings(const std::string& source_sample_file,
            const std::vector<GridPoint>& target_grid);

        /// @brief Regrids a single input file to an output file.
        /// @param input_file Path to the input data file.
        /// @param output_file Path to the output regridded file.
        /// @param target_grid Target grid points.
        /// @param time_step For YEAR_BY_YEAR, the time step to assign (e.g., year).
        /// @param first_time_step For GRID_BY_TIME, start of time range.
        /// @param last_time_step For GRID_BY_TIME, end of time range.
        void regrid_file(const std::string& input_file,
            const std::string& output_file,
            const std::vector<GridPoint>& target_grid,
            int time_step = 0,
            int first_time_step = 0,
            int last_time_step = -1) const;

    private:
        RegridConfig config_;
        std::map<int, int> nn_mapping_; ///< Nearest Neighbor mappings
        std::map<int, std::vector<int>> idw_mapping_; ///< IDW closest points

        double compute_distance(const GridPoint& p1, const GridPoint& p2) const;
        SpatialData interpolate_nn(const GridPoint& target, const SpatialData& source) const;
        SpatialData interpolate_idw(const GridPoint& target,
            const std::vector<SpatialData>& source_chunk,
            const std::vector<int>& closest_indices) const;
        double adjust_lon(double lon) const;
        void write_headers(std::ofstream& out, const std::vector<std::string>& headers) const;
    };

} // namespace regrid

#endif // REGRID_H
#ifndef IMOGEN_H
#define IMOGEN_H

#include <vector>
#include <string>
#include <array>
#include "imogenlogger.h"

// Output structure for clim_calc
/**
 * Structure to hold output anomalies from GCM_ANLG.
 */
struct GcmAnlgOutput {
    std::vector<std::vector<double>> t_anom_am;        // Air temperature anomaly (K)
    std::vector<std::vector<double>> precip_anom_am;   // Precipitation anomaly (mm/day)
    std::vector<std::vector<double>> rh15m_anom_am;    // Relative humidity anomaly
    std::vector<std::vector<double>> uwind_anom_am;    // U-wind speed anomaly (m/s)
    std::vector<std::vector<double>> vwind_anom_am;    // V-wind speed anomaly (m/s)
    std::vector<std::vector<double>> dtemp_anom_am;    // Diurnal temperature range anomaly (K)
    std::vector<std::vector<double>> pstar_ha_anom_am; // Surface pressure anomaly (hPa)
    std::vector<std::vector<double>> sw_anom_am;       // Shortwave radiation anomaly (W/m^2)
    std::vector<std::vector<double>> lw_anom_am;       // Longwave radiation anomaly (W/m^2)
    std::vector<double> dtemp_o;                       // Ocean temperature anomaly (K)
};


/**
 * Structure to hold output climate variables from CLIM_CALC.
 */
struct ClimCalcOutput {
    std::vector<std::vector<std::vector<std::vector<double>>>> t_out;         // Temperature (K)
    std::vector<std::vector<std::vector<std::vector<double>>>> conv_rain_out; // Convective rainfall (mm/day)
    std::vector<std::vector<std::vector<std::vector<double>>>> conv_snow_out; // Convective snowfall (mm/day)
    std::vector<std::vector<std::vector<std::vector<double>>>> ls_rain_out;   // Large-scale rainfall (mm/day)
    std::vector<std::vector<std::vector<std::vector<double>>>> ls_snow_out;   // Large-scale snowfall (mm/day)
    std::vector<std::vector<std::vector<std::vector<double>>>> qhum_out;      // Humidity (kg/kg)
    std::vector<std::vector<std::vector<std::vector<double>>>> wind_out;      // Wind speed (m/s)
    std::vector<std::vector<std::vector<std::vector<double>>>> pstar_out;     // Pressure (Pa)
    std::vector<std::vector<std::vector<std::vector<double>>>> sw_out;        // Shortwave radiation (W/m^2)
    std::vector<std::vector<std::vector<std::vector<double>>>> lw_out;        // Longwave radiation (W/m^2)
    std::vector<std::vector<std::vector<double>>> dtemp_out;                  // Daily temperature range (K)
    std::vector<int> seed_rain;                                             // Seeding for rainfall
};


// Function declarations 
void updateImogenControlData();
void writeFluxData();
double computeRelativeHumidityFromSpeificHumidty(double q, double p_Pa, double T_Kelvin);
double radf_co2(double co2, double co2ref, double q2co2);
double radf_non_co2(int year, int nyr_non_co2, bool file_non_co2, const std::string& file_non_co2_vals);
void qsat(std::vector<double>& qs, const std::vector<double>& t, const std::vector<double>& p, int npnts);
void redis(int nsdmax, int step_day, double max_precip_rate,
    std::vector<double>& prec_loc, std::vector<int>& n_event_local, int& n_tally);
void invert(const std::vector<double>& u_old, std::vector<double>& u_new,
    double p, double lambda_old, double lambda_new,
    const std::vector<double>& r1, const std::vector<double>& r2,
    double dz_top, int n_olevs);
void delta_temp(int n_olevs, double f_ocean, double kappa, double lambda_l,
    double lambda_o, double mu, double q, double& dtemp_l,
    std::vector<double>& dtemp_o);
void response(int ncall_yr, int year_run, std::vector<double>& rs);
void solang(double sindec, double t, double dt, const std::vector<double>& sinlat,
    const std::vector<double>& longit, int points, std::vector<double>& lit,
    std::vector<double>& cosz);
void rndm(double& random_num, std::vector<int>& seed);
void day_calc(int pointsm, int step_day, int day_mon,
    const std::vector<double>& sw_l,
    const std::vector<double>& precip_l,
    const std::vector<double>& t_l,
    const std::vector<double>& dtemp_day_l,
    const std::vector<double>& lw_l,
    const std::vector<double>& pstar_l,
    const std::vector<double>& wind_l,
    const std::vector<double>& rh15m_l,
    std::vector<std::vector<double>>& sw_sd,
    std::vector<std::vector<double>>& t_sd,
    std::vector<std::vector<double>>& lw_sd,
    std::vector<std::vector<double>>& conv_rain_sd,
    std::vector<std::vector<double>>& ls_rain_sd,
    std::vector<std::vector<double>>& ls_snow_sd,
    std::vector<std::vector<double>>& pstar_sd,
    std::vector<std::vector<double>>& wind_sd,
    std::vector<std::vector<double>>& qhum_sd,
    int month, int iday, const std::vector<double>& lat,
    const std::vector<double>& longitude, int sec_day,
    int nsdmax, std::vector<int>& seed_rain);

ClimCalcOutput clim_calc(bool anom, bool anlg, int gpoints, int mm, int md,
    const std::vector<std::vector<double>>& t_clim,
    const std::vector<std::vector<double>>& sw_clim,
    const std::vector<std::vector<double>>& lw_clim,
    const std::vector<std::vector<double>>& pstar_ha_clim,
    const std::vector<std::vector<double>>& rh15m_clim,
    const std::vector<std::vector<double>>& rainfall_clim,
    const std::vector<std::vector<double>>& snowfall_clim,
    const std::vector<std::vector<double>>& uwind_clim,
    const std::vector<std::vector<double>>& vwind_clim,
    const std::vector<std::vector<double>>& dtemp_clim,
    const std::vector<std::vector<double>>& f_wet_clim,
    const std::vector<std::vector<double>>& t_anom,
    const std::vector<std::vector<double>>& sw_anom,
    const std::vector<std::vector<double>>& lw_anom,
    const std::vector<std::vector<double>>& pstar_ha_anom,
    const std::vector<std::vector<double>>& rh15m_anom,
    const std::vector<std::vector<double>>& precip_anom,
    const std::vector<std::vector<double>>& uwind_anom,
    const std::vector<std::vector<double>>& vwind_anom,
    const std::vector<std::vector<double>>& dtemp_anom,
    int nsdmax, int step_day, std::vector<int> seed_rain,
    int sec_day, const std::vector<double>& lat,
    const std::vector<double>& longitude, double mdi);
void ocean_co2(int iyear, int year_co2, double co2_atmos_ppmv,
    double co2_atmos_init_ppmv, double dt_ocean,
    std::vector<double>& fa_ocean, double ocean_area,
    double grad_co2_atmos_ppmv, int year_run, double t_ocean_init,
    int nfarray, double& d_ocean_atmos);
void sunny(int daynumber, int jday, int points, int year,
    const std::vector<double>& lat, const std::vector<double>& lon,
    std::vector<std::vector<double>>& sun, std::vector<double>& time_max);

GcmAnlgOutput gcm_anlg(double q, int land_pts, int n_olevs, const std::string& dir_patt,
    double f_ocean, double kappa_o, double lambda_l, double lambda_o,
    double mu, double& longmin_am, double& latmin_am, double& longmax_am,
    double& latmax_am, int mm);
void solpos(int day, int /*year*/, double& sindec, double& scs);
void fair_non_co2_ghg(double ch4_ppbv, double n2o_ppbv, double ch4_init_ppbv,
    double n2o_init_ppbv, double co2_ppmv, double co2_init_ppmv,
    double& q_ch4, double& q_n2o, double& q_co2_fair);
void fair_non_co2_ghg_budget(int iyear, bool nonco2_emissions_lpjg,
    const std::vector<int>& yr_lpjg_nonco2, int nyr_lpjg_flux,
    const std::vector<double>& ch4_lpjg, const std::vector<double>& n2o_lpjg,
    const std::vector<int>& yr_emiss, int nyr_emiss_nonco2,
    const std::vector<double>& ch4_emiss, const std::vector<double>& n2o_emiss,
    double& ch4_ppbv, double& n2o_ppbv,
    double tau_decay_ch4, double tau_decay_n2o,
    const std::string& dir_common, const std::string& this_year);


// Constants
extern const int MM;
extern const int MD;
extern const int NSDMAX;
extern const int SEC_DAY;
extern const int GPOINTS;
extern const int N_OLEVS;
extern const int NFARRAY;
extern const double OCEAN_AREA;
extern const double CONV;
extern const double MDI;
extern const std::vector<int> MTHDAY;
extern const std::vector<std::string> DRIVE_MONTH;
extern const int NGPOINTS;


// namespace filesystem_dkb {
//
//     bool exists(const std::string& path) {
//        struct stat buffer;
//        return (stat(path.c_str(), &buffer) == 0);
//    }
//
//     bool create_directory(const std::string& path) {
//        // Log the attempt to create directory
//        ImogenLogger::getInstance().debug("Creating directory: " + path);
//
//        // Handle empty path
//        if (path.empty()) {
//            ImogenLogger::getInstance().error("Cannot create directory: empty path");
//            return false;
//        }
//
//        // Try creating the directory
//#if defined(_WIN32) || defined(_WIN64)
//        if (mkdir(path.c_str()) == 0) {
//            ImogenLogger::getInstance().debug("Directory created: " + path);
//            return true;
//        }
//#else
//        if (mkdir(path.c_str(), 0755) == 0) {
//            ImogenLogger::getInstance().debug("Directory created: " + path);
//            return true;
//        }
//#endif
//
//        // Check if directory already exists
//        if (errno == EEXIST) {
//            ImogenLogger::getInstance().debug("Directory already exists: " + path);
//            return true;
//        }
//
//        // If failed due to missing parent directories, create them recursively
//        if (errno == ENOENT) {
//            // Find parent directory
//            size_t pos = path.find_last_of("/\\");
//            if (pos == std::string::npos || pos == 0) {
//                ImogenLogger::getInstance().error("Cannot create directory: no parent path for " + path);
//                return false;
//            }
//
//            std::string parent = path.substr(0, pos);
//            // Recursively create parent directories
//            if (!create_directory(parent)) {
//                ImogenLogger::getInstance().error("Failed to create parent directory: " + parent);
//                return false;
//            }
//
//            // Try creating the directory again
//#if defined(_WIN32) || defined(_WIN64)
//            if (mkdir(path.c_str()) == 0) {
//                ImogenLogger::getInstance().debug("Directory created after parent: " + path);
//                return true;
//            }
//#else
//            if (mkdir(path.c_str(), 0755) == 0) {
//                ImogenLogger::getInstance().debug("Directory created after parent: " + path);
//                return true;
//            }
//#endif
//
//            ImogenLogger::getInstance().error("Failed to create directory: " + path + " (errno: " + std::to_string(errno) + ")");
//            return false;
//        }
//
//        // Other errors (e.g., EACCES)
//        ImogenLogger::getInstance().error("Failed to create directory: " + path + " (errno: " + std::to_string(errno) + ")");
//        return false;
//    }
//
//    bool remove(const std::string& path) {
//        struct stat buffer;
//        if (stat(path.c_str(), &buffer) != 0) return false;
//
//#if defined(_WIN32) || defined(_WIN64)
//        if (buffer.st_mode & _S_IFDIR) {
//            return (_rmdir(path.c_str()) == 0);
//        }
//        else {
//            return (_unlink(path.c_str()) == 0);
//        }
//#else
//        if (S_ISDIR(buffer.st_mode)) {
//            return (rmdir(path.c_str()) == 0);
//        }
//        else {
//            return (unlink(path.c_str()) == 0);
//        }
//#endif
//    }
//
//} // namespace filesystem

int RUN_IMOGEN_ENGINE();

#endif // IMOGEN_H
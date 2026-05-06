//Main IMOGEN Climate Model Controller
//This C++ version of IMOGEN is fairly a direct translation of the original Fortran based IMOGEN
//Some cleanups may be done later in terms of variable declaration and organization, memory allocation and optimal variable usage

#if defined(_WIN32) || defined(_WIN64)
#include <direct.h>    // For _mkdir, _rmdir
#include <io.h>        // For _unlink
#include <sys/stat.h>  // For _stat
#define stat _stat     // Alias for Windows
#else
#include <sys/stat.h>  // For stat, mkdir
#include <unistd.h>    // For rmdir, unlink
#endif

#include <stdexcept>
#include <cstdlib>
#include <cstdio>   // For remove
#include <cerrno>
#include <cstring>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <thread>
#include <chrono>
#include <iomanip>
#include <cmath>
#include <algorithm>
#include <limits>
#include <array>
#include <algorithm>
#include "parameters.h"
#include "imogenlogger.h"
#include "climatemodel.h"

//Define this macro to be used throughout code
#define logger ImogenLogger::getInstance()

const int MM = 12;
const int MD = 30;
const int NSDMAX = 24;
const int SEC_DAY = 86400;
const int GPOINTS = 1631;
const int N_OLEVS = 254;
const int NFARRAY = 10000;
const double OCEAN_AREA = 3.627e14;
const double CONV = 0.471;
const double MDI = 999.9;
const std::vector<int> MTHDAY = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
const std::vector<std::string> DRIVE_MONTH = { "/jan", "/feb", "/mar", "/apr", "/may", "/jun",
                                             "/jul", "/aug", "/sep", "/oct", "/nov", "/dec" };
const int NGPOINTS = 3698;

namespace filesystem_dkb {

    bool exists(const std::string& path) {
        struct stat buffer;
        return (stat(path.c_str(), &buffer) == 0);
    }

    //creates directory recursively
    bool create_directory(const std::string& path) {
        // Log the attempt to create directory
        logger.debug("Attempting to create directory: " + path);

        // Handle empty path
        if (path.empty()) {
            ImogenLogger::getInstance().error("Cannot create directory: empty path");
            return false;
        }

        // Try creating the directory
#if defined(_WIN32) || defined(_WIN64)
        if (mkdir(path.c_str()) == 0) {
            logger.debug("Directory created: " + path);
            return true;
        }
#else
        if (mkdir(path.c_str(), 0755) == 0) {
            ImogenLogger::getInstance().debug("Directory created: " + path);
            return true;
        }
#endif

        // Check if directory already exists
        if (errno == EEXIST) {
            logger.debug("Directory already exists: " + path);
            return true;
        }

        // If failed due to missing parent directories, create them recursively
        if (errno == ENOENT) {
            // Find parent directory
            size_t pos = path.find_last_of("/\\");
            if (pos == std::string::npos || pos == 0) {
                logger.error("Cannot create directory: no parent path for " + path);
                return false;
            }

            std::string parent = path.substr(0, pos);
            // Recursively create parent directories
            if (!create_directory(parent)) {
                logger.error("Failed to create parent directory: " + parent);
                return false;
            }

            // Try creating the directory again
#if defined(_WIN32) || defined(_WIN64)
            if (mkdir(path.c_str()) == 0) {
                logger.debug("Directory created after parent: " + path);
                return true;
            }
#else
            if (mkdir(path.c_str(), 0755) == 0) {
                logger.debug("Directory created after parent: " + path);
                return true;
            }
#endif

            logger.error("Failed to create directory: " + path + " (errno: " + std::to_string(errno) + ")");
            return false;
        }

        // Other errors (e.g., EACCES)
        logger.error("Failed to create directory: " + path + " (errno: " + std::to_string(errno) + ")");
        return false;
    }

    bool remove(const std::string& path) {
        struct stat buffer;
        if (stat(path.c_str(), &buffer) != 0) return false;

#if defined(_WIN32) || defined(_WIN64)
        if (buffer.st_mode & _S_IFDIR) {
            return (_rmdir(path.c_str()) == 0);
        }
        else {
            return (_unlink(path.c_str()) == 0);
        }
#else
        if (S_ISDIR(buffer.st_mode)) {
            return (rmdir(path.c_str()) == 0);
        }
        else {
            return (unlink(path.c_str()) == 0);
        }
#endif
    }

} // namespace filesystem

int RUN_IMOGEN_ENGINE() {

    //create output dir here
    filesystem_dkb::create_directory(std::string((char*)IMOGENConfig::DIR_COMMON_OUT) + "/IMOGEN/");

    //Initialize Imogen logger
    logger.initialize((char*)IMOGENConfig::DIR_COMMON_OUT, ImogenLogger::LogLevel::INFO);

    // Basic timestepping variables
    int year1 = IMOGENConfig::YEAR1;
    int iyend = IMOGENConfig::IYEND;
    int year1Lpjg = IMOGENConfig::YEAR1_LPJG;
    int iyear;
    bool fileNonCo2 = IMOGENConfig::FILE_NON_CO2;
    int mm = MM, md = MD, stepDay = IMOGENConfig::STEP_DAY, secDay = SEC_DAY, nsdmax = NSDMAX;
    std::vector<int> mthday = MTHDAY;
    int igp, imd, imm, ind;

    // Radiative forcing variables
    double qCo2, qNonCo2, qCh4, qN2o, qCo2Fair;

    // Emission and flux variables
    int nyrNonCo2 = IMOGENConfig::NYR_NON_CO2;
    int tallyCo2File, yrCo2File;
    double co2FilePpmv;
    int nyrEmiss = IMOGENConfig::NYR_EMISS;
    int nyrLpjgFlux = IMOGENConfig::NYR_LPJG_FLUX;
    int nyrEmissNonco2 = IMOGENConfig::NYR_EMISS_NONCO2;
    std::vector<int> yrEmiss(300, 0);
    std::vector<int> yrEmissNonco2(300, 0);
    std::vector<int> yrLpjg(300, 0);
    std::vector<int> yrLpjgNonco2(300, 0);
    int emissTally;
    double dLandAtmos, dOceanAtmos;
    std::vector<double> cEmiss(300, 0.0);
    double cEmissLocal;
    std::vector<double> cLpjg(300, 0.0);
    double cLpjgLocal;
    std::vector<double> ch4Emiss(300, 0.0);
    std::vector<double> n2oEmiss(300, 0.0);
    std::vector<double> ch4Lpjg(300, 0.0);
    std::vector<double> n2oLpjg(300, 0.0);

    // GCM analogue model variables
    double q2co2 = IMOGENConfig::Q2CO2;
    double fOcean = IMOGENConfig::F_OCEAN;
    double kappaO = IMOGENConfig::KAPPA_O;
    double lambdaL = IMOGENConfig::LAMBDA_L;
    double lambdaO = IMOGENConfig::LAMBDA_O;
    double mu = IMOGENConfig::MU;
    double tOceanInit = IMOGENConfig::T_OCEAN_INIT;
    double tauDecayCh4 = IMOGENConfig::TAU_DECAY_CH4;
    double tauDecayN2o = IMOGENConfig::TAU_DECAY_N2O;
    std::vector<double> faOcean(NFARRAY, 0.0);
    double oceanArea = OCEAN_AREA;
    std::vector<double> dtempO(N_OLEVS, 0.0);
    double dtOcean;

    // File and directory variables
    std::string dirPatt = std::string((char*)IMOGENConfig::DIR_PATT);
    std::string dirClim = std::string((char*)IMOGENConfig::DIR_CLIM);
    std::string dirCommon = std::string((char*)IMOGENConfig::DIR_COMMON);
    std::string dirCommonOut = std::string((char*)IMOGENConfig::DIR_COMMON_OUT); //For output on parallel runs, usually  "./" in the ins
    std::string fileClim;
    std::string fileScenEmits = std::string((char*)IMOGENConfig::FILE_SCEN_EMITS);
    std::string fileNonCo2Vals = std::string((char*)IMOGENConfig::FILE_NON_CO2_VALS);
    std::string fileScenCo2Ppmv = std::string((char*)IMOGENConfig::FILE_SCEN_CO2_PPMV);
    std::string fileLpjgFlux = std::string((char*)IMOGENConfig::FILE_LPJG_FLUX);
    std::string fileCh4N2oEmits = std::string((char*)IMOGENConfig::FILE_CH4_N2O_EMITS);
    std::string fileLpjgCh4N2oFlux = std::string((char*)IMOGENConfig::FILE_LPJG_CH4_N2O_FLUX);
    std::string fileGridlist = std::string((char*)IMOGENConfig::FILE_GRIDLIST);
    std::vector<std::string> driveMonth = DRIVE_MONTH;

    // Run conditions and switches
    bool anlg = IMOGENConfig::ANLG;
    bool anom = IMOGENConfig::ANOM;
    bool cEmissions = IMOGENConfig::C_EMISSIONS;
    bool cEmissionsIn = IMOGENConfig::C_EMISSIONS;
    bool lpjgCflux = IMOGENConfig::LPJG_CFLUX;
    bool includeCo2 = IMOGENConfig::INCLUDE_CO2;
    bool includeCo2In = IMOGENConfig::INCLUDE_CO2;
    bool includeNonCo2 = IMOGENConfig::INCLUDE_NON_CO2;
    bool dailyOut = IMOGENConfig::DAILYOUT;
    bool landFeed = IMOGENConfig::LAND_FEED;
    bool oceanFeed = IMOGENConfig::OCEAN_FEED;
    bool spinup = IMOGENConfig::SPINUP;
    bool nonco2Emissions = IMOGENConfig::NONCO2_EMISSIONS;
    bool nonco2EmissionsLpjg = IMOGENConfig::NONCO2_EMISSIONS_LPJG;
    bool co2RfFair = IMOGENConfig::CO2_RF_FAIR;
    bool regrid = IMOGENConfig::REGRID;
    bool lImpacts = false; // Not used, set to false
    bool firstCall = IMOGENConfig::FIRSTCALL;

    // Climatology and anomaly arrays
    std::vector<std::vector<double>> tAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> precipAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> rh15mAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> uwindAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> vwindAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> dtempAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> pstarHaAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> swAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> lwAnom(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<double> lat(GPOINTS, 0.0);
    std::vector<double> longG(GPOINTS, 0.0);

    std::vector<std::vector<double>> tClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> rainfallClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> snowfallClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> rh15mClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> uwindClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> vwindClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> dtempClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> pstarHaClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> swClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> lwClim(GPOINTS, std::vector<double>(MM, 0.0));
    std::vector<std::vector<double>> fWetClim(GPOINTS, std::vector<double>(MM, 0.0));

    std::vector<std::vector<std::vector<std::vector<double>>>> tOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> convRainOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> convSnowOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> lsRainOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> lsSnowOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> qhumOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> windOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));//DKB
    std::vector<std::vector<std::vector<std::vector<double>>>> pstarOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> swOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> lwOut(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(MD, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<double>>> dtempOut(GPOINTS, std::vector<std::vector<double>>(MM, std::vector<double>(MD, 0.0)));
    std::vector<std::vector<int>> fWetClimOut(GPOINTS, std::vector<int>(MM, 0));

    std::vector<std::vector<std::vector<std::vector<double>>>> tOutM(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(31, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> pOutM(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(31, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> swOutM(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(31, std::vector<double>(NSDMAX, 0.0))));
    std::vector<std::vector<std::vector<std::vector<double>>>> windOutM(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(31, std::vector<double>(NSDMAX, 0.0))));//DKB
    std::vector<std::vector<std::vector<std::vector<double>>>> rhOutM(GPOINTS, std::vector<std::vector<std::vector<double>>>(MM, std::vector<std::vector<double>>(31, std::vector<double>(NSDMAX, 0.0))));//DKB - Computed from q, presure and temp
    std::vector<std::vector<std::vector<double>>> dtempOutM(GPOINTS, std::vector<std::vector<double>>(MM, std::vector<double>(31, 0.0)));

    // Other variables
    double co2Ppmv, co2LocalPpmv, co2ChangePpmv, q, ch4Ppbv, n2oPpbv;
    double mdi = MDI;
    double dump;
    std::vector<int> seedRain(4, 0);
    int i, j, k, n, l, iiClim;
    double latminClim, latmaxClim, longminClim, longmaxClim;
    double latminAm, latmaxAm, longminAm, longmaxAm;
    double latminDat, latmaxDat, longminDat, longmaxDat;

    // LPJ-GUESS interaction variables
    bool runnowExist, runnowOpen, runfluxExist, runfluxOpen;
    bool runnonco2fluxExist, runnonco2fluxOpen, doneExist, errorExist;
    bool runnow, keepRunning = IMOGENConfig::KEEPRUNNING;
    std::string sdate, stime;
    std::string thisYear, lastYear;
    int varyear;
    std::string varyearStr;

    // Create CO2_all.dat
    std::ofstream file(dirCommonOut + "/IMOGEN/CO2_all.dat", std::ios::out | std::ios::trunc);
    file.close();


    // Main KEEPRUNNING loop
    keepRunning = IMOGENConfig::KEEPRUNNING;
    while (keepRunning) {
        runnow = false;
        runnowExist = false;
        runnowOpen = false;
        runfluxExist = false;
        runfluxOpen = false;
        runnonco2fluxExist = false;
        runnonco2fluxOpen = false;
        doneExist = false;
        errorExist = false;

        while (!runnow) {
            std::this_thread::sleep_for(std::chrono::seconds(3));
            std::cout << "." << std::flush;

            // [Step 7 of unified-codebase rebuild: bug C2 fix — restore the
            //  doneExist filesystem check that was previously short-circuited
            //  to "doneExist = true" (which silently bypassed the LPJG?IMOGEN
            //  per-year handshake's safety semantics). The first-call special
            //  case avoids an infinite poll on the very first iteration of the
            //  very first run, when no prior 'done' from LPJ-GUESS exists yet.
            //  - DKB 2026-05-06]
            doneExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/done");
            if (firstCall && !doneExist) {
                doneExist = true;  // first-call bypass: LPJG hasn't written 'done' yet
            }

            {
                std::ifstream file(dirCommon + "/LPJG_main/IMOGEN/imogen_lpjg.txt");
                // [Step 7 fix: bug C3 part 1 — restore the runnowOpen guard]
                runnowOpen = !file.is_open();
            }

            runfluxExist = filesystem_dkb::exists(fileLpjgFlux);
            {
                std::ifstream file(fileLpjgFlux);
                // [Step 7 fix: bug C3 part 2 — restore the runfluxOpen guard]
                runfluxOpen = !file.is_open();
            }
            errorExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/error");
            runnowExist = filesystem_dkb::exists(dirCommon + "/LPJG_main/IMOGEN/imogen_lpjg.txt");
            if (nonco2Emissions) {
                runnonco2fluxExist = filesystem_dkb::exists(fileLpjgCh4N2oFlux);
                {
                    std::ifstream file(fileLpjgCh4N2oFlux);
                    // [Step 7 fix: bug C3 part 3 — restore the runnonco2fluxOpen guard]
                    runnonco2fluxOpen = !file.is_open();
                }
            }

            // Debug output
            std::cout << "RUNNOW_EXIST = " << runnowExist << "\n";
            std::cout << "RUNNOW_OPEN = " << runnowOpen << "\n";
            std::cout << "RUNFLUX_EXIST = " << runfluxExist << "\n";
            std::cout << "RUNFLUX_OPEN = " << runfluxOpen << "\n";
            std::cout << "DONE_EXIST = " << doneExist << "\n";
            std::cout << "NONCO2_EMISSIONS = " << nonco2Emissions << "\n";
            if (nonco2Emissions) {
                std::cout << "RUNNONCO2FLUX_EXIST = " << runnonco2fluxExist << "\n";
                std::cout << "RUNNONCO2FLUX_OPEN = " << runnonco2fluxOpen << "\n";
            }

            if (runnowExist && !runnowOpen && runfluxExist && !runfluxOpen && doneExist &&
                (!nonco2Emissions || (runnonco2fluxExist && !runnonco2fluxOpen))) {
                runnow = true;

                // Update parameters from IMOGENConfig (replacing SETTIN_LPJG)
                //To be moved around later
                dirCommon = IMOGENConfig::DIR_COMMON;
                year1 = IMOGENConfig::YEAR1;
                iyend = IMOGENConfig::IYEND;
                spinup = IMOGENConfig::SPINUP;
                year1Lpjg = IMOGENConfig::YEAR1_LPJG;
                keepRunning = IMOGENConfig::KEEPRUNNING;
                firstCall = IMOGENConfig::FIRSTCALL;

                // Implement DATE_AND_TIME with std::chrono
                auto now = std::chrono::system_clock::now();
                auto time_t = std::chrono::system_clock::to_time_t(now);
                std::stringstream ss;
                ss << std::put_time(std::localtime(&time_t), "%Y%m%d %H%M%S");
                sdate = ss.str().substr(0, 8);
                stime = ss.str().substr(9, 6);
                std::cout << "DateTime: "<< sdate << " " << stime << "\n";
            }

            if (errorExist) {
                std::cout << "Error in LPJ-GUESS\n";
                return 1;
            }
        }

        // Handle VARYEAR
        if (firstCall) {
            varyear = 0;
        }
        else {
            std::ifstream file(dirCommonOut + "/IMOGEN/VARYEAR.dat");
            file >> varyear;
            file.close();
        }
        varyear = (varyear == 30) ? 1 : varyear + 1;
        {
            std::ofstream file(dirCommonOut + "/IMOGEN/VARYEAR.dat", std::ios::out | std::ios::trunc);
            file << varyear;
            file.close();
        }
        std::cout << "Variability iterator is " << varyear << "\n";
        varyearStr = std::to_string(varyear);

        // Spin-up settings
        if (spinup) {
            includeCo2 = false;
            cEmissions = false;
            thisYear = std::to_string(year1);
            std::cout << "YEAR1 is " << year1 << "\n";

            filesystem_dkb::create_directory(dirCommonOut + "/IMOGEN/output/" + thisYear);


            {
                std::ofstream file(dirCommonOut + "/IMOGEN/output/" + thisYear + "/CO2.dat");
                if (nonco2Emissions) {
                    file << thisYear << " " << IMOGENConfig::CO2_INIT_PPMV << " 0.0 0.0 0.0 0.0 "
                        << IMOGENConfig::CH4_INIT_PPBV << " " << IMOGENConfig::N2O_INIT_PPBV << "\n";
                }
                else {
                    file << thisYear << " " << IMOGENConfig::CO2_INIT_PPMV << " 0.0 0.0 0.0 0.0\n";
                }
                file.close();
            }
        }
        else {
            includeCo2 = includeCo2In;
            cEmissions = cEmissionsIn;
        }

        // Main year loop
        for (iyear = year1; iyear <= iyend; ++iyear) {
            logger.info("Processing year: " + std::to_string(iyear));
            thisYear = std::to_string(iyear);
            lastYear = std::to_string(iyear - 1);

            //writeFluxData(); //DKB Writes flux data //used for testing

            // Create output directory
            if (!filesystem_dkb::create_directory(dirCommonOut + "/IMOGEN/output/" + thisYear)) {
                logger.warn("Output directory creation failed: " +
                    dirCommon + "/IMOGEN/output/" + thisYear);
            }
            else {
                logger.info("Created output directory: " + dirCommonOut + "/IMOGEN/output/" + thisYear);
            }
     

            // Initialize for first year or spin-up
            if (iyear == year1Lpjg || spinup) {
                co2Ppmv = IMOGENConfig::CO2_INIT_PPMV;
                if (includeCo2) co2ChangePpmv = 0.0;
                if (nonco2EmissionsLpjg) {
                    ch4Ppbv = IMOGENConfig::CH4_INIT_PPBV;
                    n2oPpbv = IMOGENConfig::N2O_INIT_PPBV;
                }
                if (anlg) {
                    std::fill(dtempO.begin(), dtempO.end(), 0.0);
                    if (includeCo2 && oceanFeed && cEmissions) {
                        std::fill(faOcean.begin(), faOcean.end(), 0.0);
                    }
                }
                seedRain = { 9465, 1484, 3358, 8350 };
            }

            // Read previous year's state for non-first years
            if (iyear > year1Lpjg && (iyend - year1) == 0) {
                if (oceanFeed) {
                    std::cout << "Reading FA_OCEAN and DTEMP_O from file\n";
                    std::ifstream faFile(dirCommonOut + "/IMOGEN/output/" + lastYear + "/fa_ocean.dat");
                    std::ifstream dtFile(dirCommonOut + "/IMOGEN/output/" + lastYear + "/dtemp_o.dat");
                    for (i = 0; i < NFARRAY; ++i) faFile >> faOcean[i];
                    for (i = 0; i < N_OLEVS; ++i) dtFile >> dtempO[i];
                    faFile.close();
                    dtFile.close();
                }
                std::ifstream co2File(dirCommonOut + "/IMOGEN/output/" + lastYear + "/CO2.dat");
                if (nonco2Emissions) {
                    co2File >> yrCo2File >> co2Ppmv >> dump >> dump >> dump >> co2ChangePpmv >> ch4Ppbv >> n2oPpbv;
                }
                else {
                    co2File >> yrCo2File >> co2Ppmv >> dump >> dump >> dump >> co2ChangePpmv;
                }
                co2File.close();
                std::cout << yrCo2File << " " << co2Ppmv << " " << co2ChangePpmv << " " << ch4Ppbv << " " << n2oPpbv << "\n";
                if (yrCo2File + 1 != iyear) {
                    std::cout << "ERROR: CO2 value from previous year not available\n";
                    std::ofstream errFile(dirCommonOut + "/IMOGEN/output/" + thisYear + "/error");
                    errFile << "ERROR: CO2 value from previous year not available\n";
                    errFile.close();
                    return 1;
                }
            }

            // Capture CO2 concentration
            if (includeCo2) co2LocalPpmv = co2Ppmv;

            // Read emissions/CO2 concentrations
            if (cEmissions && includeCo2 && anom && anlg) {
                std::ifstream file(fileScenEmits);
                for (n = 0; n < nyrEmiss; ++n) {
                    file >> yrEmiss[n] >> cEmiss[n];
                }
                file.close();
                if (nonco2Emissions) {
                    std::ifstream file2(fileCh4N2oEmits);
                    for (n = 0; n < nyrEmissNonco2; ++n) {
                        file2 >> yrEmissNonco2[n] >> ch4Emiss[n] >> n2oEmiss[n];
                    }
                    file2.close();
                }
            }

            // Read LPJ-GUESS fluxes
            if (cEmissions && includeCo2 && anom && anlg && landFeed && lpjgCflux) {
                //std::ifstream file(dirCommon + "/LPJG_main/IMOGEN/" + fileLpjgFlux);
                std::ifstream file(fileLpjgFlux);
                for (n = 0; n < nyrLpjgFlux; ++n) {
                    file >> yrLpjg[n] >> cLpjg[n];
                    std::cout << "C flux from LPJG is " << cLpjg[n] << " for year " << yrLpjg[n] << "\n";
                }
                file.close();
                if (nonco2EmissionsLpjg) {
                    //std::ifstream file2(dirCommon + "/LPJG_main/IMOGEN/" + fileLpjgCh4N2oFlux);
                    std::ifstream file2(fileLpjgCh4N2oFlux);
                    for (n = 0; n < nyrLpjgFlux; ++n) {
                        std::cout << "Reading CH4 and N2O fluxes from LPJ-GUESS\n";
                        file2 >> yrLpjgNonco2[n] >> ch4Lpjg[n] >> n2oLpjg[n];
                        std::cout << "CH4 flux from LPJG is " << ch4Lpjg[n] << " for year " << yrLpjgNonco2[n] << "\n";
                        std::cout << "N2O flux from LPJG is " << n2oLpjg[n] << " for year " << yrLpjgNonco2[n] << "\n";
                    }
                    file2.close();
                }
                std::ofstream doneFile(dirCommon + "/LPJG_main/IMOGEN/done", std::ios::out | std::ios::trunc);
                doneFile.close();
                filesystem_dkb::remove(dirCommon + "/LPJG_main/IMOGEN/done");
            }

            // Read prescribed CO2 concentrations
            if (!cEmissions && includeCo2) {
                std::ifstream file(fileScenCo2Ppmv);
                tallyCo2File = 0;
                while (file) {
                    file >> yrCo2File >> co2FilePpmv;
                    if (file.eof()) break;
                    if (yrCo2File == iyear) {
                        co2Ppmv = co2FilePpmv;
                        tallyCo2File++;
                    }
                }
                file.close();
                if (tallyCo2File != 1) {
                    std::cout << "CO2 value not found in file\n";
                    std::ofstream errFile(dirCommon + "/IMOGEN/output/" + thisYear + "/error");
                    errFile << "CO2 value not found in file\n";
                    errFile.close();
                    return 1;
                }
            }

            // Read climatology
            iiClim = dirClim.length();
            for (j = 0; j < MM; ++j) {
                fileClim = dirClim.substr(0, iiClim) + driveMonth[j] + varyearStr;
                std::ifstream file(fileClim);
                if (!file.is_open()) {
                    std::cerr << "Error opening " << fileClim << "\n";
                    return 1;
                }
                
                file >> longminClim >> latminClim >> longmaxClim >> latmaxClim;

                //Debug information
                /*logger.info("CLIMATOLOGY HEADER");
                logger.info("CLimate Path: " + fileClim);
                logger.info("LongminClim: " + std::to_string(longminClim));
                logger.info("LatminClim: " + std::to_string(latminClim));
                logger.info("LongmaxClim: " + std::to_string(longmaxClim));
                logger.info("LatmaxClim: " + std::to_string(latmaxClim));*/


                for (l = 0; l < GPOINTS; ++l) {
                    file >> longG[l] >> lat[l] >> tClim[l][j] >> rh15mClim[l][j] >> uwindClim[l][j] >>
                        vwindClim[l][j] >> lwClim[l][j] >> swClim[l][j] >> dtempClim[l][j] >>
                        rainfallClim[l][j] >> snowfallClim[l][j] >> pstarHaClim[l][j] >> fWetClim[l][j];
                }
                file.close();
            }

            logger.info("Read Climatology Complete");

            // Calculate anomalies
            if (anom && anlg) {
                if (includeCo2) {

                    std::cout << co2Ppmv << " " << IMOGENConfig::CO2_INIT_PPMV << " " << q2co2 << std::endl;
                    
                    qCo2 = radf_co2(co2Ppmv, IMOGENConfig::CO2_INIT_PPMV, q2co2);
                }
                
                if (includeNonCo2) {
                    qNonCo2 = radf_non_co2(iyear, nyrNonCo2, fileNonCo2, fileNonCo2Vals);
                    if (nonco2Emissions) {
                        std::cout << "Including CH4 and N2O emissions directly\n";
                        fair_non_co2_ghg(ch4Ppbv, n2oPpbv, IMOGENConfig::CH4_INIT_PPBV,
                            IMOGENConfig::N2O_INIT_PPBV, co2Ppmv,
                            IMOGENConfig::CO2_INIT_PPMV, qCh4, qN2o, qCo2Fair);
                        if (co2RfFair) qCo2 = qCo2Fair;
                    }
                }
                q = nonco2Emissions ? qCo2 + qNonCo2 + qCh4 + qN2o : qCo2 + qNonCo2;
                

                {
                    std::ofstream file(dirCommonOut + "/IMOGEN/RF_all.dat", std::ios::out | std::ios::app);
                    if (anlg && anom) {
                        if (nonco2Emissions) {
                            file << iyear << " " << q << " " << qCo2 << " " << qNonCo2 << " " << qCh4 << " " << qN2o << "\n";
                        }
                        else {
                            file << iyear << " " << q << " " << qCo2 << " " << qNonCo2 << "\n";
                        }
                    }
                    file.close();
                }

                if (includeCo2 || includeNonCo2) {
                    auto anlg_output = gcm_anlg(q, GPOINTS, N_OLEVS, dirPatt, fOcean, kappaO,
                        lambdaL, lambdaO, mu, longminAm, latminAm,
                        longmaxAm, latmaxAm, MM);
                    tAnom = anlg_output.t_anom_am;
                    precipAnom = anlg_output.precip_anom_am;
                    rh15mAnom = anlg_output.rh15m_anom_am;
                    uwindAnom = anlg_output.uwind_anom_am;
                    vwindAnom = anlg_output.vwind_anom_am;
                    dtempAnom = anlg_output.dtemp_anom_am;
                    pstarHaAnom = anlg_output.pstar_ha_anom_am;
                    swAnom = anlg_output.sw_anom_am;
                    lwAnom = anlg_output.lw_anom_am;
                    dtempO = anlg_output.dtemp_o;

                     
                    //Debug
                    /*logger.info("longminClim: " + std::to_string(longminClim));
                    logger.info("longminAm: " + std::to_string(longminAm));
                    logger.info("latminClim: " + std::to_string(latminClim));
                    logger.info("latminAm: " + std::to_string(latminAm));
                    logger.info("longmaxClim: " + std::to_string(longmaxClim));
                    logger.info("longmaxAm: " + std::to_string(longmaxAm));
                    logger.info("latmaxClim: " + std::to_string(latmaxClim));
                    logger.info("latmaxAm: " + std::to_string(latmaxAm));
                    */

                    if (std::abs(longminClim - longminAm) >= 1.0e-6 ||
                        std::abs(latminClim - latminAm) >= 1.0e-6 ||
                        std::abs(longmaxClim - longmaxAm) >= 1.0e-6 ||
                        std::abs(latmaxClim - latmaxAm) >= 1.0e-6) {
                       
                        logger.error("Driving files are incompatible");
                        logger.info("longminClim: " + std::to_string(longminClim));
                        logger.info("longminAm: " + std::to_string(longminAm));
                        logger.info("latminClim: " + std::to_string(latminClim));
                        logger.info("latminAm: " + std::to_string(latminAm));
                        logger.info("longmaxClim: " + std::to_string(longmaxClim));
                        logger.info("longmaxAm: " + std::to_string(longmaxAm));
                        logger.info("latmaxClim: " + std::to_string(latmaxClim));
                        logger.info("latmaxAm: " + std::to_string(latmaxAm));

                        std::ofstream errFile(dirCommonOut + "/IMOGEN/output/" + thisYear + "/error");
                        errFile << "Driving files are incompatible\n";
                        errFile.close();
                        return 1;
                    }
                }
            }

            // Calculate daily climate
            auto clim_output = clim_calc(anom, anlg, GPOINTS, MM, MD, tClim, swClim, lwClim,
                pstarHaClim, rh15mClim, rainfallClim, snowfallClim,
                uwindClim, vwindClim, dtempClim, fWetClim,
                tAnom, swAnom, lwAnom, pstarHaAnom, rh15mAnom,
                precipAnom, uwindAnom, vwindAnom, dtempAnom,
                NSDMAX, stepDay, seedRain, SEC_DAY, lat, longG, MDI);
            tOut = clim_output.t_out;
            convRainOut = clim_output.conv_rain_out;
            convSnowOut = clim_output.conv_snow_out;
            lsRainOut = clim_output.ls_rain_out;
            lsSnowOut = clim_output.ls_snow_out;
            qhumOut = clim_output.qhum_out;
            windOut = clim_output.wind_out;
            pstarOut = clim_output.pstar_out;
            swOut = clim_output.sw_out;
            lwOut = clim_output.lw_out;
            dtempOut = clim_output.dtemp_out;
            seedRain = clim_output.seed_rain;
           

            // Carbon cycle update
            if (includeCo2 && cEmissions && anom && anlg) {
                emissTally = 0;
                for (n = 0; n < nyrEmiss; ++n) {
                    if (yrEmiss[n] == iyear) { //Check whether should be iyear-1? 
                        cEmissLocal = cEmiss[n];
                        co2Ppmv += CONV * cEmissLocal;
                        emissTally++;
                    }
                }
                if (emissTally != 1) {
                    std::cout << "Emission dataset does not match run. EMISS_TALLY is"<<emissTally<< "\n";
                    std::ofstream errFile(dirCommonOut + "/IMOGEN/output/" + thisYear + "/error");
                    errFile << "Emission dataset does not match run\n";
                    errFile.close();
                    return 1;
                }

                if (landFeed && lpjgCflux) {
                    emissTally = 0;
                    for (n = 0; n < nyrLpjgFlux; ++n) { 
                        if (yrLpjg[n] == iyear) {//Check whether should be iyear-1? 
                            cLpjgLocal = cLpjg[n];
                            dLandAtmos = CONV * cLpjgLocal;
                            co2Ppmv += dLandAtmos;
                            emissTally++;
                        }
                    }
                    if (emissTally != 1) {
                        std::cout << "LPJG C flux dataset does not match run. EMISS_TALLY is " << emissTally << "\n";
                        std::ofstream errFile(dirCommonOut + "/IMOGEN/output/" + thisYear + "/error");
                        errFile << "LPJG C flux dataset does not match run.\n";
                        errFile.close();
                        return 1;
                    }
                    if (nonco2Emissions) {
                        std::cout << "YR_LPJG_NONCO2(1) is " << yrLpjgNonco2[0] << "\n";
                        fair_non_co2_ghg_budget(iyear, nonco2EmissionsLpjg, yrLpjgNonco2,
                            nyrLpjgFlux, ch4Lpjg, n2oLpjg, yrEmiss,
                            nyrEmissNonco2, ch4Emiss, n2oEmiss,
                            ch4Ppbv, n2oPpbv, tauDecayCh4, tauDecayN2o,
                            dirCommon, thisYear);
                    }
                }
                else if (landFeed) {
                    std::cout << "WARNING: Land C uptake defaulting to 25% of emissions\n";
                    dLandAtmos = -CONV * 0.25 * cEmissLocal;
                    co2Ppmv += dLandAtmos;
                }

                if (oceanFeed) {
                    dtOcean = dtempO[0];
                    ocean_co2(iyear - year1Lpjg + 1, 1, co2Ppmv, IMOGENConfig::CO2_INIT_PPMV,
                        dtOcean, faOcean, OCEAN_AREA, co2ChangePpmv,
                        iyend - year1Lpjg + 1, tOceanInit, NFARRAY, dOceanAtmos);
                    co2Ppmv += dOceanAtmos;
                }
            }

            std::cout << "CO2 CHANGE PPV = " << co2ChangePpmv << "\n";
            if (includeCo2) co2ChangePpmv = co2Ppmv - co2LocalPpmv;


            // Write CO2 fluxes
            if (!spinup) {
                std::ofstream file91, file98;
                if (iyear == year1) {
                    file91.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/CO2.dat");
                    file98.open(dirCommonOut + "/IMOGEN/CO2_all.dat", std::ios::out | std::ios::app);
                }
                if (includeCo2 && cEmissions && anlg && anom && oceanFeed && landFeed) {
                    if (nonco2Emissions) {
                        file91 << iyear << " " << co2Ppmv << " " << CONV * cEmissLocal << " "
                            << dLandAtmos << " " << dOceanAtmos << " " << co2ChangePpmv << " "
                            << ch4Ppbv << " " << n2oPpbv << "\n";

                        file98 << iyear << " " << co2Ppmv << " " << CONV * cEmissLocal << " "
                            << dLandAtmos << " " << dOceanAtmos << " " << co2ChangePpmv << " "
                            << ch4Ppbv << " " << n2oPpbv << "\n";
                    }
                    else {
                        file91 << iyear << " " << co2Ppmv << " " << CONV * cEmissLocal << " "
                            << dLandAtmos << " " << dOceanAtmos << " " << co2ChangePpmv << "\n";
                        file98 << iyear << " " << co2Ppmv << " " << CONV * cEmissLocal << " "
                            << dLandAtmos << " " << dOceanAtmos << " " << co2ChangePpmv << "\n";
                    }
                }
                else {
                    if (nonco2Emissions) {
                        file91 << iyear << " " << co2Ppmv << " 0.0 0.0 0.0 0.0 " << ch4Ppbv << " " << n2oPpbv << "\n";
                        file98 << iyear << " " << co2Ppmv << " 0.0 0.0 0.0 0.0 " << ch4Ppbv << " " << n2oPpbv << "\n";
                    }
                    else {
                        file91 << iyear << " " << co2Ppmv << " 0.0 0.0 0.0 0.0\n";
                        file98 << iyear << " " << co2Ppmv << " 0.0 0.0 0.0 0.0\n";
                    }
                }
                file91.close();
                file98.close();
            }


            // Write climate anomalies
            if (anlg && anom && stepDay == 1 && mm == 12 && md == 30) {
                // Transfer output to 365-day year
                for (igp = 0; igp < GPOINTS; ++igp) {
                    for (imm = 0; imm < MM; ++imm) {
                        for (imd = 0; imd < 31; ++imd) {
                            if (imd < mthday[imm]) {
                                for (ind = 0; ind < stepDay; ++ind) {
                                    if (imd < 30) {
                                        tOutM[igp][imm][imd][ind] = tOut[igp][imm][imd][ind];
                                        swOutM[igp][imm][imd][ind] = swOut[igp][imm][imd][ind];
                                        windOutM[igp][imm][imd][ind] = windOut[igp][imm][imd][ind];//Added wind DKB
                                        rhOutM[igp][imm][imd][ind] = computeRelativeHumidityFromSpeificHumidty(qhumOut[igp][imm][imd][ind], pstarOut[igp][imm][imd][ind], tOut[igp][imm][imd][ind]); //Compute Rh from Qh since Rh is not output directly
                                        pOutM[igp][imm][imd][ind] = lsRainOut[igp][imm][imd][ind] +
                                            convRainOut[igp][imm][imd][ind] +
                                            lsSnowOut[igp][imm][imd][ind] +
                                            convSnowOut[igp][imm][imd][ind];
                                    }
                                    else {
                                        tOutM[igp][imm][imd][ind] = tOut[igp][imm][imd - 1][ind];
                                        swOutM[igp][imm][imd][ind] = swOut[igp][imm][imd - 1][ind];
                                        windOutM[igp][imm][imd][ind] = windOut[igp][imm][imd - 1][ind]; //wind DKB
                                        rhOutM[igp][imm][imd][ind] = computeRelativeHumidityFromSpeificHumidty(qhumOut[igp][imm][imd-1][ind], pstarOut[igp][imm][imd-1][ind], tOut[igp][imm][imd-1][ind]); //Compute Rh from Qh since Rh is not output directly
                                        pOutM[igp][imm][imd][ind] = lsRainOut[igp][imm][imd - 1][ind] +
                                            convRainOut[igp][imm][imd - 1][ind] +
                                            lsSnowOut[igp][imm][imd - 1][ind] +
                                            convSnowOut[igp][imm][imd - 1][ind];
                                    }
                                }
                                if (imd < 30) {
                                    dtempOutM[igp][imm][imd] = dtempOut[igp][imm][imd];
                                }
                                else {
                                    dtempOutM[igp][imm][imd] = dtempOut[igp][imm][imd - 1];
                                }
                            }
                            else {
                                for (ind = 0; ind < stepDay; ++ind) {
                                    tOutM[igp][imm][imd][ind] = mdi;
                                    pOutM[igp][imm][imd][ind] = mdi;
                                    swOutM[igp][imm][imd][ind] = mdi;
                                    windOutM[igp][imm][imd][ind] = mdi; //Wind
                                    rhOutM[igp][imm][imd][ind] = mdi; //Relative humidity
                                }
                                dtempOutM[igp][imm][imd] = mdi;
                            }
                        }
                        fWetClimOut[igp][imm] = static_cast<int>(fWetClim[igp][imm] * mthday[imm]);
                        if (fWetClimOut[igp][imm] == 0 &&
                            (rainfallClim[igp][imm] + snowfallClim[igp][imm] + precipAnom[igp][imm]) >= 0.0005) {
                            fWetClimOut[igp][imm] = 1;
                        }
                    }
                }

                // Output in native IMOGEN grid
                std::cout << "Writing native-grid anomalies for year: " << iyear << "\n";
                std::ofstream file92, file93, file94, file95, file11, file96, file97;

                if (iyear == year1) {
                    file92.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/T_anom.dat");
                    file93.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/P_anom.dat");
                    file94.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/SW_anom.dat");
                    file95.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/WET.dat");
                    file11.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/DTEMP_anom.dat");
                    file96.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/Rh_anom.dat");
                    file97.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/W_anom.dat");

                }
                for (igp = 0; igp < GPOINTS; ++igp) {
                    file92 << std::fixed << std::setw(8) << std::setprecision(3) << longG[igp] << " ";
                    file92 << std::fixed << std::setw(8) << std::setprecision(3) << lat[igp] << " ";
                    file93 << std::fixed << std::setw(8) << std::setprecision(3) << longG[igp] << " ";
                    file93 << std::fixed << std::setw(8) << std::setprecision(3) << lat[igp] << " ";
                    file94 << std::fixed << std::setw(8) << std::setprecision(3) << longG[igp] << " ";
                    file94 << std::fixed << std::setw(8) << std::setprecision(3) << lat[igp] << " ";
                    file95 << std::fixed << std::setw(8) << std::setprecision(3) << longG[igp] << " ";
                    file95 << std::fixed << std::setw(8) << std::setprecision(3) << lat[igp] << " ";
                    file11 << std::fixed << std::setw(8) << std::setprecision(3) << longG[igp] << " ";
                    file11 << std::fixed << std::setw(8) << std::setprecision(3) << lat[igp] << " ";
                    file96 << std::fixed << std::setw(8) << std::setprecision(3) << longG[igp] << " ";
                    file96 << std::fixed << std::setw(8) << std::setprecision(3) << lat[igp] << " ";
                    file97 << std::fixed << std::setw(8) << std::setprecision(3) << longG[igp] << " ";
                    file97 << std::fixed << std::setw(8) << std::setprecision(3) << lat[igp] << " ";

                    for (imm = 0; imm < MM; ++imm) {
                        if (dailyOut) {
                            for (imd = 0; imd < 31; ++imd) {
                                if (imd < mthday[imm]) {
                                    for (ind = 0; ind < stepDay; ++ind) {
                                        file92 << std::fixed << std::setw(10) << std::setprecision(3) << tOutM[igp][imm][imd][ind] << " ";
                                        file93 << std::fixed << std::setw(10) << std::setprecision(3) << pOutM[igp][imm][imd][ind] << " ";
                                        file94 << std::fixed << std::setw(10) << std::setprecision(3) << swOutM[igp][imm][imd][ind] << " ";
                                        file97 << std::fixed << std::setw(10) << std::setprecision(3) << windOutM[igp][imm][imd][ind] << " ";//DKB Wind
                                        file96 << std::fixed << std::setw(10) << std::setprecision(3) << rhOutM[igp][imm][imd][ind] << " ";//DKB Rh
                                        file11 << std::fixed << std::setw(10) << std::setprecision(3) << dtempOutM[igp][imm][imd] << " ";
                                        file95 << std::setw(10) << fWetClimOut[igp][imm] << " ";
                                    }
                                }
                            }
                        }
                        else {
                            file92 << std::fixed << std::setw(10) << std::setprecision(3) << tOutM[igp][imm][0][0] << " ";
                            file93 << std::fixed << std::setw(10) << std::setprecision(3) << pOutM[igp][imm][0][0] << " ";
                            file94 << std::fixed << std::setw(10) << std::setprecision(3) << swOutM[igp][imm][0][0] << " ";
                            file97 << std::fixed << std::setw(10) << std::setprecision(3) << windOutM[igp][imm][0][0] << " "; //DKB
                            file96 << std::fixed << std::setw(10) << std::setprecision(3) << rhOutM[igp][imm][0][0] << " "; //DKB
                            file11 << std::fixed << std::setw(10) << std::setprecision(3) << dtempOutM[igp][imm][0] << " ";
                            file95 << std::setw(10) << fWetClimOut[igp][imm] << " ";
                        }
                    }
                    file92 << "\n";
                    file93 << "\n";
                    file94 << "\n";
                    file95 << "\n";
                    file96 << "\n";
                    file97 << "\n";
                    file11 << "\n";
                }

                if (iyear == iyend) {
                    file92.close();
                    file93.close();
                    file94.close();
                    file95.close();
                    file96.close();
                    file97.close();
                    file11.close();
                }

                // Write done file for LPJ-GUESS
                {
                    std::ofstream file97(dirCommonOut + "/IMOGEN/output/" + thisYear + "/done");
                    file97 << "Climate files written\n";
                    file97.close();
                }
            }



            // Write FA_OCEAN and DTEMP_O for restart
            if (oceanFeed) {
                std::ofstream file95, file96;
                if (iyear == year1) {
                    file95.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/fa_ocean.dat");
                    file96.open(dirCommonOut + "/IMOGEN/output/" + thisYear + "/dtemp_o.dat");
                }
                for (igp = 0; igp < NFARRAY; ++igp) {
                    file95 << faOcean[igp] << "\n";
                }
                for (igp = 0; igp < N_OLEVS; ++igp) {
                    file96 << dtempO[igp] << "\n";
                }
                if (iyear == iyend) {
                    file95.close();
                    file96.close();
                }
            }

            updateImogenControlData(); //manual ctrl data update
        }

    } // End of IYEAR loop

    return 0;
} // End of KEEPRUNNING loop


void updateImogenControlData() {
    IMOGENConfig::YEAR1++;
    IMOGENConfig::IYEND++;

    if (IMOGENConfig::YEAR1 == 1901) {
        IMOGENConfig::SPINUP=false;
    }

    if (IMOGENConfig::YEAR1 == 2100) {
        IMOGENConfig::KEEPRUNNING = false;
    }

    if (IMOGENConfig::IYEND > 1900) {
        IMOGENConfig::FIRSTCALL = false;
    }

    IMOGENConfig::YEAR1_LPJG = 1871;

}

//Write test flux data
void writeFluxData() {
    // Open files for writing (overwrite mode)
    std::ofstream file121(IMOGENConfig::DIR_COMMON + "/LPJG_main/IMOGEN/" + IMOGENConfig::FILE_LPJG_CH4_N2O_FLUX);
    std::ofstream file122(IMOGENConfig::DIR_COMMON + "/LPJG_main/IMOGEN/" + IMOGENConfig::FILE_LPJG_FLUX);

    if (file121.is_open() && file122.is_open()) {

        if (IMOGENConfig::SPINUP) {
            file121 << IMOGENConfig::YEAR1 << "\t" << "0.00" << "\t" << "0.00" << "\n";
        }
        else {
            file121 << IMOGENConfig::YEAR1 << "\t" << "202" << "\t" << "9.1" << "\n";
        }

        file122 << IMOGENConfig::YEAR1 << "\t" << "0.00" << "\n";

        //throw std::runtime_error("Unable to open LPJG CH4/N2O flux file or C flux file");
    }
    else {
        //do nothing for now
    }

}



double computeRelativeHumidityFromSpeificHumidty(double q, double p_Pa, double T_Kelvin) {
    // Convert temperature from Kelvin to Celsius
    double T_Celsius = T_Kelvin - 273.15;

    // Convert pressure from Pa to hPa
    double p_hPa = p_Pa / 100.0;

    // Step 1: Compute vapor pressure (e) in hPa
    double e = (q * p_hPa) / (0.622 + 0.378 * q);

    // Step 2: Compute saturation vapor pressure (es) using Tetens formula
    double es = 6.112 * std::exp((17.67 * T_Celsius) / (T_Celsius + 243.5));

    // Step 3: Compute relative humidity
    double RH = (e / es) * 100.0;

    // Clamp RH to [0, 100] for physical validity
    if (RH < 0.0) RH = 0.0;
    if (RH > 100.0) RH = 100.0;

    return RH;



    //double calc_relative_humidity(double temp, double specific_humidity, double pressure) {

    //    // qair  specific humidity, dimensionless (e.g. kg/kg) 
    //    // temp  temperature in degrees C
    //    // press pressure in Pa
    //    // rh    relative humidity in frac.
    ////	if ( pressure < 10000 ) {
    ////		fail("Unit for pressure must be [Pa]: calc_relative_humidity(cfinput.cpp) year=%d Pa=%f", date.get_calendar_year(), pressure);
    ////	}
    ////	if ( temp  > 80. ) {
    ////		fail("Unit for temperature must be [deg C]: calc_relative_humidity(cfinput.cpp)");
    ////	}
    ////	double pres_hPa = pressure / 100.; // convert to hPa

    //    double pres_hPa = (pressure > 10000) ? pressure / 100.0 : pressure; // might need to change from Pa to hPa

    //    if (temp > 80.0) // need to change from K to degC
    //        temp = temp - 273.15;

    //    // saturation water-vapour pressure following August-Roche-Magnus Formula
    //    double es = 6.112 * exp(17.67 * temp / (temp + 243.5));

    //    // water-vapour pressure
    //    // derived from approximation for s = rho_w/(rho_dryAir - rho_w)    
    //    double e = specific_humidity * pres_hPa / (0.378 * specific_humidity + 0.622);
    //    double rh = min(max(e / es, 0.), 1.);
    //    return rh;
    //}





}



/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//ACTUAL FUNCTION DECLARATIONS
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


/**
 * Calculates the radiative forcing due to a given CO2 concentration.
 *
 * @param co2 Current CO2 concentration (ppmv).
 * @param co2ref Reference CO2 concentration (ppmv).
 * @param q2co2 Radiative forcing due to doubling CO2 (W/m^2).
 * @return Radiative forcing due to CO2 (W/m^2).
 * @throws std::invalid_argument If co2 or co2ref is non-positive.
 *
 * Written by Peter Cox (August 1998), converted to C++ in 2025.
 */
double radf_co2(double co2, double co2ref, double q2co2) {
    if (co2 <= 0.0 || co2ref <= 0.0) {
        throw std::invalid_argument("CO2 and CO2REF must be positive");
    }

    return q2co2 * std::log(co2 / co2ref) / std::log(2.0);
}


/**
 * Calculates the radiative forcing due to non-CO2 greenhouse gases.
 * Consistent with the HadCM3 GHG run (AAXZE).
 *
 * @param year Julian year.
 * @param nyr_non_co2 Number of years for which non-CO2 forcing is prescribed.
 * @param file_non_co2 True if non-CO2 forcings are read from a file.
 * @param file_non_co2_vals File path containing non-CO2 radiative forcings.
 * @return Non-CO2 radiative forcing (W/m^2).
 * @throws std::runtime_error If nyr_non_co2 is invalid or file operations fail.
 *
 * Written by Peter Cox (Sept 1998), adjusted by Chris Huntingford (Dec 1999),
 * converted to C++ in 2025.
 */
double radf_non_co2(int year, int nyr_non_co2, bool file_non_co2, const std::string& file_non_co2_vals) {
    // Local parameters
    constexpr double growth_rate = 0.0;
    constexpr size_t max_years = 300;

    // Validate inputs
    if (!file_non_co2 && nyr_non_co2 != 21) {
        throw std::runtime_error("NYR_NON_CO2 must be 21 when FILE_NON_CO2 is false");
    }
    if (nyr_non_co2 > static_cast<int>(max_years)) {
        throw std::runtime_error("NYR_NON_CO2 exceeds maximum of 300");
    }
    if (nyr_non_co2 <= 0) {
        throw std::runtime_error("NYR_NON_CO2 must be positive");
    }

    // Initialize default data (equivalent to Fortran DATA statements)
    std::vector<int> years = {
        1859, 1875, 1890, 1900, 1917,
        1935, 1950, 1960, 1970, 1980,
        1990, 2005, 2020, 2030, 2040,
        2050, 2060, 2070, 2080, 2090,
        2100
    };
    years.resize(max_years, 2100); // Fill remaining with 2100

    std::vector<double> q_non_co2 = {
        0.0344, 0.0557, 0.0754, 0.0912, 0.1176,
        0.1483, 0.1831, 0.2387, 0.3480, 0.4987,
        0.6627, 0.8430, 0.9225, 0.9763, 1.0575,
        1.1486, 1.2316, 1.3025, 1.3604, 1.4102,
        1.4602
    };
    q_non_co2.resize(max_years, 1.4602); // Fill remaining with 1.4602

    // Read non-CO2 forcings from file if required
    if (file_non_co2) {
        std::ifstream file(file_non_co2_vals);
        if (!file.is_open()) {
            throw std::runtime_error("Unable to open file: " + file_non_co2_vals);
        }
        for (int i = 0; i < nyr_non_co2; ++i) {
            if (file >> years[i] >> q_non_co2[i]) {
                // Successfully read year and forcing
            }
            else {
                file.close();
                throw std::runtime_error("Invalid data format in file: " + file_non_co2_vals);
            }
        }
        file.close();
    }

    // Calculate non-CO2 forcing
    if (year < years[0]) {
        return 0.0; // Before first year, forcing is zero
    }
    else if (year > years[nyr_non_co2 - 1]) {
        // After last year, apply growth rate
        int delta_years = year - years[nyr_non_co2 - 1];
        return q_non_co2[nyr_non_co2 - 1] * std::pow(1.0 + 0.01 * growth_rate, delta_years);
    }
    else {
        // Interpolate between years
        for (int i = 0; i < nyr_non_co2 - 1; ++i) {
            if (year >= years[i] && year <= years[i + 1]) {
                double slope = (q_non_co2[i + 1] - q_non_co2[i]) / (years[i + 1] - years[i]);
                return q_non_co2[i] + (year - years[i]) * slope;
            }
        }
    }

    // Should not reach here if logic is correct
    throw std::runtime_error("Error in non-CO2 forcing calculation for year: " + std::to_string(year));
}


/**
 * Calculates saturation mixing ratio at given temperatures and pressures.
 *
 * Uses a lookup table of saturation water vapor pressures based on the
 * Goff-Gratch formulae, with values over water above 0°C and over ice below 0°C.
 *
 * @param qs Output saturation mixing ratio (kg/kg).
 * @param t Input temperature (K).
 * @param p Input pressure (Pa).
 * @param npnts Number of points.
 * @throws std::runtime_error If inputs are invalid (npnts <= 0, mismatched array sizes, or p[i] <= 0).
 *
 * Written by DLR, converted to C++ in 2025.
 */
void qsat(std::vector<double>& qs, const std::vector<double>& t,
    const std::vector<double>& p, int npnts) {

    // Write qs, t, and p to a file
    std::ofstream outfile("qsat_output.txt");
    if (!outfile.is_open()) {
        throw std::runtime_error("Failed to open output file");
    }

    outfile << "Index\tQS\tT(K)\tP(Pa)\n";
    for (int i = 0; i < npnts; ++i) {
        outfile << i << "\t" << qs[i] << "\t" << t[i] << "\t" << p[i] << "\n";
    }
    outfile.close();

    // Validate inputs
    if (npnts <= 0) {
        throw std::runtime_error("npnts must be positive");
    }

    if (qs.size() != static_cast<size_t>(npnts) ||
        t.size() != static_cast<size_t>(npnts) ||
        p.size() != static_cast<size_t>(npnts)) {
        throw std::runtime_error("Array sizes must match npnts");
    }
   // std::cout << "P Size: " << p.size() << " " << "Npoints: " << npnts << std::endl;

    for (int i = 0; i < npnts; ++i) {
        if (p[i] <= 0.0) {
            //throw std::runtime_error("Pressure must be positive");
            //std::cout << p[i] << std::endl;
            //do nothing for now cos native IMOGEN allows negative pressures
        }
    }


    // Model constants
    constexpr double epsilon = 0.62198; // Ratio of molecular weights of water and dry air
    constexpr double one_minus_epsilon = 1.0 - epsilon;
    constexpr double zerodegc = 273.15; // Kelvin-Celsius conversion

    // Lookup table constants
    constexpr double t_low = 183.15; // Lowest temperature for table (K)
    constexpr double t_high = 338.15; // Highest temperature for table (K)
    constexpr double delta_t = 0.1; // Temperature increment (K)
    constexpr int n = static_cast<int>(((t_high - t_low + (delta_t * 0.5)) / delta_t) + 1.0); // 1551

    // Saturation vapor pressure table (Pa)
    // Placeholder: Insert 1553 elements from Fortran DATA statements
    std::vector<float> es = {
    0.966483E-02,
    0.966483E-02,0.984279E-02,0.100240E-01,0.102082E-01,0.103957E-01,
      0.105865E-01,0.107803E-01,0.109777E-01,0.111784E-01,0.113825E-01,
      0.115902E-01,0.118016E-01,0.120164E-01,0.122348E-01,0.124572E-01,
     0.126831E-01,0.129132E-01,0.131470E-01,0.133846E-01,0.136264E-01,
     0.138724E-01,0.141225E-01,0.143771E-01,0.146356E-01,0.148985E-01,
     0.151661E-01,0.154379E-01,0.157145E-01,0.159958E-01,0.162817E-01,
     0.165725E-01,0.168680E-01,0.171684E-01,0.174742E-01,0.177847E-01,
     0.181008E-01,0.184216E-01,0.187481E-01,0.190801E-01,0.194175E-01,
     0.197608E-01,0.201094E-01,0.204637E-01,0.208242E-01,0.211906E-01,
     0.215631E-01,0.219416E-01,0.223263E-01,0.227172E-01,0.231146E-01,
     0.235188E-01,0.239296E-01,0.243465E-01,0.247708E-01,0.252019E-01,
     0.256405E-01,0.260857E-01,0.265385E-01,0.269979E-01,0.274656E-01,
     0.279405E-01,0.284232E-01,0.289142E-01,0.294124E-01,0.299192E-01,
      0.304341E-01,0.309571E-01,0.314886E-01,0.320285E-01,0.325769E-01,
     0.331348E-01,0.337014E-01,0.342771E-01,0.348618E-01,0.354557E-01,
      0.360598E-01,0.366727E-01,0.372958E-01,0.379289E-01,0.385717E-01,
     0.392248E-01,0.398889E-01,0.405633E-01,0.412474E-01,0.419430E-01,
      0.426505E-01,0.433678E-01,0.440974E-01,0.448374E-01,0.455896E-01,
      0.463545E-01,0.471303E-01,0.479191E-01,0.487190E-01,0.495322E-01,
     0.503591E-01,0.511977E-01,0.520490E-01,0.529145E-01,0.537931E-01,
      0.546854E-01,0.555924E-01,0.565119E-01,0.574467E-01,0.583959E-01,
      0.593592E-01,0.603387E-01,0.613316E-01,0.623409E-01,0.633655E-01,
      0.644053E-01,0.654624E-01,0.665358E-01,0.676233E-01,0.687302E-01,
      0.698524E-01,0.709929E-01,0.721490E-01,0.733238E-01,0.745180E-01,
      0.757281E-01,0.769578E-01,0.782061E-01,0.794728E-01,0.807583E-01,
      0.820647E-01,0.833905E-01,0.847358E-01,0.861028E-01,0.874882E-01,
      0.888957E-01,0.903243E-01,0.917736E-01,0.932464E-01,0.947407E-01,
      0.962571E-01,0.977955E-01,0.993584E-01,0.100942E+00,0.102551E+00,
      0.104186E+00,0.105842E+00,0.107524E+00,0.109231E+00,0.110963E+00,
      0.112722E+00,0.114506E+00,0.116317E+00,0.118153E+00,0.120019E+00,
      0.121911E+00,0.123831E+00,0.125778E+00,0.127755E+00,0.129761E+00,
      0.131796E+00,0.133863E+00,0.135956E+00,0.138082E+00,0.140241E+00,
      0.142428E+00,0.144649E+00,0.146902E+00,0.149190E+00,0.151506E+00,
      0.153859E+00,0.156245E+00,0.158669E+00,0.161126E+00,0.163618E+00,
      0.166145E+00,0.168711E+00,0.171313E+00,0.173951E+00,0.176626E+00,
      0.179342E+00,0.182096E+00,0.184893E+00,0.187724E+00,0.190600E+00,
      0.193518E+00,0.196473E+00,0.199474E+00,0.202516E+00,0.205604E+00,
      0.208730E+00,0.211905E+00,0.215127E+00,0.218389E+00,0.221701E+00 ,
     0.225063E+00,0.228466E+00,0.231920E+00,0.235421E+00,0.238976E+00,
      0.242580E+00,0.246232E+00,0.249933E+00,0.253691E+00,0.257499E+00,
     0.261359E+00,0.265278E+00,0.269249E+00,0.273274E+00,0.277358E+00,
      0.281498E+00,0.285694E+00,0.289952E+00,0.294268E+00,0.298641E+00,
      0.303078E+00,0.307577E+00,0.312135E+00,0.316753E+00,0.321440E+00,
      0.326196E+00,0.331009E+00,0.335893E+00,0.340842E+00,0.345863E+00,
      0.350951E+00,0.356106E+00,0.361337E+00,0.366636E+00,0.372006E+00,
     0.377447E+00,0.382966E+00,0.388567E+00,0.394233E+00,0.399981E+00,
     0.405806E+00,0.411714E+00,0.417699E+00,0.423772E+00,0.429914E+00,
      0.436145E+00,0.442468E+00,0.448862E+00,0.455359E+00,0.461930E+00,
      0.468596E+00,0.475348E+00,0.482186E+00,0.489124E+00,0.496160E+00,
      0.503278E+00,0.510497E+00,0.517808E+00,0.525224E+00,0.532737E+00,
      0.540355E+00,0.548059E+00,0.555886E+00,0.563797E+00,0.571825E+00,
      0.579952E+00,0.588198E+00,0.596545E+00,0.605000E+00,0.613572E+00,
      0.622255E+00,0.631059E+00,0.639962E+00,0.649003E+00,0.658144E+00,
      0.667414E+00,0.676815E+00,0.686317E+00,0.695956E+00,0.705728E+00,
      0.715622E+00,0.725641E+00,0.735799E+00,0.746082E+00,0.756495E+00,
      0.767052E+00,0.777741E+00,0.788576E+00,0.799549E+00,0.810656E+00,
      0.821914E+00,0.833314E+00,0.844854E+00,0.856555E+00,0.868415E+00,
     0.880404E+00,0.892575E+00,0.904877E+00,0.917350E+00,0.929974E+00,
      0.942771E+00,0.955724E+00,0.968837E+00,0.982127E+00,0.995600E+00,
      0.100921E+01,0.102304E+01,0.103700E+01,0.105116E+01,0.106549E+01,
      0.108002E+01,0.109471E+01,0.110962E+01,0.112469E+01,0.113995E+01,
      0.115542E+01,0.117107E+01,0.118693E+01,0.120298E+01,0.121923E+01,
      0.123569E+01,0.125234E+01,0.126923E+01,0.128631E+01,0.130362E+01,
      0.132114E+01,0.133887E+01,0.135683E+01,0.137500E+01,0.139342E+01,
      0.141205E+01,0.143091E+01,0.145000E+01,0.146933E+01,0.148892E+01,
     0.150874E+01,0.152881E+01,0.154912E+01,0.156970E+01,0.159049E+01,
     0.161159E+01,0.163293E+01,0.165452E+01,0.167640E+01,0.169852E+01,
     0.172091E+01,0.174359E+01,0.176653E+01,0.178977E+01,0.181332E+01,
     0.183709E+01,0.186119E+01,0.188559E+01,0.191028E+01,0.193524E+01,
     0.196054E+01,0.198616E+01,0.201208E+01,0.203829E+01,0.206485E+01,
     0.209170E+01,0.211885E+01,0.214637E+01,0.217424E+01,0.220242E+01,
      0.223092E+01,0.225979E+01,0.228899E+01,0.231855E+01,0.234845E+01,
      0.237874E+01,0.240937E+01,0.244040E+01,0.247176E+01,0.250349E+01,
      0.253560E+01,0.256814E+01,0.260099E+01,0.263431E+01,0.266800E+01,
      0.270207E+01,0.273656E+01,0.277145E+01,0.280671E+01,0.284248E+01,
      0.287859E+01,0.291516E+01,0.295219E+01,0.298962E+01,0.302746E+01,
     0.306579E+01,0.310454E+01,0.314377E+01,0.318351E+01,0.322360E+01,
      0.326427E+01,0.330538E+01,0.334694E+01,0.338894E+01,0.343155E+01,
      0.347456E+01,0.351809E+01,0.356216E+01,0.360673E+01,0.365184E+01,
      0.369744E+01,0.374352E+01,0.379018E+01,0.383743E+01,0.388518E+01,
      0.393344E+01,0.398230E+01,0.403177E+01,0.408175E+01,0.413229E+01,
      0.418343E+01,0.423514E+01,0.428746E+01,0.434034E+01,0.439389E+01,
      0.444808E+01,0.450276E+01,0.455820E+01,0.461423E+01,0.467084E+01,
      0.472816E+01,0.478607E+01,0.484468E+01,0.490393E+01,0.496389E+01,
      0.502446E+01,0.508580E+01,0.514776E+01,0.521047E+01,0.527385E+01,
      0.533798E+01,0.540279E+01,0.546838E+01,0.553466E+01,0.560173E+01,
      0.566949E+01,0.573807E+01,0.580750E+01,0.587749E+01,0.594846E+01,
      0.602017E+01,0.609260E+01,0.616591E+01,0.623995E+01,0.631490E+01,
      0.639061E+01,0.646723E+01,0.654477E+01,0.662293E+01,0.670220E+01,
      0.678227E+01,0.686313E+01,0.694495E+01,0.702777E+01,0.711142E+01,
      0.719592E+01,0.728140E+01,0.736790E+01,0.745527E+01,0.754352E+01,
      0.763298E+01,0.772316E+01,0.781442E+01,0.790676E+01,0.800001E+01,
      0.809435E+01,0.818967E+01,0.828606E+01,0.838343E+01,0.848194E+01,
      0.858144E+01,0.868207E+01,0.878392E+01,0.888673E+01,0.899060E+01,
      0.909567E+01,0.920172E+01,0.930909E+01,0.941765E+01,0.952730E+01,
     0.963821E+01,0.975022E+01,0.986352E+01,0.997793E+01,0.100937E+02,
      0.102105E+02,0.103287E+02,0.104481E+02,0.105688E+02,0.106909E+02,
      0.108143E+02,0.109387E+02,0.110647E+02,0.111921E+02,0.113207E+02,
      0.114508E+02,0.115821E+02,0.117149E+02,0.118490E+02,0.119847E+02,
      0.121216E+02,0.122601E+02,0.124002E+02,0.125416E+02,0.126846E+02,
      0.128290E+02,0.129747E+02,0.131224E+02,0.132712E+02,0.134220E+02,
      0.135742E+02,0.137278E+02,0.138831E+02,0.140403E+02,0.141989E+02,
      0.143589E+02,0.145211E+02,0.146845E+02,0.148501E+02,0.150172E+02,
      0.151858E+02,0.153564E+02,0.155288E+02,0.157029E+02,0.158786E+02,
      0.160562E+02,0.162358E+02,0.164174E+02,0.166004E+02,0.167858E+02,
      0.169728E+02,0.171620E+02,0.173528E+02,0.175455E+02,0.177406E+02,
      0.179372E+02,0.181363E+02,0.183372E+02,0.185400E+02,0.187453E+02,
      0.189523E+02,0.191613E+02,0.193728E+02,0.195866E+02,0.198024E+02,
      0.200200E+02,0.202401E+02,0.204626E+02,0.206871E+02,0.209140E+02,
      0.211430E+02,0.213744E+02,0.216085E+02,0.218446E+02,0.220828E+02,
      0.223241E+02,0.225671E+02,0.228132E+02,0.230615E+02,0.233120E+02,
      0.235651E+02,0.238211E+02,0.240794E+02,0.243404E+02,0.246042E+02,
      0.248704E+02,0.251390E+02,0.254109E+02,0.256847E+02,0.259620E+02,
      0.262418E+02,0.265240E+02,0.268092E+02,0.270975E+02,0.273883E+02,
     0.276822E+02,0.279792E+02,0.282789E+02,0.285812E+02,0.288867E+02,
      0.291954E+02,0.295075E+02,0.298222E+02,0.301398E+02,0.304606E+02,
      0.307848E+02,0.311119E+02,0.314424E+02,0.317763E+02,0.321133E+02,
      0.324536E+02,0.327971E+02,0.331440E+02,0.334940E+02,0.338475E+02,
      0.342050E+02,0.345654E+02,0.349295E+02,0.352975E+02,0.356687E+02,
      0.360430E+02,0.364221E+02,0.368042E+02,0.371896E+02,0.375790E+02,
      0.379725E+02,0.383692E+02,0.387702E+02,0.391744E+02,0.395839E+02,
      0.399958E+02,0.404118E+02,0.408325E+02,0.412574E+02,0.416858E+02,
      0.421188E+02,0.425551E+02,0.429962E+02,0.434407E+02,0.438910E+02,
      0.443439E+02,0.448024E+02,0.452648E+02,0.457308E+02,0.462018E+02,
      0.466775E+02,0.471582E+02,0.476428E+02,0.481313E+02,0.486249E+02,
      0.491235E+02,0.496272E+02,0.501349E+02,0.506479E+02,0.511652E+02,
      0.516876E+02,0.522142E+02,0.527474E+02,0.532836E+02,0.538266E+02,
      0.543737E+02,0.549254E+02,0.554839E+02,0.560456E+02,0.566142E+02,
      0.571872E+02,0.577662E+02,0.583498E+02,0.589392E+02,0.595347E+02,
      0.601346E+02,0.607410E+02,0.613519E+02,0.619689E+02,0.625922E+02,
      0.632204E+02,0.638550E+02,0.644959E+02,0.651418E+02,0.657942E+02,
      0.664516E+02,0.671158E+02,0.677864E+02,0.684624E+02,0.691451E+02,
      0.698345E+02,0.705293E+02,0.712312E+02,0.719398E+02,0.726542E+02,
     0.733754E+02,0.741022E+02,0.748363E+02,0.755777E+02,0.763247E+02,
      0.770791E+02,0.778394E+02,0.786088E+02,0.793824E+02,0.801653E+02,
      0.809542E+02,0.817509E+02,0.825536E+02,0.833643E+02,0.841828E+02,
      0.850076E+02,0.858405E+02,0.866797E+02,0.875289E+02,0.883827E+02,
      0.892467E+02,0.901172E+02,0.909962E+02,0.918818E+02,0.927760E+02,
      0.936790E+02,0.945887E+02,0.955071E+02,0.964346E+02,0.973689E+02,
      0.983123E+02,0.992648E+02,0.100224E+03,0.101193E+03,0.102169E+03,
      0.103155E+03,0.104150E+03,0.105152E+03,0.106164E+03,0.107186E+03,
      0.108217E+03,0.109256E+03,0.110303E+03,0.111362E+03,0.112429E+03,
      0.113503E+03,0.114588E+03,0.115684E+03,0.116789E+03,0.117903E+03,
      0.119028E+03,0.120160E+03,0.121306E+03,0.122460E+03,0.123623E+03,
      0.124796E+03,0.125981E+03,0.127174E+03,0.128381E+03,0.129594E+03,
      0.130822E+03,0.132058E+03,0.133306E+03,0.134563E+03,0.135828E+03,
      0.137109E+03,0.138402E+03,0.139700E+03,0.141017E+03,0.142338E+03,
      0.143676E+03,0.145025E+03,0.146382E+03,0.147753E+03,0.149133E+03,
      0.150529E+03,0.151935E+03,0.153351E+03,0.154783E+03,0.156222E+03,
      0.157678E+03,0.159148E+03,0.160624E+03,0.162117E+03,0.163621E+03,
      0.165142E+03,0.166674E+03,0.168212E+03,0.169772E+03,0.171340E+03,
      0.172921E+03,0.174522E+03,0.176129E+03,0.177755E+03,0.179388E+03,
     0.181040E+03,0.182707E+03,0.184382E+03,0.186076E+03,0.187782E+03,
      0.189503E+03,0.191240E+03,0.192989E+03,0.194758E+03,0.196535E+03,
      0.198332E+03,0.200141E+03,0.201963E+03,0.203805E+03,0.205656E+03,
      0.207532E+03,0.209416E+03,0.211317E+03,0.213236E+03,0.215167E+03,
      0.217121E+03,0.219087E+03,0.221067E+03,0.223064E+03,0.225080E+03,
      0.227113E+03,0.229160E+03,0.231221E+03,0.233305E+03,0.235403E+03,
      0.237520E+03,0.239655E+03,0.241805E+03,0.243979E+03,0.246163E+03,
      0.248365E+03,0.250593E+03,0.252830E+03,0.255093E+03,0.257364E+03,
      0.259667E+03,0.261979E+03,0.264312E+03,0.266666E+03,0.269034E+03,
      0.271430E+03,0.273841E+03,0.276268E+03,0.278722E+03,0.281185E+03,
      0.283677E+03,0.286190E+03,0.288714E+03,0.291266E+03,0.293834E+03,
      0.296431E+03,0.299045E+03,0.301676E+03,0.304329E+03,0.307006E+03,
      0.309706E+03,0.312423E+03,0.315165E+03,0.317930E+03,0.320705E+03,
      0.323519E+03,0.326350E+03,0.329199E+03,0.332073E+03,0.334973E+03,
      0.337897E+03,0.340839E+03,0.343800E+03,0.346794E+03,0.349806E+03,
      0.352845E+03,0.355918E+03,0.358994E+03,0.362112E+03,0.365242E+03,
      0.368407E+03,0.371599E+03,0.374802E+03,0.378042E+03,0.381293E+03,
      0.384588E+03,0.387904E+03,0.391239E+03,0.394604E+03,0.397988E+03,
      0.401411E+03,0.404862E+03,0.408326E+03,0.411829E+03,0.415352E+03,
     0.418906E+03,0.422490E+03,0.426095E+03,0.429740E+03,0.433398E+03,
      0.437097E+03,0.440827E+03,0.444570E+03,0.448354E+03,0.452160E+03,
      0.455999E+03,0.459870E+03,0.463765E+03,0.467702E+03,0.471652E+03,
      0.475646E+03,0.479674E+03,0.483715E+03,0.487811E+03,0.491911E+03,
      0.496065E+03,0.500244E+03,0.504448E+03,0.508698E+03,0.512961E+03,
      0.517282E+03,0.521617E+03,0.525989E+03,0.530397E+03,0.534831E+03,
      0.539313E+03,0.543821E+03,0.548355E+03,0.552938E+03,0.557549E+03,
      0.562197E+03,0.566884E+03,0.571598E+03,0.576351E+03,0.581131E+03,
      0.585963E+03,0.590835E+03,0.595722E+03,0.600663E+03,0.605631E+03,
      0.610641E+03,0.615151E+03,0.619625E+03,0.624140E+03,0.628671E+03,
      0.633243E+03,0.637845E+03,0.642465E+03,0.647126E+03,0.651806E+03,
      0.656527E+03,0.661279E+03,0.666049E+03,0.670861E+03,0.675692E+03,
      0.680566E+03,0.685471E+03,0.690396E+03,0.695363E+03,0.700350E+03,
      0.705381E+03,0.710444E+03,0.715527E+03,0.720654E+03,0.725801E+03,
      0.730994E+03,0.736219E+03,0.741465E+03,0.746756E+03,0.752068E+03,
      0.757426E+03,0.762819E+03,0.768231E+03,0.773692E+03,0.779172E+03,
      0.784701E+03,0.790265E+03,0.795849E+03,0.801483E+03,0.807137E+03,
      0.812842E+03,0.818582E+03,0.824343E+03,0.830153E+03,0.835987E+03,
      0.841871E+03,0.847791E+03,0.853733E+03,0.859727E+03,0.865743E+03,
     0.871812E+03,0.877918E+03,0.884046E+03,0.890228E+03,0.896433E+03,
      0.902690E+03,0.908987E+03,0.915307E+03,0.921681E+03,0.928078E+03,
      0.934531E+03,0.941023E+03,0.947539E+03,0.954112E+03,0.960708E+03,
      0.967361E+03,0.974053E+03,0.980771E+03,0.987545E+03,0.994345E+03,
      0.100120E+04,0.100810E+04,0.101502E+04,0.102201E+04,0.102902E+04,
      0.103608E+04,0.104320E+04,0.105033E+04,0.105753E+04,0.106475E+04,
      0.107204E+04,0.107936E+04,0.108672E+04,0.109414E+04,0.110158E+04,
      0.110908E+04,0.111663E+04,0.112421E+04,0.113185E+04,0.113952E+04,
      0.114725E+04,0.115503E+04,0.116284E+04,0.117071E+04,0.117861E+04,
      0.118658E+04,0.119459E+04,0.120264E+04,0.121074E+04,0.121888E+04,
      0.122709E+04,0.123534E+04,0.124362E+04,0.125198E+04,0.126036E+04,
      0.126881E+04,0.127731E+04,0.128584E+04,0.129444E+04,0.130307E+04,
      0.131177E+04,0.132053E+04,0.132931E+04,0.133817E+04,0.134705E+04,
      0.135602E+04,0.136503E+04,0.137407E+04,0.138319E+04,0.139234E+04,
      0.140156E+04,0.141084E+04,0.142015E+04,0.142954E+04,0.143896E+04,
      0.144845E+04,0.145800E+04,0.146759E+04,0.147725E+04,0.148694E+04,
      0.149672E+04,0.150655E+04,0.151641E+04,0.152635E+04,0.153633E+04,
      0.154639E+04,0.155650E+04,0.156665E+04,0.157688E+04,0.158715E+04,
      0.159750E+04,0.160791E+04,0.161836E+04,0.162888E+04,0.163945E+04,
     0.165010E+04,0.166081E+04,0.167155E+04,0.168238E+04,0.169325E+04,
      0.170420E+04,0.171522E+04,0.172627E+04,0.173741E+04,0.174859E+04,
      0.175986E+04,0.177119E+04,0.178256E+04,0.179402E+04,0.180552E+04,
      0.181711E+04,0.182877E+04,0.184046E+04,0.185224E+04,0.186407E+04,
      0.187599E+04,0.188797E+04,0.190000E+04,0.191212E+04,0.192428E+04,
      0.193653E+04,0.194886E+04,0.196122E+04,0.197368E+04,0.198618E+04,
      0.199878E+04,0.201145E+04,0.202416E+04,0.203698E+04,0.204983E+04,
      0.206278E+04,0.207580E+04,0.208887E+04,0.210204E+04,0.211525E+04,
      0.212856E+04,0.214195E+04,0.215538E+04,0.216892E+04,0.218249E+04,
      0.219618E+04,0.220994E+04,0.222375E+04,0.223766E+04,0.225161E+04,
      0.226567E+04,0.227981E+04,0.229399E+04,0.230829E+04,0.232263E+04,
      0.233708E+04,0.235161E+04,0.236618E+04,0.238087E+04,0.239560E+04,
      0.241044E+04,0.242538E+04,0.244035E+04,0.245544E+04,0.247057E+04,
      0.248583E+04,0.250116E+04,0.251654E+04,0.253204E+04,0.254759E+04,
      0.256325E+04,0.257901E+04,0.259480E+04,0.261073E+04,0.262670E+04,
      0.264279E+04,0.265896E+04,0.267519E+04,0.269154E+04,0.270794E+04,
      0.272447E+04,0.274108E+04,0.275774E+04,0.277453E+04,0.279137E+04,
      0.280834E+04,0.282540E+04,0.284251E+04,0.285975E+04,0.287704E+04,
      0.289446E+04,0.291198E+04,0.292954E+04,0.294725E+04,0.296499E+04,
     0.298288E+04,0.300087E+04,0.301890E+04,0.303707E+04,0.305529E+04,
      0.307365E+04,0.309211E+04,0.311062E+04,0.312927E+04,0.314798E+04,
      0.316682E+04,0.318577E+04,0.320477E+04,0.322391E+04,0.324310E+04,
      0.326245E+04,0.328189E+04,0.330138E+04,0.332103E+04,0.334073E+04,
      0.336058E+04,0.338053E+04,0.340054E+04,0.342069E+04,0.344090E+04,
      0.346127E+04,0.348174E+04,0.350227E+04,0.352295E+04,0.354369E+04,
      0.356458E+04,0.358559E+04,0.360664E+04,0.362787E+04,0.364914E+04,
      0.367058E+04,0.369212E+04,0.371373E+04,0.373548E+04,0.375731E+04,
      0.377929E+04,0.380139E+04,0.382355E+04,0.384588E+04,0.386826E+04,
      0.389081E+04,0.391348E+04,0.393620E+04,0.395910E+04,0.398205E+04,
      0.400518E+04,0.402843E+04,0.405173E+04,0.407520E+04,0.409875E+04,
      0.412246E+04,0.414630E+04,0.417019E+04,0.419427E+04,0.421840E+04,
      0.424272E+04,0.426715E+04,0.429165E+04,0.431634E+04,0.434108E+04,
      0.436602E+04,0.439107E+04,0.441618E+04,0.444149E+04,0.446685E+04,
      0.449241E+04,0.451810E+04,0.454385E+04,0.456977E+04,0.459578E+04,
      0.462197E+04,0.464830E+04,0.467468E+04,0.470127E+04,0.472792E+04,
      0.475477E+04,0.478175E+04,0.480880E+04,0.483605E+04,0.486336E+04,
      0.489087E+04,0.491853E+04,0.494623E+04,0.497415E+04,0.500215E+04,
      0.503034E+04,0.505867E+04,0.508707E+04,0.511568E+04,0.514436E+04,
     0.517325E+04,0.520227E+04,0.523137E+04,0.526068E+04,0.529005E+04,
      0.531965E+04,0.534939E+04,0.537921E+04,0.540923E+04,0.543932E+04,
      0.546965E+04,0.550011E+04,0.553064E+04,0.556139E+04,0.559223E+04,
      0.562329E+04,0.565449E+04,0.568577E+04,0.571727E+04,0.574884E+04,
      0.578064E+04,0.581261E+04,0.584464E+04,0.587692E+04,0.590924E+04,
      0.594182E+04,0.597455E+04,0.600736E+04,0.604039E+04,0.607350E+04,
      0.610685E+04,0.614036E+04,0.617394E+04,0.620777E+04,0.624169E+04,
      0.627584E+04,0.631014E+04,0.634454E+04,0.637918E+04,0.641390E+04,
      0.644887E+04,0.648400E+04,0.651919E+04,0.655467E+04,0.659021E+04,
      0.662599E+04,0.666197E+04,0.669800E+04,0.673429E+04,0.677069E+04,
      0.680735E+04,0.684415E+04,0.688104E+04,0.691819E+04,0.695543E+04,
      0.699292E+04,0.703061E+04,0.706837E+04,0.710639E+04,0.714451E+04,
      0.718289E+04,0.722143E+04,0.726009E+04,0.729903E+04,0.733802E+04,
      0.737729E+04,0.741676E+04,0.745631E+04,0.749612E+04,0.753602E+04,
      0.757622E+04,0.761659E+04,0.765705E+04,0.769780E+04,0.773863E+04,
      0.777975E+04,0.782106E+04,0.786246E+04,0.790412E+04,0.794593E+04,
      0.798802E+04,0.803028E+04,0.807259E+04,0.811525E+04,0.815798E+04,
      0.820102E+04,0.824427E+04,0.828757E+04,0.833120E+04,0.837493E+04,
      0.841895E+04,0.846313E+04,0.850744E+04,0.855208E+04,0.859678E+04,
     0.864179E+04,0.868705E+04,0.873237E+04,0.877800E+04,0.882374E+04,
      0.886979E+04,0.891603E+04,0.896237E+04,0.900904E+04,0.905579E+04,
      0.910288E+04,0.915018E+04,0.919758E+04,0.924529E+04,0.929310E+04,
      0.934122E+04,0.938959E+04,0.943804E+04,0.948687E+04,0.953575E+04,
      0.958494E+04,0.963442E+04,0.968395E+04,0.973384E+04,0.978383E+04,
      0.983412E+04,0.988468E+04,0.993534E+04,0.998630E+04,0.100374E+05,
      0.100888E+05,0.101406E+05,0.101923E+05,0.102444E+05,0.102966E+05,
      0.103492E+05,0.104020E+05,0.104550E+05,0.105082E+05,0.105616E+05,
      0.106153E+05,0.106693E+05,0.107234E+05,0.107779E+05,0.108325E+05,
      0.108874E+05,0.109425E+05,0.109978E+05,0.110535E+05,0.111092E+05,
      0.111653E+05,0.112217E+05,0.112782E+05,0.113350E+05,0.113920E+05,
      0.114493E+05,0.115070E+05,0.115646E+05,0.116228E+05,0.116809E+05,
      0.117396E+05,0.117984E+05,0.118574E+05,0.119167E+05,0.119762E+05,
      0.120360E+05,0.120962E+05,0.121564E+05,0.122170E+05,0.122778E+05,
      0.123389E+05,0.124004E+05,0.124619E+05,0.125238E+05,0.125859E+05,
      0.126484E+05,0.127111E+05,0.127739E+05,0.128372E+05,0.129006E+05,
      0.129644E+05,0.130285E+05,0.130927E+05,0.131573E+05,0.132220E+05,
      0.132872E+05,0.133526E+05,0.134182E+05,0.134842E+05,0.135503E+05,
      0.136168E+05,0.136836E+05,0.137505E+05,0.138180E+05,0.138854E+05,
     0.139534E+05,0.140216E+05,0.140900E+05,0.141588E+05,0.142277E+05,
      0.142971E+05,0.143668E+05,0.144366E+05,0.145069E+05,0.145773E+05,
      0.146481E+05,0.147192E+05,0.147905E+05,0.148622E+05,0.149341E+05,
      0.150064E+05,0.150790E+05,0.151517E+05,0.152250E+05,0.152983E+05,
      0.153721E+05,0.154462E+05,0.155205E+05,0.155952E+05,0.156701E+05,
      0.157454E+05,0.158211E+05,0.158969E+05,0.159732E+05,0.160496E+05,
      0.161265E+05,0.162037E+05,0.162811E+05,0.163589E+05,0.164369E+05,
      0.165154E+05,0.165942E+05,0.166732E+05,0.167526E+05,0.168322E+05,
      0.169123E+05,0.169927E+05,0.170733E+05,0.171543E+05,0.172356E+05,
      0.173173E+05,0.173993E+05,0.174815E+05,0.175643E+05,0.176471E+05,
      0.177305E+05,0.178143E+05,0.178981E+05,0.179826E+05,0.180671E+05,
      0.181522E+05,0.182377E+05,0.183232E+05,0.184093E+05,0.184955E+05,
      0.185823E+05,0.186695E+05,0.187568E+05,0.188447E+05,0.189326E+05,
      0.190212E+05,0.191101E+05,0.191991E+05,0.192887E+05,0.193785E+05,
      0.194688E+05,0.195595E+05,0.196503E+05,0.197417E+05,0.198332E+05,
      0.199253E+05,0.200178E+05,0.201105E+05,0.202036E+05,0.202971E+05,
      0.203910E+05,0.204853E+05,0.205798E+05,0.206749E+05,0.207701E+05,
      0.208659E+05,0.209621E+05,0.210584E+05,0.211554E+05,0.212524E+05,
      0.213501E+05,0.214482E+05,0.215465E+05,0.216452E+05,0.217442E+05,
     0.218439E+05,0.219439E+05,0.220440E+05,0.221449E+05,0.222457E+05,
      0.223473E+05,0.224494E+05,0.225514E+05,0.226542E+05,0.227571E+05,
      0.228606E+05,0.229646E+05,0.230687E+05,0.231734E+05,0.232783E+05,
      0.233839E+05,0.234898E+05,0.235960E+05,0.237027E+05,0.238097E+05,
      0.239173E+05,0.240254E+05,0.241335E+05,0.242424E+05,0.243514E+05,
      0.244611E+05,0.245712E+05,0.246814E+05,0.247923E+05,0.249034E+05,
      0.250152E+05,0.250152E+05,
    };

    // Verify es size
    if (es.size() != static_cast<size_t>(n + 2)) {
        throw std::runtime_error("es array size must be " + std::to_string(n + 2));
    }

    // Compute saturation mixing ratio
    for (size_t i = 0; i < static_cast<size_t>(npnts); ++i) {

        // Compute FSUBW (Gill's equation A4.7)
        double fsubw = 1.0 + 1.0e-8 * p[i] * (4.5 +
            6.0e-4 * (t[i] - zerodegc) * (t[i] - zerodegc));

        // Interpolate saturation vapor pressure from lookup table
        double tt = std::max(t_low, std::min(t_high, t[i]));
        double atable = (tt - t_low + delta_t) / delta_t;
        int itable = static_cast<int>(std::floor(atable));
        atable -= itable;

        double qs_i = (1.0 - atable) * es[itable] + atable * es[itable + 1];

        // Apply FSUBW (Gill's equation A4.6)
        qs_i *= fsubw;

        // Compute mixing ratio (Gill's equation A4.3) with singularity fix
        qs[i] = (epsilon * qs_i) / (std::max(p[i], qs_i) - one_minus_epsilon * qs_i);
    }
}


/**
 * Redistributes precipitation if the maximum precipitation rate is exceeded.
 *
 * Adjusts the precipitation array to ensure no sub-daily timestep exceeds
 * the maximum precipitation rate, redistributing excess precipitation to
 * other periods within the day.
 *
 * @param nsdmax Maximum possible number of sub-daily timesteps.
 * @param step_day Number of timesteps per day.
 * @param max_precip_rate Maximum allowed precipitation rate (mm/day).
 * @param prec_loc Precipitation for each timestep (mm/day), modified in-place.
 * @param n_event_local 1 if precipitation occurs in timestep, 0 otherwise, modified in-place.
 * @param n_tally Number of precipitation periods, updated in-place.
 * @throws std::runtime_error If inputs are invalid (e.g., negative sizes, mismatched arrays).
 *
 * Written by Chris Huntingford (September 2001), converted to C++ in 2025.
 */
void redis(int nsdmax, int step_day, double max_precip_rate,
    std::vector<double>& prec_loc, std::vector<int>& n_event_local,
    int& n_tally) {
    // Validate inputs
    if (nsdmax <= 0 || step_day <= 0 || step_day > nsdmax) {
        throw std::runtime_error("Invalid nsdmax or step_day");
    }
    if (max_precip_rate < 0.0) {
        throw std::runtime_error("max_precip_rate must be non-negative");
    }
    if (prec_loc.size() != static_cast<size_t>(nsdmax) ||
        n_event_local.size() != static_cast<size_t>(nsdmax)) {
        throw std::runtime_error("Array sizes must match nsdmax");
    }
    if (n_tally < 0 || n_tally > step_day) {
        throw std::runtime_error("Invalid n_tally");
    }

    // Calculate total precipitation for the day (mm/day)
    double prec_tot = 0.0;
    for (size_t i = 0; i < static_cast<size_t>(step_day); ++i) {
        prec_tot += (1.0 / static_cast<double>(step_day)) * prec_loc[i];
    }

    // Limit precipitation rate to max_precip_rate
    for (size_t i = 0; i < static_cast<size_t>(step_day); ++i) {
        if (prec_loc[i] > max_precip_rate) {
            prec_loc[i] = max_precip_rate;
        }
    }

    // Calculate adjusted total precipitation
    double prec_tot_adj = 0.0;
    for (size_t i = 0; i < static_cast<size_t>(step_day); ++i) {
        prec_tot_adj += (1.0 / static_cast<double>(step_day)) * prec_loc[i];
    }

    // Find first and last periods of precipitation
    int last_period = 0;
    for (size_t i = 0; i < static_cast<size_t>(step_day); ++i) {
        if (n_event_local[i] == 1) {
            last_period = static_cast<int>(i);
        }
    }
    int first_period = last_period - n_tally + 1;

    // Calculate precipitation to redistribute
    double prec_change = prec_tot - prec_tot_adj;

    // Redistribute excess precipitation if necessary
    if (prec_change > 0.0) {
        double extra_per_real = (prec_change * static_cast<double>(step_day)) / max_precip_rate;
        int extra_per_int = static_cast<int>(std::floor(extra_per_real));

        // Case: Cannot distribute all rainfall (fill all non-event periods)
        if (extra_per_int >= step_day - n_tally) {
            for (size_t i = 0; i < static_cast<size_t>(step_day); ++i) {
                if (n_event_local[i] == 0) {
                    prec_loc[i] = max_precip_rate;
                    n_event_local[i] = 1; // Update event indicator
                }
            }
            n_tally = step_day; // All periods are now precipitation events
        }
        // Case 1: First_period == 1, distribute all after storm
        else if (first_period == 1) {
            for (size_t i = last_period + 1; i <= static_cast<size_t>(last_period + extra_per_int); ++i) {
                prec_loc[i] = max_precip_rate;
                n_event_local[i] = 1;
            }
            if (extra_per_real > extra_per_int) {
                size_t idx = last_period + extra_per_int + 1;
                prec_loc[idx] = max_precip_rate * (extra_per_real - static_cast<double>(extra_per_int));
                n_event_local[idx] = 1;
            }
            n_tally += extra_per_int + (extra_per_real > extra_per_int ? 1 : 0);
        }
        // Case 2: All precipitation can be accommodated before storm
        else if (extra_per_int + 1 <= first_period - 1) {
            for (size_t i = static_cast<size_t>(first_period - 1); i >= static_cast<size_t>(first_period - extra_per_int); --i) {
                prec_loc[i] = max_precip_rate;
                n_event_local[i] = 1;
            }
            if (extra_per_real > extra_per_int) {
                size_t idx = first_period - extra_per_int - 1;
                prec_loc[idx] = max_precip_rate * (extra_per_real - static_cast<double>(extra_per_int));
                n_event_local[idx] = 1;
            }
            n_tally += extra_per_int + (extra_per_real > extra_per_int ? 1 : 0);
        }
        // Case 3: Distribute before and after storm
        else {
            // Fill periods before storm
            for (size_t i = static_cast<size_t>(first_period - 1); i >= 1; --i) {
                prec_loc[i] = max_precip_rate;
                n_event_local[i] = 1;
            }
            // Fill periods after storm
            int periods_after = extra_per_int - (first_period - 1);
            for (size_t i = last_period + 1; i <= static_cast<size_t>(last_period + periods_after); ++i) {
                prec_loc[i] = max_precip_rate;
                n_event_local[i] = 1;
            }
            if (extra_per_real > extra_per_int) {
                size_t idx = last_period + periods_after + 1;
                prec_loc[idx] = max_precip_rate * (extra_per_real - static_cast<double>(extra_per_int));
                n_event_local[idx] = 1;
            }
            n_tally += extra_per_int + (extra_per_real > extra_per_int ? 1 : 0);
        }
    }
}


/**
 * Solves a tridiagonal matrix system to compute new values of u.
 *
 * Solves A u_new = B u_old + k, where A and B are tridiagonal matrices,
 * representing the equation du/dz - pu = lambda. Uses Gaussian elimination
 * and verifies the solution.
 *
 * @param u_old Old values of u (size n_olevs).
 * @param u_new New values of u, computed in-place (size n_olevs).
 * @param p Value in mixed-boundary condition.
 * @param lambda_old Lambda value at old timestep.
 * @param lambda_new Lambda value at new timestep.
 * @param r1 Mesh ratio (size n_olevs).
 * @param r2 Mesh ratio (size n_olevs).
 * @param dz_top Top layer mesh size.
 * @param n_olevs Number of layers.
 * @throws std::runtime_error If inputs are invalid or solution verification fails.
 *
 * Converted to C++ in 2025.
 */
void invert(const std::vector<double>& u_old, std::vector<double>& u_new,
    double p, double lambda_old, double lambda_new,
    const std::vector<double>& r1, const std::vector<double>& r2,
    double dz_top, int n_olevs) {
    // Validate inputs
    if (n_olevs <= 0) {
        throw std::runtime_error("n_olevs must be positive");
    }
    if (u_old.size() != static_cast<size_t>(n_olevs) ||
        u_new.size() != static_cast<size_t>(n_olevs) ||
        r1.size() != static_cast<size_t>(n_olevs) ||
        r2.size() != static_cast<size_t>(n_olevs)) {
        throw std::runtime_error("array sizes must match n_olevs");
    }
    if (dz_top < 0.0) {
        throw std::runtime_error("dz_top must be non-negative");
    }

    // Initialize matrices and vectors
    std::vector<std::vector<double>> a(n_olevs, std::vector<double>(n_olevs, 0.0));
    std::vector<std::vector<double>> b(n_olevs, std::vector<double>(n_olevs, 0.0));
    std::vector<std::vector<double>> a_l(n_olevs, std::vector<double>(n_olevs, 0.0));
    std::vector<double> k(n_olevs, 0.0);
    std::vector<double> f_l(n_olevs, 0.0);

    // Populate matrices A, B, and vector K
    a[0][0] = (1.0 + r1[0]) + r1[0] * dz_top * p;
    a[0][1] = -r1[0];
    b[0][0] = (1.0 - r1[0]) - r1[0] * dz_top * p;
    b[0][1] = r1[0];
    k[0] = -r1[0] * dz_top * (lambda_old + lambda_new);

    for (size_t i = 1; i < static_cast<size_t>(n_olevs) - 1; ++i) {
        a[i][i - 1] = -r1[i];
        a[i][i] = 1.0 + r1[i] + r2[i];
        a[i][i + 1] = -r2[i];
        b[i][i - 1] = r1[i];
        b[i][i] = 1.0 - r1[i] - r2[i];
        b[i][i + 1] = r2[i];
    }

    a[n_olevs - 1][n_olevs - 2] = -r1[n_olevs - 1];
    a[n_olevs - 1][n_olevs - 1] = 1.0 + r1[n_olevs - 1] + r2[n_olevs - 1];
    b[n_olevs - 1][n_olevs - 2] = r1[n_olevs - 1];
    b[n_olevs - 1][n_olevs - 1] = 1.0 - r1[n_olevs - 1] - r2[n_olevs - 1];

    // Compute F_L = B u_old + k
    f_l[0] = b[0][0] * u_old[0] + b[0][1] * u_old[1] + k[0];
    for (size_t i = 1; i < static_cast<size_t>(n_olevs) - 1; ++i) {
        f_l[i] = b[i][i - 1] * u_old[i - 1] + b[i][i] * u_old[i] + b[i][i + 1] * u_old[i + 1] + k[i];
    }
    f_l[n_olevs - 1] = b[n_olevs - 1][n_olevs - 2] * u_old[n_olevs - 2] +
        b[n_olevs - 1][n_olevs - 1] * u_old[n_olevs - 1] + k[n_olevs - 1];

    // Copy A to A_L
    a_l[0][0] = a[0][0];
    a_l[0][1] = a[0][1];
    for (size_t i = 1; i < static_cast<size_t>(n_olevs) - 1; ++i) {
        a_l[i][i - 1] = a[i][i - 1];
        a_l[i][i] = a[i][i];
        a_l[i][i + 1] = a[i][i + 1];
    }
    a_l[n_olevs - 1][n_olevs - 2] = a[n_olevs - 1][n_olevs - 2];
    a_l[n_olevs - 1][n_olevs - 1] = a[n_olevs - 1][n_olevs - 1];

    // Gaussian elimination
    if (std::abs(a_l[n_olevs - 1][n_olevs - 1]) < 1e-10) {
        throw std::runtime_error("division by near-zero in Gaussian elimination");
    }
    double factor = a_l[n_olevs - 2][n_olevs - 1] / a_l[n_olevs - 1][n_olevs - 1];
    a_l[n_olevs - 1][n_olevs - 2] *= factor;
    a_l[n_olevs - 1][n_olevs - 1] = a_l[n_olevs - 2][n_olevs - 1];
    f_l[n_olevs - 1] *= factor;

    a_l[n_olevs - 2][n_olevs - 2] -= a_l[n_olevs - 1][n_olevs - 2];
    a_l[n_olevs - 2][n_olevs - 1] = 0.0;
    f_l[n_olevs - 2] -= f_l[n_olevs - 1];

    for (int i = n_olevs - 2; i >= 1; --i) {
        if (std::abs(a_l[i][i]) < 1e-10) {
            throw std::runtime_error("division by near-zero in Gaussian elimination");
        }
        factor = a_l[i - 1][i] / a_l[i][i];
        a_l[i][i - 1] *= factor;
        a_l[i][i] = a_l[i - 1][i];
        f_l[i] *= factor;

        a_l[i - 1][i - 1] -= a_l[i][i - 1];
        a_l[i - 1][i] = 0.0;
        f_l[i - 1] -= f_l[i];
    }

    // Compute U_NEW
    if (std::abs(a_l[0][0]) < 1e-10) {
        throw std::runtime_error("division by near-zero in U_NEW computation");
    }
    u_new[0] = f_l[0] / a_l[0][0];
    for (size_t i = 1; i < static_cast<size_t>(n_olevs); ++i) {
        if (std::abs(a_l[i][i]) < 1e-10) {
            throw std::runtime_error("division by near-zero in U_NEW computation");
        }
        u_new[i] = (f_l[i] - a_l[i][i - 1] * u_new[i - 1]) / a_l[i][i];
    }

    // Verify solution
    for (size_t i = 0; i < static_cast<size_t>(n_olevs); ++i) {
        double dummy1 = 0.0;
        double dummy2 = 0.0;
        for (size_t j = 0; j < static_cast<size_t>(n_olevs); ++j) {
            dummy1 += a[i][j] * u_new[j];
            dummy2 += b[i][j] * u_old[j];
        }
        dummy2 += k[i];
        if (std::abs(dummy1 - dummy2) >= 0.0001) {
            throw std::runtime_error("solution verification failed: A u_new != B u_old + k");
        }
    }
}


/**
 * Computes global mean land and ocean surface temperature anomalies.
 *
 * Implements a two-box thermal model using an implicit solver for ocean
 * temperature profiles across multiple layers, estimating land temperature
 * anomalies based on ocean surface temperature.
 *
 * @param n_olevs Number of ocean thermal layers.
 * @param f_ocean Fractional coverage of planet with ocean (0 to 1).
 * @param kappa Ocean eddy diffusivity (W/m/K).
 * @param lambda_l Inverse climate sensitivity over land (W/K/m^2).
 * @param lambda_o Inverse climate sensitivity over ocean (W/K/m^2).
 * @param mu Ratio of land-to-ocean temperature anomalies.
 * @param q Increase in global radiative forcing (W/m^2).
 * @param dtemp_l Land mean temperature anomaly, computed in-place.
 * @param dtemp_o Ocean mean temperature anomalies, modified in-place.
 * @throws std::runtime_error If inputs are invalid or flux check fails.
 *
 * Written by C. Huntingford (September 1998), converted to C++ in 2025.
 */
void delta_temp(int n_olevs, double f_ocean, double kappa, double lambda_l,
    double lambda_o, double mu, double q, double& dtemp_l,
    std::vector<double>& dtemp_o) {
    // Validate inputs
    if (n_olevs <= 0) {
        throw std::runtime_error("n_olevs must be positive");
    }
    if (f_ocean < 0.0 || f_ocean > 1.0) {
        throw std::runtime_error("f_ocean must be between 0 and 1");
    }
    if (kappa <= 0.0) {
        throw std::runtime_error("kappa must be positive");
    }
    if (lambda_l <= 0.0 || lambda_o <= 0.0) {
        throw std::runtime_error("lambda_l and lambda_o must be positive");
    }
    if (mu < 0.0) {
        throw std::runtime_error("mu must be non-negative");
    }
    if (dtemp_o.size() != static_cast<size_t>(n_olevs)) {
        throw std::runtime_error("dtemp_o size must match n_olevs");
    }

    // Constants
    constexpr double rhocp = 4.04e6;      // Ocean heat capacity (J/K/m^3)
    constexpr double sec_year = 3.1536e7; // Seconds in a year
    constexpr int iter_per_year = 20;     // Iterations per year

    // Model parameters
    const double dtime = sec_year / static_cast<double>(iter_per_year);
    const int timesteps = iter_per_year;

    // Initialize arrays
    std::vector<double> dz(n_olevs);
    std::vector<double> r1(n_olevs);
    std::vector<double> r2(n_olevs);
    std::vector<double> u_old(n_olevs);
    std::vector<double> u_new(n_olevs);

    // Compute variable depth mesh
    double dz_top = 2.0;
    double depth = 0.0;
    for (size_t i = 0; i < static_cast<size_t>(n_olevs); ++i) {
        double factor_dep = std::exp(depth / 500.0);
        dz[i] = dz_top * factor_dep;
        depth += dz[i];
    }

    // Scale depths to total 5000 meters
    dz_top *= (5000.0 / depth);
    for (size_t i = 0; i < static_cast<size_t>(n_olevs); ++i) {
        dz[i] *= (5000.0 / depth);
    }

    // Compute mesh ratios
    r1[0] = (kappa / rhocp) * (dtime / (dz_top * dz_top));
    r2[0] = 0.0;
    for (size_t i = 1; i < static_cast<size_t>(n_olevs); ++i) {
        r1[i] = (kappa / rhocp) * (dtime / (dz[i - 1] * (dz[i] + dz[i - 1])));
        r2[i] = (kappa / rhocp) * (dtime / (dz[i] * (dz[i] + dz[i - 1])));
    }

    // Initialize u_old from dtemp_o
    for (size_t i = 0; i < static_cast<size_t>(n_olevs); ++i) {
        u_old[i] = dtemp_o[i];
    }

    // Time stepping loop
    for (int i = 0; i < timesteps; ++i) {
        double lambda_old = -q / (kappa * f_ocean);
        double lambda_new = -q / (kappa * f_ocean);
        double p = ((1.0 - f_ocean) * lambda_l * mu) / (f_ocean * kappa) + lambda_o / kappa;

        // Solve for u_new
        invert(u_old, u_new, p, lambda_old, lambda_new, r1, r2, dz_top, n_olevs);

        // Check bottom flux
        double flux_top = -0.5 * (kappa * lambda_old * dtime) - 0.5 * (kappa * lambda_new * dtime)
            - 0.5 * (p * kappa * u_old[0] * dtime) - 0.5 * (p * kappa * u_new[0] * dtime);
        double flux_bottom = (dtime / (2.0 * dz[n_olevs - 1])) * kappa * (u_old[n_olevs - 1] + u_new[n_olevs - 1]);

        if (std::abs(flux_bottom / (flux_top + 1e-7)) > 0.01) {
            std::cerr << "Warning: Flux at bottom of the ocean is greater than 0.01 of top" << std::endl;
            // Optionally throw: throw std::runtime_error("bottom flux too large");
        }

        // Update u_old
        for (size_t j = 0; j < static_cast<size_t>(n_olevs); ++j) {
            u_old[j] = u_new[j];
        }
    }

    // Compute outputs
    for (size_t j = 0; j < static_cast<size_t>(n_olevs); ++j) {
        dtemp_o[j] = u_new[j];
    }
    dtemp_l = mu * dtemp_o[0];
}


/**
 * GCM Analogue Model to calculate climate anomalies based on radiative forcing.
 *
 * @param q Radiative forcing (W/m^2).
 * @param land_pts Number of land points.
 * @param n_olevs Number of ocean thermal layers.
 * @param dir_patt Directory containing anomaly patterns.
 * @param f_ocean Fractional coverage of the ocean.
 * @param kappa_o Ocean eddy diffusivity (W/m/K).
 * @param lambda_l Inverse climate sensitivity over land (W/m^2/K).
 * @param lambda_o Inverse climate sensitivity over ocean (W/m^2/K).
 * @param mu Ratio of land to ocean temperature anomalies.
 * @param longmin_am Minimum longitude (degrees).
 * @param latmin_am Minimum latitude (degrees).
 * @param longmax_am Maximum longitude (degrees).
 * @param latmax_am Maximum latitude (degrees).
 * @param mm Number of months in a year.
 * @return GcmAnlgOutput Structure containing anomaly arrays and updated dtemp_o.
 * @throws std::runtime_error If file operations or inputs are invalid.
 *
 * Written by C. Huntingford and P. Cox (9/98), simplified 3/04, converted to C++ in 2025.
 */
GcmAnlgOutput gcm_anlg(double q, int land_pts, int n_olevs, const std::string& dir_patt,
    double f_ocean, double kappa_o, double lambda_l, double lambda_o,
    double mu, double& longmin_am, double& latmin_am, double& longmax_am,
    double& latmax_am, int mm) {
    // Validate inputs
    if (land_pts <= 0 || n_olevs <= 0 || mm <= 0) {
        throw std::runtime_error("land_pts, n_olevs, and mm must be positive");
    }
    if (dir_patt.empty()) {
        throw std::runtime_error("dir_patt cannot be empty");
    }

    // Initialize output structure
    GcmAnlgOutput output;
    output.t_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.precip_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.rh15m_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.uwind_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.vwind_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.dtemp_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.pstar_ha_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.sw_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.lw_anom_am.resize(land_pts, std::vector<double>(mm, 0.0));
    output.dtemp_o.resize(n_olevs, 0.0); // Initialize with input dtemp_o (updated by delta_temp)

    // Define month labels (equivalent to Fortran DATA DRIVE_MONTH)
    std::array<std::string, 12> drive_month = {
        "/jan", "/feb", "/mar", "/apr", "/may", "/jun",
        "/jul", "/aug", "/sep", "/oct", "/nov", "/dec"
    };

    // Local variables
    std::vector<double> long_am(land_pts), lat_am(land_pts);

    // Loop over months
    for (int im = 0; im < mm; ++im) {
        // Calculate temperature anomalies (only in first month)
        double dtemp_l = 0.0;
        if (im == 0) {
            delta_temp(n_olevs, f_ocean, kappa_o, lambda_l, lambda_o, mu, q,
                dtemp_l, output.dtemp_o);
        }

        // Construct file path (trim DIR_PATT and append DRIVE_MONTH)
        std::string driver_patt = dir_patt;
        while (!driver_patt.empty() && driver_patt.back() == ' ') {
            driver_patt.pop_back();
        }
        if (im < static_cast<int>(drive_month.size())) {
            driver_patt += drive_month[im];
        }
        else {
            throw std::runtime_error("Invalid month index: " + std::to_string(im));
        }

        // Log file path (equivalent to Fortran WRITE(6,*))
        std::cerr << "Reading pattern file: " << driver_patt << std::endl;

        // Open and read pattern file
        std::ifstream file(driver_patt);
        if (!file.is_open()) {
            throw std::runtime_error("Unable to open file: " + driver_patt);
        }

        // Read header
        double read_longmin_am, read_latmin_am, read_longmax_am, read_latmax_am;
        if (!(file >> read_longmin_am >> read_latmin_am >> read_longmax_am >> read_latmax_am)) {
            file.close();
            throw std::runtime_error("Failed to read header from: " + driver_patt);
        }
        // Update input parameters (Fortran modifies these directly)
        longmin_am = read_longmin_am;
        latmin_am = read_latmin_am;
        longmax_am = read_longmax_am;
        latmax_am = read_latmax_am;
   /*     logger.info("////////////////////////////////////////////");
        logger.info("Drive path: " + driver_patt);
        logger.info("longmin_am: " + std::to_string(longmin_am));
        logger.info("latmin_am: " + std::to_string(latmin_am));
        logger.info("longmax_am: " + std::to_string(longmax_am));
        logger.info("latmax_am: " + std::to_string(latmax_am));
        logger.info("\n");*/

        // Log dtemp_l (equivalent to Fortran print *)
        std::cerr << "DTEMP_L = " << dtemp_l << std::endl;

        // Read and process anomaly patterns for each land point
        for (int l = 0; l < land_pts; ++l) {
            double dt_c_pat, drh15m_pat, duwind_pat, dvwind_pat, dlw_c_pat,
                dsw_c_pat, ddtemp_day_pat, drainfall_pat, dsnowfall_pat,
                dpstar_c_pat;
            if (!(file >> long_am[l] >> lat_am[l] >> dt_c_pat >> drh15m_pat
                >> duwind_pat >> dvwind_pat >> dlw_c_pat >> dsw_c_pat
                >> ddtemp_day_pat >> drainfall_pat >> dsnowfall_pat
                >> dpstar_c_pat)) {
                file.close();
                throw std::runtime_error("Failed to read data for point " +
                    std::to_string(l) + " from: " + driver_patt);
            }

            // Scale anomalies by land mean temperature anomaly
            output.t_anom_am[l][im] = dt_c_pat * dtemp_l;
            output.rh15m_anom_am[l][im] = drh15m_pat * dtemp_l;
            output.uwind_anom_am[l][im] = duwind_pat * dtemp_l;
            output.vwind_anom_am[l][im] = dvwind_pat * dtemp_l;
            output.lw_anom_am[l][im] = dlw_c_pat * dtemp_l;
            output.sw_anom_am[l][im] = dsw_c_pat * dtemp_l;
            output.dtemp_anom_am[l][im] = ddtemp_day_pat * dtemp_l;
            output.pstar_ha_anom_am[l][im] = dpstar_c_pat * dtemp_l;

            // Compute rainfall and snowfall anomalies
            double rainfall_anom_am = drainfall_pat * dtemp_l;
            double snowfall_anom_am = dsnowfall_pat * dtemp_l;
            output.precip_anom_am[l][im] = rainfall_anom_am + snowfall_anom_am;
        }

        file.close();
    }

    return output;
}


/**
 * Computes the response function for oceanic CO2 uptake.
 *
 * Populates the response function values used in the Joos et al. model for
 * calculating CO2 perturbations in the ocean mixed layer.
 *
 * @param ncall_yr Number of calls per year to the ocean routine.
 * @param year_run Number of years in the simulation.
 * @param rs Response function values, computed in-place (size ncall_yr * year_run).
 * @throws std::runtime_error If inputs are invalid.
 *
 * Converted to C++ in 2025.
 */
void response(int ncall_yr, int year_run, std::vector<double>& rs) {
    // Validate inputs
    if (ncall_yr <= 0) {
        throw std::runtime_error("ncall_yr must be positive");
    }
    if (year_run <= 0) {
        throw std::runtime_error("year_run must be positive");
    }

    // Resize output vector
    rs.resize(ncall_yr * year_run);

    // Compute response function
    for (int i = 1; i <= ncall_yr * year_run; ++i) {
        double time_rs = static_cast<double>(i) / ncall_yr;
        if (time_rs >= 1.0) {
            rs[i - 1] = 0.014819 +
                0.70367 * std::exp(-time_rs / 0.70177) +
                0.24966 * std::exp(-time_rs / 2.3488) +
                0.066485 * std::exp(-time_rs / 15.281) +
                0.038344 * std::exp(-time_rs / 65.359) +
                0.019439 * std::exp(-time_rs / 347.55);
        }
        else {
            double t2 = time_rs * time_rs;
            double t3 = t2 * time_rs;
            double t4 = t3 * time_rs;
            double t5 = t4 * time_rs;
            double t6 = t5 * time_rs;
            rs[i - 1] = 1.0 - 2.2617 * time_rs + 14.002 * t2 -
                48.770 * t3 + 82.986 * t4 - 67.527 * t5 +
                21.037 * t6;
        }
    }
}

/**
 * Calculates the sine of the solar declination and solar constant scaling factor.
 *
 * Computes the solar declination and scaling factor for the solar constant
 * based on the day of the year and orbital parameters, using a 360-day calendar.
 *
 * @param day Day of the year (1 to 360).
 * @param year Calendar year (unused in 360-day calendar mode).
 * @param sindec Sine of the solar declination, modified in-place.
 * @param scs Solar constant scaling factor, modified in-place.
 * @throws std::runtime_error If day is invalid (not in [1, 360]).
 *
 * Written by William Ingram (March 1989), converted to C++ in 2025.
 */
void solpos(int day, int /*year*/, double& sindec, double& scs) {
    // Validate inputs
    if (day < 1 || day > 360) {
        throw std::runtime_error("day must be between 1 and 360");
    }

    // Constants
    constexpr double pi = 3.1415926535879323846;
    constexpr double pi_over_180 = pi / 180.0;
    constexpr double recip_pi_over_180 = 180.0 / pi;
    constexpr double twopi = 2.0 * pi;

    // Orbital constants
    constexpr double gamma = 1.352631; // Orbital constant
    constexpr double e = 0.0167;       // Eccentricity
    constexpr double tau0 = 2.5;       // True date of perihelion
    constexpr double sinobl = 0.397789; // Sine of obliquity
    constexpr double diny = 360.0;     // Days in year (360-day calendar)
    constexpr double e1 = e * (2.0 - 0.25 * e * e);
    constexpr double e2 = 1.25 * e * e;
    constexpr double e3 = e * e * e * 13.0 / 12.0;
    constexpr double e4 = ((1.0 + e * e * 0.5) / (1.0 - e * e)) * ((1.0 + e * e * 0.5) / (1.0 - e * e));
    constexpr double tau1 = tau0 * diny / 365.25 + 0.71 + 0.5;

    // Compute mean anomaly (Eq 3.1.1)
    double m = twopi * (static_cast<double>(day) - tau1) / diny;

    // Compute true anomaly (Eq 3.1.2)
    double v = m + e1 * std::sin(m) + e2 * std::sin(2.0 * m) + e3 * std::sin(3.0 * m);

    // Compute solar constant scaling factor (Eq 3.1.4)
    scs = e4 * (1.0 + e * std::cos(v)) * (1.0 + e * std::cos(v));

    // Compute sine of solar declination (Eq 3.1.6)
    sindec = sinobl * std::sin(v - gamma);
}


/**
 * Calculates the sunlit fraction and mean cosine of the solar zenith angle.
 *
 * Computes the fraction of the timestep that is sunlit and the mean cosine
 * of the solar zenith angle for each point, based on solar declination,
 * latitude, longitude, and time.
 *
 * @param sindec Sine of the solar declination.
 * @param t Start time (GMT, seconds).
 * @param dt Timestep duration (seconds).
 * @param sinlat Sine of latitude for each point.
 * @param longit Longitude of each point (radians).
 * @param points Number of points.
 * @param lit Sunlit fraction of the timestep, modified in-place.
 * @param cosz Mean cosine of the solar zenith angle, modified in-place.
 * @throws std::runtime_error If inputs are invalid (e.g., negative sizes, mismatched arrays).
 *
 * Written by J. Lean (January 1993), converted to C++ in 2025.
 */
void solang(double sindec, double t, double dt, const std::vector<double>& sinlat,
    const std::vector<double>& longit, int points, std::vector<double>& lit,
    std::vector<double>& cosz) {
    // Validate inputs
    if (points <= 0) {
        throw std::runtime_error("points must be positive");
    }
    if (dt <= 0.0 || t < 0.0) {
        throw std::runtime_error("dt must be positive and t non-negative");
    }
    if (sinlat.size() != static_cast<size_t>(points) ||
        longit.size() != static_cast<size_t>(points)) {
        throw std::runtime_error("sinlat and longit sizes must match points");
    }
    if (lit.size() != static_cast<size_t>(points) ||
        cosz.size() != static_cast<size_t>(points)) {
        throw std::runtime_error("lit and cosz sizes must match points");
    }

    // Constants
    constexpr double pi = 3.1415926535879323846;
    constexpr double pi_over_180 = pi / 180.0;
    constexpr double recip_pi_over_180 = 180.0 / pi;
    constexpr double twopi = 2.0 * pi;
    constexpr double s2r = pi / 43200.0;

    // Convert time to radians
    double trad = t * s2r - pi;
    double dtrad = dt * s2r;

    // Process each point
    for (size_t j = 0; j < static_cast<size_t>(points); ++j) {
        // Initialize variables
        double hld = 0.0; // Half-length of day, default to 0.0
        double sinsin = sindec * sinlat[j];
        double coscos = std::sqrt((1.0 - sindec * sindec) * (1.0 - sinlat[j] * sinlat[j]));
        double coshld = (coscos > 0.0) ? sinsin / coscos : 0.0;

        if (coshld < -1.0) { // Perpetual night
            lit[j] = 0.0;
            cosz[j] = 0.0;
        }
        else {
            double hat = longit[j] + trad; // Local hour angle
            double omega1, omega2;

            if (coshld > 1.0) { // Perpetual day
                omega1 = hat;
                omega2 = hat + dtrad;
            }
            else { // Partial day
                hld = std::acos(-coshld); // Compute hld for partial day
                double omegab = hat + hld;
                // Normalize omegab to [0, 2pi]
                while (omegab < 0.0) omegab += twopi;
                while (omegab >= twopi) omegab -= twopi;
                double omegae = omegab + dtrad;
                if (omegae > twopi) omegae -= twopi;
                double omegas = 2.0 * hld;

                // Set integration bounds
                if (omegab <= omegas || omegab < omegae) {
                    omega1 = omegab - hld;
                }
                else {
                    omega1 = -hld;
                }
                if (omegae <= omegas) {
                    omega2 = omegae - hld;
                }
                else {
                    omega2 = omegas - hld;
                }
                if (omegae > omegab && omegab > omegas) {
                    omega2 = omega1; // No sunlit period
                }
            }

            // Compute sunlit fraction and mean cosine
            double difsin = std::sin(omega2) - std::sin(omega1);
            double diftim = omega2 - omega1;

            // Handle case where sun sets and rises within timestep
            if (diftim < 0.0) {
                difsin += 2.0 * std::sqrt(1.0 - coshld * coshld);
                diftim += 2.0 * hld;
            }

            if (diftim == 0.0) {
                cosz[j] = 0.0;
                lit[j] = 0.0;
            }
            else {
                cosz[j] = difsin * coscos / diftim + sinsin;
                lit[j] = diftim / dtrad;
            }
        }
    }
}


/**
 * Calculates normalized solar radiation and time of maximum temperature.
 *
 * Computes solar radiation at each timestep and point, normalized by daily mean,
 * and estimates the GMT of maximum temperature based on sunrise and sunset.
 *
 * @param daynumber Day of the year (1 to 366).
 * @param jday Number of timesteps in the day.
 * @param points Number of spatial points.
 * @param year Calendar year.
 * @param lat Latitude of each point (degrees).
 * @param lon Longitude of each point (degrees).
 * @param sun Normalized solar radiation at each point and timestep, modified in-place.
 * @param time_max GMT of maximum temperature (hours), modified in-place.
 * @throws std::runtime_error If inputs are invalid (e.g., negative sizes, mismatched arrays).
 *
 * Written by Peter Cox (March 1996), converted to C++ in 2025.
 */
void sunny(int daynumber, int jday, int points, int year,
    const std::vector<double>& lat, const std::vector<double>& lon,
    std::vector<std::vector<double>>& sun, std::vector<double>& time_max) {
    // Validate inputs
    if (points <= 0 || jday <= 0) {
        throw std::runtime_error("points and jday must be positive");
    }
    if (daynumber < 1 || daynumber > 366) {
        throw std::runtime_error("daynumber must be between 1 and 366");
    }
    if (year < 0) {
        throw std::runtime_error("year must be non-negative");
    }
    if (lat.size() != static_cast<size_t>(points) ||
        lon.size() != static_cast<size_t>(points) ||
        time_max.size() != static_cast<size_t>(points)) {
        throw std::runtime_error("lat, lon, and time_max sizes must match points");
    }
//   if (sun.size() != static_cast<size_t>(points) ||
//    !std::all_of(sun.begin(), sun.end(), [jday](const std::vector<double>& row) {
//        return row.size() == static_cast<size_t>(jday);
//    })) {
//    throw std::runtime_error("sun must be a points x jday array");
//}

   if (sun.size() != static_cast<size_t>(points) ||
       !std::all_of(sun.begin(), sun.end(), [jday](const std::vector<double>& row) {
           return row.size() == static_cast<size_t>(jday);
           })) {
       throw std::runtime_error("sun must be a points x jday array");
   }


    // Constants
    constexpr double pi = 3.1415926535879323846;
    constexpr double pi_over_180 = pi / 180.0;
    constexpr double recip_pi_over_180 = 180.0 / pi;

    // Compute solar declination and solar constant
    double sindec, scs;
    solpos(daynumber, year, sindec, scs);

    // Initialize arrays
    std::vector<double> sinlat(points);
    std::vector<double> longrad(points);
    std::vector<double> coszm(points, 0.0);

    // Convert latitude and longitude to radians
    for (size_t i = 0; i < static_cast<size_t>(points); ++i) {
        double latrad = pi_over_180 * lat[i];
        longrad[i] = pi_over_180 * lon[i];
        sinlat[i] = std::sin(latrad);
    }

    double cosdec = std::sqrt(1.0 - sindec * sindec);
    double tandec = sindec / cosdec;
    double timestep = 86400.0 / static_cast<double>(jday);

    // Calculate COSZ and LIT for each timestep
    std::vector<double> lit(points);
    std::vector<double> cosz(points);
    for (size_t j = 0; j < static_cast<size_t>(jday); ++j) {
        double time = static_cast<double>(j) * timestep;
        solang(sindec, time, timestep, sinlat, longrad, points, lit, cosz);

        for (size_t i = 0; i < static_cast<size_t>(points); ++i) {
            sun[i][j] = cosz[i] * lit[i];
            coszm[i] += sun[i][j] / static_cast<double>(jday);
        }
    }

    // Normalize solar radiation
    for (size_t j = 0; j < static_cast<size_t>(jday); ++j) {
        for (size_t i = 0; i < static_cast<size_t>(points); ++i) {
            if (coszm[i] > 0.0) {
                sun[i][j] /= coszm[i];
            }
            else {
                sun[i][j] = 0.0;
            }
        }
    }

    // Calculate time of maximum temperature
    for (size_t i = 0; i < static_cast<size_t>(points); ++i) {
        double coslat = std::sqrt(1.0 - sinlat[i] * sinlat[i]);
        double tanlat = sinlat[i] / coslat;
        double tantan = tanlat * tandec;

        double time_up = 0.0, time_down = 0.0;
        if (std::abs(tantan) <= 1.0) { // Sun rises and sets
            double omega_up = -std::acos(-tantan);
            time_up = 0.5 * 24.0 * ((omega_up - longrad[i]) / pi + 1.0);
            double omega_down = std::acos(-tantan);
            time_down = 0.5 * 24.0 * ((omega_down - longrad[i]) / pi + 1.0);
        }
        else { // Perpetual day or night
            time_up = 0.0;
            time_down = 0.0;
        }

        time_max[i] = 0.5 * (time_up + time_down) + 0.15 * (time_down - time_up);
    }
}


/**
 * Generates a pseudo-random number by updating a set of four seed values.
 *
 * Follows the ITE model, updating seeds deterministically instead of using
 * a standard random number generator. The seeds are modified in-place, and
 * a random number in [0, 1) is computed.
 *
 * @param random_num The generated random number, modified in-place.
 * @param seed Array of four seed values, modified in-place.
 * @throws std::runtime_error If seed array size is not exactly 4.
 *
 * Converted to C++ in 2025.
 */
void rndm(double& random_num, std::vector<int>& seed) {
    // Validate input
    if (seed.size() != 4) {
        throw std::runtime_error("seed array must have exactly 4 elements");
    }

    // Update seeds
    seed[3] = 3 * seed[3] + seed[1];
    seed[2] = 3 * seed[2] + seed[0];
    seed[1] = 3 * seed[1];
    seed[0] = 3 * seed[0];

    // Normalize seeds with carry-over
    int i = static_cast<int>(seed[0] / 1000.0);
    seed[0] = seed[0] - i * 1000;
    seed[1] = seed[1] + i;

    i = static_cast<int>(seed[1] / 100.0);
    seed[1] = seed[1] - 100 * i;
    seed[2] = seed[2] + i;

    i = static_cast<int>(seed[2] / 1000.0);
    seed[2] = seed[2] - i * 1000;
    seed[3] = seed[3] + i;

    i = static_cast<int>(seed[3] / 100.0);
    seed[3] = seed[3] - 100 * i;

    // Compute random number
    random_num = (((static_cast<double>(seed[0]) * 0.001 + static_cast<double>(seed[1])) * 0.01 +
        static_cast<double>(seed[2])) * 0.001 + static_cast<double>(seed[3])) * 0.01;
}


/**
 * Calculates sub-daily variability for climate variables.
 *
 * @param pointsm Number of grid points.
 * @param step_day Number of sub-daily timesteps per day.
 * @param day_mon Number of days in a month.
 * @param sw_l Daily shortwave radiation (W/m^2).
 * @param precip_l Daily precipitation (mm/day).
 * @param t_l Daily temperature (K).
 * @param dtemp_day_l Daily diurnal temperature range (K).
 * @param lw_l Daily longwave radiation (W/m^2).
 * @param pstar_l Daily pressure (Pa).
 * @param wind_l Daily wind speed (m/s).
 * @param rh15m_l Daily relative humidity (%).
 * @param sw_sd Sub-daily shortwave radiation (W/m^2).
 * @param t_sd Sub-daily temperature (K).
 * @param lw_sd Sub-daily longwave radiation (W/m^2).
 * @param conv_rain_sd Sub-daily convective rain (mm/day).
 * @param ls_rain_sd Sub-daily large-scale rain (mm/day).
 * @param ls_snow_sd Sub-daily large-scale snow (mm/day).
 * @param pstar_sd Sub-daily pressure (Pa).
 * @param wind_sd Sub-daily wind speed (m/s).
 * @param qhum_sd Sub-daily humidity (kg/kg).
 * @param month Month of interest (1-based).
 * @param iday Day number in month (1-based).
 * @param lat Latitude (degrees).
 * @param longitude Longitude (degrees).
 * @param sec_day Seconds in a day.
 * @param nsdmax Maximum sub-daily timesteps.
 * @param seed_rain Seeding numbers for rainfall disaggregation.
 * @throws std::runtime_error If inputs are invalid or dependencies fail.
 *
 * Written by C. Huntingford (April 2001), based on P. Cox, converted to C++ in 2025.
 */
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
    int nsdmax, std::vector<int>& seed_rain) {
    // Validate inputs
    if (pointsm <= 0 || step_day <= 0 || day_mon <= 0 || sec_day <= 0 || nsdmax <= 0) {
        throw std::runtime_error("pointsm, step_day, day_mon, sec_day, and nsdmax must be positive");
    }
    if (sw_l.size() != static_cast<size_t>(pointsm) || sw_sd.size() != static_cast<size_t>(pointsm)) {
        throw std::runtime_error("Invalid array sizes");
    }
    if (month < 1 || iday < 1 || iday > day_mon) {
        throw std::runtime_error("Invalid month or iday");
    }

    // Constants
    constexpr double pi = 3.1415926535879323846;
    constexpr double temp_conv = 293.15; // Convective rain threshold (K)
    constexpr double temp_snow = 275.15; // Snow threshold (K)
    constexpr double max_precip_rate = 350.0; // Max precipitation rate (mm/day)

    // Precipitation durations
    double dur_conv_rain = 6.0; // Hours
    double dur_ls_rain = 1.0;   // Hours
    double dur_ls_snow = 1.0;   // Hours

    // Local variables
    double period_len = 24.0 / static_cast<double>(step_day);
    double timestep = static_cast<double>(sec_day) / static_cast<double>(step_day);

    std::vector<std::vector<int>> n_event(pointsm, std::vector<int>(nsdmax, 0));
    std::vector<int> n_event_local(nsdmax, 0);
    std::vector<double> prec_loc(nsdmax, 0.0);
    std::vector<double> t_sd_local(pointsm, 0.0);
    std::vector<double> pstar_sd_local(pointsm, 0.0);
    std::vector<double> qs_sd_local(pointsm, 0.0);
    std::vector<std::vector<double>> sun(pointsm, std::vector<double>(nsdmax, 0.0));
    std::vector<double> time_max(pointsm, 0.0);

    // Initialize output arrays
    for (int l = 0; l < pointsm; ++l) {
        for (int istep = 0; istep < step_day; ++istep) {
            conv_rain_sd[l][istep] = 0.0;
            ls_rain_sd[l][istep] = 0.0;
            ls_snow_sd[l][istep] = 0.0;
        }
    }


    if (step_day >= 2) {
        // Ensure durations are at least one period

        //std::cout << "Before adjustment:" << std::endl;
        //std::cout << "period_len     = " << period_len << std::endl;
        //std::cout << "dur_conv_rain  = " << dur_conv_rain << std::endl;
        //std::cout << "dur_ls_rain    = " << dur_ls_rain << std::endl;
        //std::cout << "dur_ls_snow    = " << dur_ls_snow << std::endl;

        if (dur_conv_rain <= period_len) dur_conv_rain = period_len + 1.0e-6;
        if (dur_ls_rain <= period_len) dur_ls_rain = period_len + 1.0e-6;
        if (dur_ls_snow <= period_len) dur_ls_snow = period_len + 1.0e-6;
        

        // Calculate diurnal cycle in solar radiation
        int daynumber = static_cast<int>((month - 1) * day_mon) + iday;
       
        sunny(daynumber, step_day, pointsm, 1990, lat, longitude, sun, time_max);

        // Loop over sub-daily timesteps
        for (int istep = 0; istep < step_day; ++istep) {
            double time_day = (istep + 0.5) * timestep;

            // Calculate diurnal variables
            for (int l = 0; l < pointsm; ++l) {
                t_sd[l][istep] = t_l[l] + 0.5 * dtemp_day_l[l] *
                    std::cos(2 * pi * (time_day - 3600.0 * time_max[l]) / sec_day);
                lw_sd[l][istep] = lw_l[l] * (4.0 * t_sd[l][istep] / t_l[l] - 3.0);
                sw_sd[l][istep] = sw_l[l] * sun[l][istep];
            }

            // Non-diurnal variables
            for (int l = 0; l < pointsm; ++l) {
                pstar_sd[l][istep] = pstar_l[l];
                wind_sd[l][istep] = wind_l[l];
            }

            // Humidity calculation
            for (int l = 0; l < pointsm; ++l) {
                pstar_sd_local[l] = pstar_sd[l][istep];
                t_sd_local[l] = t_sd[l][istep];
            }
            qsat(qs_sd_local, t_sd_local, pstar_sd_local, pointsm);
            for (int l = 0; l < pointsm; ++l) {
                qhum_sd[l][istep] = 0.01 * rh15m_l[l] * qs_sd_local[l];
            }
        }

        // Precipitation disaggregation
        for (int l = 0; l < pointsm; ++l) {
            double random_num_sd = 0;
            rndm(random_num_sd, seed_rain);

            // Reset local arrays
            std::fill(n_event_local.begin(), n_event_local.end(), 0);
            std::fill(prec_loc.begin(), prec_loc.end(), 0.0);

            int n_tally = 0;
            if (t_l[l] >= temp_conv) {
                // Convective rain
                double init_hour_conv_rain = random_num_sd * (24.0 - dur_conv_rain);
                double end_hour_conv_rain = init_hour_conv_rain + dur_conv_rain;

                for (int istep = 0; istep < step_day; ++istep) {
                    double hourevent = (istep + 0.5) * period_len;
                    if (hourevent >= init_hour_conv_rain && hourevent < end_hour_conv_rain) {
                        n_event[l][istep] = 1;
                        n_tally++;
                    }
                }

                for (int istep = 0; istep < step_day; ++istep) {
                    if (n_event[l][istep] == 1) {
                        conv_rain_sd[l][istep] = (static_cast<double>(step_day) / n_tally) * precip_l[l];
                        prec_loc[istep] = conv_rain_sd[l][istep];
                        n_event_local[istep] = n_event[l][istep];
                    }
                }

                redis(nsdmax, step_day, max_precip_rate, prec_loc, n_event_local, n_tally);
                for (int istep = 0; istep < step_day; ++istep) {
                    conv_rain_sd[l][istep] = prec_loc[istep];
                }
            }
            else if (t_l[l] < temp_conv && t_l[l] >= temp_snow) {
                // Large-scale rain
                double init_hour_ls_rain = random_num_sd * (24.0 - dur_ls_rain);
                double end_hour_ls_rain = init_hour_ls_rain + dur_ls_rain;

                for (int istep = 0; istep < step_day; ++istep) {
                    double hourevent = (istep + 0.5) * period_len;
                    if (hourevent >= init_hour_ls_rain && hourevent < end_hour_ls_rain) {
                        n_event[l][istep] = 1;
                        n_tally++;
                    }
                }

                for (int istep = 0; istep < step_day; ++istep) {
                    if (n_event[l][istep] == 1) {
                        ls_rain_sd[l][istep] = (static_cast<double>(step_day) / n_tally) * precip_l[l];
                        prec_loc[istep] = ls_rain_sd[l][istep];
                        n_event_local[istep] = n_event[l][istep];
                    }
                }

                redis(nsdmax, step_day, max_precip_rate, prec_loc, n_event_local, n_tally);
                for (int istep = 0; istep < step_day; ++istep) {
                    ls_rain_sd[l][istep] = prec_loc[istep];
                }
            }
            else {
                // Large-scale snow
                double init_hour_ls_snow = random_num_sd * (24.0 - dur_ls_snow);
                double end_hour_ls_snow = init_hour_ls_snow + dur_ls_snow;

                for (int istep = 0; istep < step_day; ++istep) {
                    double hourevent = (istep + 0.5) * period_len;
                    if (hourevent >= init_hour_ls_snow && hourevent < end_hour_ls_snow) {
                        n_event[l][istep] = 1;
                        n_tally++;
                    }
                }

                for (int istep = 0; istep < step_day; ++istep) {
                    if (n_event[l][istep] == 1) {
                        ls_snow_sd[l][istep] = (static_cast<double>(step_day) / n_tally) * precip_l[l];
                        prec_loc[istep] = ls_snow_sd[l][istep];
                        n_event_local[istep] = n_event[l][istep];
                    }
                }

                redis(nsdmax, step_day, max_precip_rate, prec_loc, n_event_local, n_tally);
                for (int istep = 0; istep < step_day; ++istep) {
                    ls_snow_sd[l][istep] = prec_loc[istep];
                }
            }
        }
    }
    else {
        // No sub-daily variation (step_day = 1)
       
        int istep = 0;

        for (int l = 0; l < pointsm; ++l) {
            pstar_sd_local[l] = pstar_sd[l][istep];
            t_sd_local[l] = t_sd[l][istep];
        }

        qsat(qs_sd_local, t_sd_local, pstar_sd_local, pointsm);

        for (int l = 0; l < pointsm; ++l) {
            sw_sd[l][istep] = sw_l[l];
            t_sd[l][istep] = t_l[l];
            lw_sd[l][istep] = lw_l[l];
            pstar_sd[l][istep] = pstar_l[l];
            wind_sd[l][istep] = wind_l[l];
            qhum_sd[l][istep] = 0.01 * rh15m_l[l] * qs_sd_local[l];

            if (t_l[l] >= temp_conv) {
                conv_rain_sd[l][istep] = precip_l[l];
            }
            else if (t_l[l] < temp_conv && t_l[l] >= temp_snow) {
                ls_rain_sd[l][istep] = precip_l[l];
            }
            else {
                ls_snow_sd[l][istep] = precip_l[l];
            }
        }
    }
}


/**
 * Combines climatology and anomalies to produce daily/sub-daily climate variables.
 *
 * @param anom If true, apply anomalies.
 * @param anlg If true, use GCM analogue model.
 * @param gpoints Number of land points.
 * @param mm Number of months.
 * @param md Number of days per month.
 * @param t_clim Control climate temperature (K).
 * @param sw_clim Control climate shortwave radiation (W/m^2).
 * @param lw_clim Control climate longwave radiation (W/m^2).
 * @param pstar_ha_clim Control climate pressure (hPa).
 * @param rh15m_clim Control climate relative humidity (%).
 * @param rainfall_clim Control climate rainfall (mm/day).
 * @param snowfall_clim Control climate snowfall (mm/day).
 * @param uwind_clim Control climate u-wind (m/s).
 * @param vwind_clim Control climate v-wind (m/s).
 * @param dtemp_clim Control climate diurnal temperature range (K).
 * @param f_wet_clim Control climate fraction wet.
 * @param t_anom Temperature anomalies (K).
 * @param sw_anom Shortwave radiation anomalies (W/m^2).
 * @param lw_anom Longwave radiation anomalies (W/m^2).
 * @param pstar_ha_anom Pressure anomalies (hPa).
 * @param rh15m_anom Relative humidity anomalies (%).
 * @param precip_anom Precipitation anomalies (mm/day).
 * @param uwind_anom U-wind anomalies (m/s).
 * @param vwind_anom V-wind anomalies (m/s).
 * @param dtemp_anom Diurnal temperature anomalies (K).
 * @param nsdmax Maximum sub-daily increments.
 * @param step_day Number of daily timesteps.
 * @param sec_day Number of seconds in a day.
 * @param lat Latitudinal positions (degrees).
 * @param longitude Longitudinal positions (degrees).
 * @param mdi Missing data indicator.
 * @return ClimCalcOutput Structure containing output climate variables and updated seed_rain.
 * @throws std::runtime_error If inputs are invalid or DAY_CALC fails.
 */
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
    const std::vector<double>& longitude, double mdi) {
    // Validate inputs
    if (gpoints <= 0 || mm <= 0 || md <= 0 || nsdmax <= 0 || step_day <= 0 || sec_day <= 0) {
        throw std::runtime_error("gpoints, mm, md, nsdmax, step_day, and sec_day must be positive");
    }
    if (t_clim.size() != static_cast<size_t>(gpoints) || t_clim[0].size() != static_cast<size_t>(mm)) {
        throw std::runtime_error("Invalid dimensions for input arrays");
    }

    // Initialize output structure
    ClimCalcOutput output;
    output.t_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.conv_rain_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.conv_snow_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.ls_rain_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.ls_snow_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.qhum_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.wind_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.pstar_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.sw_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
        mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.lw_out.resize(gpoints, std::vector<std::vector<std::vector<double>>>(
mm, std::vector<std::vector<double>>(md, std::vector<double>(nsdmax, 0.0))));
    output.dtemp_out.resize(gpoints, std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    output.seed_rain = seed_rain;

    // Local arrays
    std::vector<std::vector<std::vector<double>>> t_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> precip_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> rh15m_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> uwind_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> vwind_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> wind_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> dtemp_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> pstar_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> sw_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));
    std::vector<std::vector<std::vector<double>>> lw_daily(gpoints,
        std::vector<std::vector<double>>(mm, std::vector<double>(md, 0.0)));

    std::vector<double> sw_daily_local(gpoints, 0.0);
    std::vector<double> precip_daily_local(gpoints, 0.0);
    std::vector<double> t_daily_local(gpoints, 0.0);
    std::vector<double> dtemp_daily_local(gpoints, 0.0);
    std::vector<double> lw_daily_local(gpoints, 0.0);
    std::vector<double> pstar_daily_local(gpoints, 0.0);
    std::vector<double> wind_daily_local(gpoints, 0.0);
    std::vector<double> rh15m_daily_local(gpoints, 0.0);

    // Updated: 2D arrays for sub-daily outputs
    std::vector<std::vector<double>> sw_out_local(gpoints, std::vector<double>(nsdmax, 0.0));
    std::vector<std::vector<double>> t_out_local(gpoints, std::vector<double>(nsdmax, 0.0));
    std::vector<std::vector<double>> lw_out_local(gpoints, std::vector<double>(nsdmax, 0.0));
    std::vector<std::vector<double>> conv_rain_out_local(gpoints, std::vector<double>(nsdmax, 0.0));
    std::vector<std::vector<double>> ls_rain_out_local(gpoints, std::vector<double>(nsdmax, 0.0));
    std::vector<std::vector<double>> ls_snow_out_local(gpoints, std::vector<double>(nsdmax, 0.0));
    std::vector<std::vector<double>> pstar_out_local(gpoints, std::vector<double>(nsdmax, 0.0));
    std::vector<std::vector<double>> wind_out_local(gpoints, std::vector<double>(nsdmax, 0.0));
    std::vector<std::vector<double>> qhum_out_local(gpoints, std::vector<double>(nsdmax, 0.0));

    // Calculate monthly means and add anomalies
    for (int j = 0; j < mm; ++j) {
        for (int l = 0; l < gpoints; ++l) {
            for (int k = 0; k < md; ++k) {
                t_daily[l][j][k] = t_clim[l][j] + (anom ? t_anom[l][j] : 0.0);
                sw_daily[l][j][k] = sw_clim[l][j] + (anom ? sw_anom[l][j] : 0.0);
                rh15m_daily[l][j][k] = rh15m_clim[l][j] + (anom ? rh15m_anom[l][j] : 0.0);
                dtemp_daily[l][j][k] = dtemp_clim[l][j] + (anom ? dtemp_anom[l][j] : 0.0);

                precip_daily[l][j][k] = rainfall_clim[l][j] + snowfall_clim[l][j] +
                    (anom ? precip_anom[l][j] : 0.0);
                precip_daily[l][j][k] = std::max(precip_daily[l][j][k], 0.0);

                pstar_daily[l][j][k] = 100.0 * (pstar_ha_clim[l][j] +
                    (anom ? pstar_ha_anom[l][j] : 0.0));

                rh15m_daily[l][j][k] = std::min(rh15m_daily[l][j][k], 100.0);
                rh15m_daily[l][j][k] = std::max(rh15m_daily[l][j][k], 0.0);

                dtemp_daily[l][j][k] = std::max(dtemp_daily[l][j][k], 0.0);

                lw_daily[l][j][k] = lw_clim[l][j] + (anom ? lw_anom[l][j] : 0.0);

                uwind_daily[l][j][k] = uwind_clim[l][j] + (anom ? uwind_anom[l][j] : 0.0);
                vwind_daily[l][j][k] = vwind_clim[l][j] + (anom ? vwind_anom[l][j] : 0.0);
                wind_daily[l][j][k] = std::sqrt(uwind_daily[l][j][k] * uwind_daily[l][j][k] +
                    vwind_daily[l][j][k] * vwind_daily[l][j][k]);
                wind_daily[l][j][k] = std::max(wind_daily[l][j][k], 0.01);
            }
        }
    }

    // Disaggregate to sub-daily values
    for (int j = 0; j < mm; ++j) {
        for (int k = 0; k < md; ++k) {
            // Copy daily values to local arrays
            for (int l = 0; l < gpoints; ++l) {
                sw_daily_local[l] = sw_daily[l][j][k];
                precip_daily_local[l] = precip_daily[l][j][k];
                t_daily_local[l] = t_daily[l][j][k];
                dtemp_daily_local[l] = dtemp_daily[l][j][k];
                lw_daily_local[l] = lw_daily[l][j][k];
                pstar_daily_local[l] = pstar_daily[l][j][k];
                wind_daily_local[l] = wind_daily[l][j][k];
                rh15m_daily_local[l] = rh15m_daily[l][j][k];
            }

            // Call day_calc with 2D arrays
            day_calc(gpoints, step_day, md, sw_daily_local, precip_daily_local,
                t_daily_local, dtemp_daily_local, lw_daily_local,
                pstar_daily_local, wind_daily_local, rh15m_daily_local,
                sw_out_local, t_out_local, lw_out_local, conv_rain_out_local,
                ls_rain_out_local, ls_snow_out_local, pstar_out_local,
                wind_out_local, qhum_out_local, j + 1, k + 1, lat, longitude,
                sec_day, nsdmax, output.seed_rain);


            // Finalize outputs
            for (int l = 0; l < gpoints; ++l) {
                for (int istep = 0; istep < step_day; ++istep) {
                    output.sw_out[l][j][k][istep] = sw_out_local[l][istep];
                    output.t_out[l][j][k][istep] = t_out_local[l][istep];
                    output.lw_out[l][j][k][istep] = lw_out_local[l][istep];
                    output.conv_rain_out[l][j][k][istep] = conv_rain_out_local[l][istep];
                    output.conv_snow_out[l][j][k][istep] = 0.0;
                    output.ls_rain_out[l][j][k][istep] = ls_rain_out_local[l][istep];
                    output.ls_snow_out[l][j][k][istep] = ls_snow_out_local[l][istep];
                    output.pstar_out[l][j][k][istep] = pstar_out_local[l][istep];
                    output.wind_out[l][j][k][istep] = wind_out_local[l][istep];
                    output.qhum_out[l][j][k][istep] = qhum_out_local[l][istep];
                }
                for (int istep = step_day; istep < nsdmax; ++istep) {
                    output.sw_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                    output.t_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                    output.conv_rain_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                    output.conv_snow_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                    output.ls_rain_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                    output.ls_snow_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                    output.pstar_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                    output.wind_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                    output.qhum_out[l][j][k][istep] = std::numeric_limits<double>::quiet_NaN();
                }
                output.dtemp_out[l][j][k] = dtemp_daily[l][j][k];
            }
        }
    }

    return output;
}


/**
 * Models oceanic uptake of atmospheric CO2 based on Joos et al.
 *
 * Computes CO2 fluxes between atmosphere and ocean mixed layer, updating
 * atmospheric CO2 concentration due to ocean-atmosphere feedbacks.
 *
 * @param iyear Years since start of run.
 * @param year_co2 Years between updated atmospheric CO2 concentration.
 * @param co2_atmos_ppmv Atmospheric CO2 concentration (ppm).
 * @param co2_atmos_init_ppmv Initial atmospheric CO2 concentration (ppm).
 * @param dt_ocean Mixed-layer temperature anomaly (K).
 * @param fa_ocean CO2 fluxes from atmosphere to ocean (ppm/m^2/yr), modified in-place.
 * @param ocean_area Ocean area (m^2).
 * @param grad_co2_atmos_ppmv Gradient of atmospheric CO2 (ppm/yr).
 * @param year_run Number of years in simulation.
 * @param t_ocean_init Initial ocean surface temperature (K).
 * @param nfarray Size of fa_ocean array.
 * @param d_ocean_atmos Change in atmospheric CO2 due to ocean uptake (ppm), computed in-place.
 * @throws std::runtime_error If inputs are invalid or array size is too small.
 *
 * Written by Huntingford and Cox (March 1999), converted to C++ in 2025.
 */
void ocean_co2(int iyear, int year_co2, double co2_atmos_ppmv,
    double co2_atmos_init_ppmv, double dt_ocean,
    std::vector<double>& fa_ocean, double ocean_area,
    double grad_co2_atmos_ppmv, int year_run, double t_ocean_init,
    int nfarray, double& d_ocean_atmos) {
    // Validate inputs
    if (iyear < 0) {
        throw std::runtime_error("iyear must be non-negative");
    }
    if (year_co2 <= 0) {
        throw std::runtime_error("year_co2 must be positive");
    }
    if (year_run <= 0) {
        throw std::runtime_error("year_run must be positive");
    }
    if (ocean_area <= 0.0) {
        throw std::runtime_error("ocean_area must be positive");
    }
    if (fa_ocean.size() != static_cast<size_t>(nfarray)) {
        throw std::runtime_error("fa_ocean size must match nfarray");
    }

    // Constants
    constexpr int ncall_yr = 20;          // Calls per year
    constexpr double k_g = 0.1306;        // Gas exchange coefficient (/m^2/yr)
    constexpr double h = 40.0;            // Mixed-layer depth (m)
    constexpr double c = 1.722e17;        // Units conversion (umol m^3/ppm/kg)

    // Check array size
    if (year_run * ncall_yr > nfarray) {
        throw std::runtime_error("array size too small for fa_ocean");
    }

    // Initialize response function
    std::vector<double> rs(year_run * ncall_yr);
    response(ncall_yr, year_run, rs);

    // Initialize output
    d_ocean_atmos = 0.0;

    // Convert initial ocean temperature to Celsius
    double t_mixed_init = t_ocean_init - 273.15;

    // Compute timestep
    double timestep_co2 = 1.0 / static_cast<double>(ncall_yr);

    // Main loop over sub-timesteps
    for (int j = 1; j <= ncall_yr * year_co2; ++j) {
        int istep = (iyear - year_co2) * ncall_yr + j;

        // Assume initial ocean CO2 in equilibrium with atmosphere
        double co2_ocean_init = co2_atmos_init_ppmv;

        // Interpolate atmospheric CO2 on short timescale
        double co2_atmos_short = co2_atmos_ppmv +
            grad_co2_atmos_ppmv * (static_cast<double>(j) / ncall_yr - 0.5 * year_co2);
        double dco2_atmos = co2_atmos_short - co2_atmos_init_ppmv;

        // Compute perturbation in dissolved inorganic carbon (Joos Eqn 3)
        double dco2_ocean_mol = 0.0;
        if (istep >= 2) {
            for (int i = 1; i <= istep - 1; ++i) {
                dco2_ocean_mol += (c / h) * fa_ocean[i - 1] * rs[istep - i - 1] * timestep_co2;
            }
        }

        // Convert DCO2_OCEAN_MOL (umol/kg) to DCO2_OCEAN (ppm)
        double dco2_ocean =
            (1.5568 - 1.3993e-2 * t_mixed_init) * dco2_ocean_mol +
            (7.4706 - 0.20207 * t_mixed_init) * 1.0e-3 * (dco2_ocean_mol * dco2_ocean_mol) -
            (1.2748 - 0.12015 * t_mixed_init) * 1.0e-5 * (dco2_ocean_mol * dco2_ocean_mol * dco2_ocean_mol) +
            (2.4491 - 0.12639 * t_mixed_init) * 1.0e-7 * (dco2_ocean_mol * dco2_ocean_mol * dco2_ocean_mol * dco2_ocean_mol) -
            (1.5468 - 0.15326 * t_mixed_init) * 1.0e-10 * (dco2_ocean_mol * dco2_ocean_mol * dco2_ocean_mol * dco2_ocean_mol * dco2_ocean_mol);

        // Apply temperature correction
        double co2_ocean = (co2_ocean_init + dco2_ocean) * std::exp(0.0423 * dt_ocean);

        // Compute CO2 flux
        fa_ocean[istep - 1] = (k_g / ocean_area) * (co2_atmos_short - co2_ocean);

        // Update atmospheric CO2 change
        d_ocean_atmos -= fa_ocean[istep - 1] * ocean_area * timestep_co2;
    }
}


/**
 * Calculates effective radiative forcing from CH4, N2O, and CO2 mixing ratios.
 *
 * Implements FAIR model (Smith et al., 2018) to compute radiative forcing
 * contributions from CH4, N2O, and CO2, based on current and initial mixing ratios.
 *
 * @param ch4_ppbv CH4 mixing ratio (ppbv).
 * @param n2o_ppbv N2O mixing ratio (ppbv).
 * @param ch4_init_ppbv Initial CH4 mixing ratio (ppbv).
 * @param n2o_init_ppbv Initial N2O mixing ratio (ppbv).
 * @param co2_ppmv CO2 mixing ratio (ppmv).
 * @param co2_init_ppmv Initial CO2 mixing ratio (ppmv).
 * @param q_ch4 CH4 radiative forcing (W/m^2), computed in-place.
 * @param q_n2o N2O radiative forcing (W/m^2), computed in-place.
 * @param q_co2_fair CO2 radiative forcing (W/m^2), computed in-place.
 * @throws std::runtime_error If inputs are invalid.
 *
 * Written by Thomas Pugh and Peter Anthoni (November 2019), converted to C++ in 2025.
 */
void fair_non_co2_ghg(double ch4_ppbv, double n2o_ppbv, double ch4_init_ppbv,
    double n2o_init_ppbv, double co2_ppmv, double co2_init_ppmv,
    double& q_ch4, double& q_n2o, double& q_co2_fair) {
    // Validate inputs
    if (co2_ppmv <= 0.0 || co2_init_ppmv <= 0.0) {
        throw std::runtime_error("co2_ppmv and co2_init_ppmv must be positive");
    }
    if (ch4_ppbv < 0.0 || n2o_ppbv < 0.0 || ch4_init_ppbv < 0.0 || n2o_init_ppbv < 0.0) {
        throw std::runtime_error("mixing ratios must be non-negative");
    }

    // Compute CO2 radiative forcing
    double co2_sum = co2_ppmv + co2_init_ppmv;
    double n2o_sum = n2o_ppbv + n2o_init_ppbv;
    q_co2_fair = (-2.4e-7 * co2_sum * co2_sum + 7.2e-4 * co2_sum - 1.05e-4 * n2o_sum + 5.36) *
        std::log(co2_ppmv / co2_init_ppmv);

    // Compute N2O radiative forcing
    double ch4_sum = ch4_ppbv + ch4_init_ppbv;
    q_n2o = (-4.0e-6 * co2_sum + 2.1e-6 * n2o_sum - 2.45e-6 * ch4_sum + 0.117) *
        (std::sqrt(n2o_ppbv) - std::sqrt(n2o_init_ppbv));

    // Compute CH4 radiative forcing
    q_ch4 = (-6.5e-7 * ch4_sum - 4.1e-6 * n2o_sum + 0.043) *
        (std::sqrt(ch4_ppbv) - std::sqrt(ch4_init_ppbv));
}


/**
 * Updates CH4 and N2O mixing ratios using a simple box model.
 *
 * Implements FAIR model (Smith et al., 2018) to update atmospheric CH4 and N2O
 * mixing ratios based on emissions and decay lifetimes, incorporating anthropogenic
 * and optional LPJ-GUESS natural emissions.
 *
 * @param iyear Current year in the run.
 * @param nonco2_emissions_lpjg Whether to use LPJ-GUESS for natural CH4/N2O emissions.
 * @param yr_lpjg_nonco2 Years for LPJ-GUESS non-CO2 fluxes.
 * @param nyr_lpjg_flux Number of years in LPJ-GUESS flux data.
 * @param ch4_lpjg LPJ-GUESS CH4 fluxes (TgCH4/yr).
 * @param n2o_lpjg LPJ-GUESS N2O fluxes (TgN2O/yr).
 * @param yr_emiss Years for anthropogenic emissions.
 * @param nyr_emiss_nonco2 Number of years in emission data.
 * @param ch4_emiss Anthropogenic CH4 emissions (TgCH4/yr).
 * @param n2o_emiss Anthropogenic N2O emissions (TgN2O/yr).
 * @param ch4_ppbv CH4 mixing ratio (ppbv), updated in-place.
 * @param n2o_ppbv N2O mixing ratio (ppbv), updated in-place.
 * @param tau_decay_ch4 Atmospheric lifetime of CH4 (years).
 * @param tau_decay_n2o Atmospheric lifetime of N2O (years).
 * @param dir_common Directory for shared input/output files.
 * @param this_year String representation of current year.
 * @throws std::runtime_error If inputs are invalid or emission data mismatches.
 *
 * Written by Thomas Pugh and Peter Anthoni (November 2019), converted to C++ in 2025.
 */
void fair_non_co2_ghg_budget(int iyear, bool nonco2_emissions_lpjg,
    const std::vector<int>& yr_lpjg_nonco2, int nyr_lpjg_flux,
    const std::vector<double>& ch4_lpjg, const std::vector<double>& n2o_lpjg,
    const std::vector<int>& yr_emiss, int nyr_emiss_nonco2,
    const std::vector<double>& ch4_emiss, const std::vector<double>& n2o_emiss,
    double& ch4_ppbv, double& n2o_ppbv,
    double tau_decay_ch4, double tau_decay_n2o,
    const std::string& dir_common, const std::string& this_year) {
    // Constants
    constexpr double mm_air = 28.9647;    // Molar mass of air (g/mol)
    constexpr double mm_ch4 = 16.04;      // Molar mass of CH4 (g/mol)
    constexpr double mm_n2o = 44.01;      // Molar mass of N2O (g/mol)
    constexpr double mm_n2 = 2 * 14.0067; // Molar mass of N2 (g/mol)
    constexpr double ma = 5.1352e18;      // Mass of atmosphere (kg)

    // Validate inputs
    if (iyear < 0) {
        throw std::runtime_error("iyear must be non-negative");
    }
    if (nyr_emiss_nonco2 <= 0) {
        throw std::runtime_error("nyr_emiss_nonco2 must be positive");
    }
    if (nonco2_emissions_lpjg && nyr_lpjg_flux <= 0) {
        throw std::runtime_error("nyr_lpjg_flux must be positive when using LPJ-GUESS");
    }
    if (tau_decay_ch4 <= 0.0 || tau_decay_n2o <= 0.0) {
        throw std::runtime_error("tau_decay_ch4 and tau_decay_n2o must be positive");
    }
    if (yr_emiss.size() < static_cast<size_t>(nyr_emiss_nonco2) ||
        ch4_emiss.size() < static_cast<size_t>(nyr_emiss_nonco2) ||
        n2o_emiss.size() < static_cast<size_t>(nyr_emiss_nonco2)) {
        throw std::runtime_error("emission arrays too small for nyr_emiss_nonco2");
    }
    if (nonco2_emissions_lpjg &&
        (yr_lpjg_nonco2.size() < static_cast<size_t>(nyr_lpjg_flux) ||
            ch4_lpjg.size() < static_cast<size_t>(nyr_lpjg_flux) ||
            n2o_lpjg.size() < static_cast<size_t>(nyr_lpjg_flux))) {
        throw std::runtime_error("LPJ-GUESS arrays too small for nyr_lpjg_flux");
    }

    // Convert mixing ratios to molar mixing ratios
    double ch4_ppbv_in = ch4_ppbv * 1.0e-9;
    double n2o_ppbv_in = n2o_ppbv * 1.0e-9;

    // Find anthropogenic emissions for iyear-1
    double ch4_emiss_local = 0.0;
    double n2o_emiss_local = 0.0;
    int emiss_tally = 0;
    for (int n = 0; n < nyr_emiss_nonco2; ++n) {
        if (yr_emiss[n] == iyear) { //Check should be iyear-1?
            ch4_emiss_local = ch4_emiss[n];
            n2o_emiss_local = n2o_emiss[n];
            ++emiss_tally;
        }
    }

    if (emiss_tally != 1) {
        std::string error_file = dir_common + "/IMOGEN/output/" + this_year + "/error";
        std::ofstream out(error_file);
        out << "Non-CO2 emission dataset does not match run\n";
        out.close();
        throw std::runtime_error("Non-CO2 emission dataset does not match run");
    }

    // Add LPJ-GUESS emissions if enabled
    if (nonco2_emissions_lpjg) {
        emiss_tally = 0;
        for (int n = 0; n < nyr_lpjg_flux; ++n) {
            if (yr_lpjg_nonco2[n] == iyear) {//Check should be iyear-1?
                ch4_emiss_local += ch4_lpjg[n];
                n2o_emiss_local += n2o_lpjg[n];
                ++emiss_tally;
            }
        }

        if (emiss_tally != 1) {
            std::string error_file = dir_common + "/IMOGEN/output/" + this_year + "/error";
            std::ofstream out(error_file);
            out << "LPJG non-CO2 flux dataset does not match run. Year: " << iyear - 1
                << ", Tally: " << emiss_tally << "\n";
            out.close();
            throw std::runtime_error("LPJG non-CO2 flux dataset does not match run");
        }
    }

    // Convert emissions to kg/yr
    ch4_emiss_local *= 1.0e12 / 1.0e3; // TgCH4/yr to kgCH4/yr
    n2o_emiss_local *= (mm_n2 / mm_n2o) * (1.0e12 / 1.0e3); // TgN2O/yr to kgN2/yr

    // Compute molar mixing ratio increments (Eq. 4)
    double dghg_dt_ch4 = ch4_emiss_local / ma * mm_air / mm_ch4;
    double dghg_dt_n2o = n2o_emiss_local / ma * mm_air / mm_n2;

    // Update mixing ratios (Eq. 5, simplified)
    ch4_ppbv = ch4_ppbv_in + dghg_dt_ch4 - ch4_ppbv_in * (1.0 - std::exp(-1.0 / tau_decay_ch4));
    n2o_ppbv = n2o_ppbv_in + dghg_dt_n2o - n2o_ppbv_in * (1.0 - std::exp(-1.0 / tau_decay_n2o));

    // Convert back to ppbv
    ch4_ppbv *= 1.0e9;
    n2o_ppbv *= 1.0e9;
}


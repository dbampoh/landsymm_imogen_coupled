#include "intermediary.h"
#include <iomanip>
#include <iostream>
#include <sstream>
#include <fstream>
#include <unordered_map>
#include <map>
#include <vector>
#include <cmath>
#include <algorithm>
using namespace std;


std::string scenario;

std::map<std::string, std::string> config;

std::vector<std::string> ssps, rcps;

int firstyear, lastyear;

std::string baseDirectory, pathToLogFile;

std::string myPLUMDataFilePath;

std::string lpjgOutputDirectory;

std::string methaneEmissionOutputFilePath;

// File path for file containing methane emissions from enteric fermentation
std::string entericFermentationMethaneOutputFilePath;

// File path for file containing methane emissions from manure management systems
std::string manureManagementMethaneOutputFilePath;

// File path for file containing total nitrogen emissions
std::string nitrogenEmissionOutputFilePath;

// File path for file conatining nitrogen emissions from fertilizer
std::string historic_nitrogen_fertiizer_file_path;

// File path for file conatining nitrogen emissions from fertilizer
std::string arable_lands_nitrogen_fertilizer_path;

// File path for file containing total methane and total nitrogen emissions in one file
std::string methaneNitrogenTotalOutputFilePath;

// File path for file containing wetland areas
std::string wetlandsAreaFilePath;

// File path for file containing methane emissions from wetlands
std::string wetlandsMethaneEmissionsOutputPath;

// Folder path for plum land use data v1
std::string basePathPLUMdata;

// Folder path for plum land use data v2
std::string basePathPLUMdata_v2;

// File path for PLUM pre-processed fertilizer emissions output path
std::string plumFertilizerOutputPath;

// File path for file containing modelled nitrogen and methane emissions
std::string file_LPJG_IPCC_Path;

// File path for preprocessed plum fertilizers
std::string plumFertlizerPath;

// File path for LPJG methane
std::string lpjgMethane;

// File path for LPJG nitrogen
std::string lpjgNitrogen;

// File path for LPJG cflux
std::string lpjgCflux;

// File path for LPJG clfux + IIASA co2
std::string lpjgCflux_plus_IIASA_lpjg_co2;

// File path for LPJG co2 replacement (IIASA corresponding version)
std::string IIASA_lpjg_co2_file_path;

// File path for component of IIASA not simulated by LPJG and IPCC (ch4 and n2o only)
std::string IIASA_non_lpjg_1850_2100;

// File path for component of IIASA simulated by LPJG and IPCC (ch4 and n2o only)
std::string IIASA_lpjg_1850_2100;

// File path to OWI livestock counts
std::string livestock_counts_path;

// File path to FAO fertilizer and arable land data
std::string fao_stats_path;

int lpjg_start_year, lpjg_end_year;

bool simulate_ipcc_fao_owi_rice_cultivation_methane_emissions = false;

Adder::Adder()
{
	std::cout << "Adder constructor invoked. Remember to set file path before calling print() " << endl;
}

Adder::Adder(string total_methane_nitrogen_file_output_file_path, string IIASA_non_lpjg_1850_2009_file_path, string IIASA_lpjg_1850_2009_file_path, string filePath_LPJG_IPCC_only, string lpjgcflux_plus_iiasa_lpjg_co2, string IIASA_lpjg_co2_file)
{
	setTotalMethaneNitrogenFilePath(total_methane_nitrogen_file_output_file_path);
	set_IIASA_non_lpjg_1850_2100_file_path(IIASA_non_lpjg_1850_2009_file_path);
	file_LPJG_IPCC_only = filePath_LPJG_IPCC_only;
	lpjgcflux_plus_iiasa_lpjg_co2_file_path = lpjgcflux_plus_iiasa_lpjg_co2;
	IIASA_lpjg_co2_file_path = IIASA_lpjg_co2_file;

	set_IIASA_lpjg_1850_2100_file_path(IIASA_lpjg_1850_2009_file_path);
	read_IIASA_lpjg_1850_2010();
	read_IIASA_non_lpjg_1850_2010();
	read_IIASA_co2_lpjg_1850_2100();
}

Adder::~Adder()
{
	std::cout << "Adder destructor invoked " << endl;
	std::cout << "FINISHED" << endl;
}

void Adder::startAddition(vector<dataHolder1>& LPJGCfluxData, vector<dataHolder1>& IPCCMethane, vector<dataHolder1>& WetlandsMethane, vector<dataHolder1>& LPJGMethane, vector<dataHolder1>& LPJGNitrogen, vector<dataHolder1>& IPCCNitrogen, vector<dataHolder1>& Historic_methane_1961_2009, vector<dataHolder1>& Historic_nitrogen_1961_2009)
{

	std::cout << "Verifiying size of component vectors" << endl;
	std::cout << "IPCCMethane_2010_2100: " << IPCCMethane.size() << endl;						// 91
	std::cout << "IPCCNitrogen_2010_2100: " << IPCCNitrogen.size() << endl;						// 91
	std::cout << "LPJGMethane_1961_2100: " << LPJGMethane.size() << endl;						// 140
	std::cout << "LPJGNitrogen_1961_2100: " << LPJGNitrogen.size() << endl;						// 140
	std::cout << "Historic_methane_1961_2009: " << Historic_methane_1961_2009.size() << endl;	// 49
	std::cout << "Historic_nitrogen_1961_2009: " << Historic_nitrogen_1961_2009.size() << endl; // 49

	int vecSize = lastyear - firstyear + 1;
	// 251 for cmip5
	// 111 for cmip6

	myTotalMethaneData.resize(vecSize);
	myTotalNitrogenData.resize(vecSize);
	total_combined_iiasa_historic_1850_1960_lpjg__ipcc_fao_1961_2100.resize(vecSize);
	myLPJG_IPCC_Wetlands_only_methane.resize(vecSize);
	myLPJG_IPCC_Wetlands_only_nitrogen.resize(vecSize);
	cflux_iiasa_co2_1850_1960_lpjg_2100.resize(vecSize);

	// where full iiasa data starts. scenario dependent
	int where_full_iiasa_covers_backwards = 0;
	int region_for_lpjg_ipcc_histroic_start = 0;
	int region_for_lpjg_ipcc_histroic_end = 0;
	int benchmark_to_zero_arrays_or_to_step_midway = 0;

	if (scenario == "cmip5")
	{
		where_full_iiasa_covers_backwards = 1961;
		region_for_lpjg_ipcc_histroic_start = 1960;
		region_for_lpjg_ipcc_histroic_end = 2010;
		benchmark_to_zero_arrays_or_to_step_midway = 111;
	}

	// cmip6 dataset starts at 1991
	if (scenario == "cmip6")
	{
		where_full_iiasa_covers_backwards = 1990;
		region_for_lpjg_ipcc_histroic_start = 1989;
		region_for_lpjg_ipcc_histroic_end = 2010;
		benchmark_to_zero_arrays_or_to_step_midway = -29;
	}

	for (int i = firstyear; i <= lastyear; i++)
	{

		if (i < where_full_iiasa_covers_backwards)
		{

			myTotalMethaneData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value1 + IIASA_lpjg_1850_2100[i - firstyear].value1;
			myTotalNitrogenData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value2 + IIASA_lpjg_1850_2100[i - firstyear].value2;

			myLPJG_IPCC_Wetlands_only_methane[i - firstyear].value = IIASA_lpjg_1850_2100[i - firstyear].value1;
			myLPJG_IPCC_Wetlands_only_nitrogen[i - firstyear].value = IIASA_lpjg_1850_2100[i - firstyear].value2;
			cflux_iiasa_co2_1850_1960_lpjg_2100[i - firstyear].value = IIASA_lpjg_co2[i - firstyear].value;
		}

		// Region for LPJG historic + ipcc histroic (owi +fao)
		else if (i > region_for_lpjg_ipcc_histroic_start && i < region_for_lpjg_ipcc_histroic_end)
		{
			myTotalMethaneData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value1 + Historic_methane_1961_2009[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value + LPJGMethane[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
			//+ WetlandsMethane[i-1850-111].value; - removed methane here since LPJG is already producing it | 30.05.2023
			myTotalNitrogenData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value2 + Historic_nitrogen_1961_2009[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value + LPJGNitrogen[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;

			myLPJG_IPCC_Wetlands_only_methane[i - firstyear].value = Historic_methane_1961_2009[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value + LPJGMethane[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
			//+ WetlandsMethane[i-1850-111].value;
			myLPJG_IPCC_Wetlands_only_nitrogen[i - firstyear].value = Historic_nitrogen_1961_2009[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value + LPJGNitrogen[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
			cflux_iiasa_co2_1850_1960_lpjg_2100[i - firstyear].value = LPJGCfluxData[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
		}
		else
		{

			myTotalMethaneData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value1 + IPCCMethane[i - firstyear - 160].value + LPJGMethane[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
			//+ WetlandsMethane[i - 1850 - 111].value; - removed methane here since LPJG is producing it now | 30.05.2023
			myTotalNitrogenData[i - firstyear].value = IIASA_non_lpjg_1850_2100[i - firstyear].value2 + IPCCNitrogen[i - firstyear - 160].value + LPJGNitrogen[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;

			myLPJG_IPCC_Wetlands_only_methane[i - firstyear].value = IPCCMethane[i - firstyear - 160].value + LPJGMethane[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
			//+ WetlandsMethane[i - 1850 - 111].value;
			myLPJG_IPCC_Wetlands_only_nitrogen[i - firstyear].value = IPCCNitrogen[i - firstyear - 160].value + LPJGNitrogen[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
			cflux_iiasa_co2_1850_1960_lpjg_2100[i - firstyear].value = LPJGCfluxData[i - firstyear - benchmark_to_zero_arrays_or_to_step_midway].value;
		}
	}

	// perform smoothening throughout
	// vector<double> myBuffer_methane(myTotalMethaneData.size());
	// vector<double> myBuffer_nitrogen(myTotalNitrogenData.size());

	// // fill buffer
	// for (int i = 0; i < myBuffer_methane.size(); i++)
	// {
	// 	myBuffer_methane[i] = myTotalMethaneData[i].value; // 1850->0
	// }

	// for (int i = 0; i < myBuffer_nitrogen.size(); i++)
	// {
	// 	myBuffer_nitrogen[i] = myTotalNitrogenData[i].value; // 1850->0
	// }

	// int window = 16;
	// int half_window = window / 2;
	// int number_of_times_to_smoothen = 2;

	// // smoothen data nTimes
	// for (int i = 0; i < number_of_times_to_smoothen; i++)
	// {
	// 	myBuffer_methane = centeredMovingAverage(myBuffer_methane, window);
	// 	myBuffer_nitrogen = centeredMovingAverage(myBuffer_nitrogen, window);
	// }

	// // concatenate back
	// std::cout << "Printing out methane" << endl;
	// for (int i = 0; i < myBuffer_methane.size(); i++)
	// {
	// 	std::cout << myBuffer_methane[i] << endl;
	// }

	// std::cout << "Prinitng out nitrogen" << endl;
	// for (int i = 0; i < myBuffer_nitrogen.size(); i++)
	// {
	// 	std::cout << myBuffer_nitrogen[i] << endl;
	// }

	// // system("pause");
	// // fill in

	// for (int i = 0; i < myBuffer_methane.size() - window; i++)
	// {
	// 	myTotalMethaneData[i + half_window].value = myBuffer_methane[i + half_window];
	// }

	// for (int i = 0; i < myBuffer_nitrogen.size() - window; i++)
	// {
	// 	myTotalNitrogenData[i + half_window].value = myBuffer_nitrogen[i + half_window];
	// }

	for (int i = firstyear; i <= lastyear; i++)
	{
		total_combined_iiasa_historic_1850_1960_lpjg__ipcc_fao_1961_2100[i - firstyear].year = i;
		total_combined_iiasa_historic_1850_1960_lpjg__ipcc_fao_1961_2100[i - firstyear].value1 = myTotalMethaneData[i - firstyear].value;
		total_combined_iiasa_historic_1850_1960_lpjg__ipcc_fao_1961_2100[i - firstyear].value2 = myTotalNitrogenData[i - firstyear].value;

		// fit in years for cflux vector
		cflux_iiasa_co2_1850_1960_lpjg_2100[i - firstyear].year = i;
	}

	myFileManager.printToConsole(total_combined_iiasa_historic_1850_1960_lpjg__ipcc_fao_1961_2100);

	// put LPJG_IPCC_only methane and nitrogen into one vector
	LPJG_IPCC_Only_Methane_Nitrogen.resize(vecSize);

	std::cout << "Printing methane to console" << endl;
	myFileManager.printToConsole(myLPJG_IPCC_Wetlands_only_methane);

	std::cout << "Printing nitrogen to console" << endl;
	myFileManager.printToConsole(myLPJG_IPCC_Wetlands_only_nitrogen);

	for (int i = firstyear; i <= lastyear; i++)
	{
		LPJG_IPCC_Only_Methane_Nitrogen[i - firstyear].year = i;
		LPJG_IPCC_Only_Methane_Nitrogen[i - firstyear].value1 = myLPJG_IPCC_Wetlands_only_methane[i - firstyear].value;
		LPJG_IPCC_Only_Methane_Nitrogen[i - firstyear].value2 = myLPJG_IPCC_Wetlands_only_nitrogen[i - firstyear].value;
	}
}

void Adder::PrintTotalMethaneNitrogenToFile()
{

	std::cout << "File_LPJG_only: " << file_LPJG_IPCC_only << endl;
	// system("pause");

	myFileManager.printToFile(fileTotalMethaneNitrogenPath, total_combined_iiasa_historic_1850_1960_lpjg__ipcc_fao_1961_2100);
	myFileManager.printToFile(file_LPJG_IPCC_only, LPJG_IPCC_Only_Methane_Nitrogen);
	myFileManager.printToFile(lpjgcflux_plus_iiasa_lpjg_co2_file_path, cflux_iiasa_co2_1850_1960_lpjg_2100);
}

void Adder::setTotalMethaneNitrogenFilePath(string path)
{
	fileTotalMethaneNitrogenPath = path;
}

void Adder::read_IIASA_non_lpjg_1850_2010()
{
	IIASA_non_lpjg_1850_2100 = myFileManager.loadFile3(IIASA_non_lpjg_1850_2100_file_path);
}

void Adder::read_IIASA_co2_lpjg_1850_2100()
{
	IIASA_lpjg_co2 = myFileManager.loadFile2(IIASA_lpjg_co2_file_path);
}

void Adder::set_IIASA_non_lpjg_1850_2100_file_path(string path)
{
	IIASA_non_lpjg_1850_2100_file_path = path;
}

void Adder::read_IIASA_lpjg_1850_2010()
{
	IIASA_lpjg_1850_2100 = myFileManager.loadFile3(IIASA_lpjg_1850_2100_file_path);
}

void Adder::set_IIASA_lpjg_1850_2100_file_path(string path)
{
	IIASA_lpjg_1850_2100_file_path = path;
}

void Adder::set_actual_lpjg_simulated_IIASA_1850_2009_lpjg_2010_2100()
{

	int vecSize = lastyear = firstyear + 1;
	actual_lpjg_simulated_IIASA_1850_2009_lpjg_2010_2100.resize(vecSize);
	for (int i = firstyear; i <= lastyear; i++)
	{

		if (i < 2010)
		{

			actual_lpjg_simulated_IIASA_1850_2009_lpjg_2010_2100[i - firstyear] = IIASA_lpjg_1850_2100[i - firstyear];
		}

		if (i > 2009)
		{
			actual_lpjg_simulated_IIASA_1850_2009_lpjg_2010_2100[i - firstyear] = myTotalData_lpjg_ipcc_sim_calc[i - firstyear - 160];
		}
	}
}

std::vector<double> Adder::centeredMovingAverage(std::vector<double> data, int window_size)
{
	std::vector<double> smoothed_data(data.size());
	int half_window = window_size / 2;

	// Add padding to the beginning and end of the data
	std::vector<double> padded_data(data.size() + window_size - 1);
	for (int i = 0; i < half_window; i++)
	{
		padded_data[i] = data[0];
	}
	for (int i = half_window; i < padded_data.size() - half_window; i++)
	{
		padded_data[i] = data[i - half_window];
	}
	for (int i = padded_data.size() - half_window; i < padded_data.size(); i++)
	{
		padded_data[i] = data[data.size() - 1];
	}

	double sum = 0;
	for (int i = 0; i < window_size; i++)
	{
		sum += padded_data[i];
	}
	for (int i = half_window; i < data.size() - half_window; i++)
	{
		smoothed_data[i] = sum / window_size;
		sum += padded_data[i + half_window] - padded_data[i - half_window];
	}
	return smoothed_data;
}

vector<dataHolder2> Adder::get_total_data_iiasa_historic_lpjg_sim()
{
	return total_combined_iiasa_historic_1850_1960_lpjg__ipcc_fao_1961_2100;
}




Calculator::Calculator()
{
	cout << "Calculator constructor invoked" << endl;
	// loadCountries();
}

Calculator::~Calculator()
{
	cout << "\nCalculator destructor invoked!" << endl;
}

void Calculator::loadCountries()
{

	const string fileName = "C:\\GitHub\\LPJ_IMOGEN_coupling\\IPCC\\data\\countries.txt";
	cout << "Loading countries from file: " << fileName << endl;
	ifstream myReader(fileName);

	if (!myReader.is_open())
	{
		cout << "Database connection to" << fileName << "error!" << endl;
		exit(200);
	}
	else
	{
		while (myReader.good())
		{
			string temp = " ";
			getline(myReader, temp);
			myCountries.push_back(temp);
		}
	}
	cout << "The size of the countries vector is: " << myCountries.size() << endl;
	myReader.close();
}

double Calculator::calcCH4EntericFermentation(string country, string animal, double nHeads)
{

	double emmission_factor_for_enteric_fermentation = myMaps.getEmissionFactorForMethaneEmissionFromEntericfermentation(country, animal);

	double ch4_enteric_fermentation = (emmission_factor_for_enteric_fermentation * nHeads) / 1000000.0;

	return ch4_enteric_fermentation;
}

double Calculator::calcCH4ManureManagement(string country, string animal, int nHeads)
{

	double methane_manure_management = 0.0;
	string region = myMaps.getRegionOfCountry(country);
	string ClimateofCountry = myMaps.getClimateofRegion(region);
	string animalCategory = myMaps.getAnimalCategoryForTypicalAnimalMass(animal); // using same map beacuse it's applicable here

	double VolatileSolidExcretion = myMaps.getVolatileSolidExcretionRate(region, animal);

	for (auto pair : myMaps.AWMS[animalCategory][region])
	{

		methane_manure_management += (nHeads * VolatileSolidExcretion) * (pair.second * myMaps.MAP_EMISSION_FACTOR_FOR_METHANE_BY_MANURE_MANAGEMENT_SYSTEM[animalCategory][pair.first][ClimateofCountry]) / 1000.0;
	}

	return methane_manure_management;
}

double Calculator::calcVolalileSolidExcretion(double volatile_solid_excretion_rate, double typical_animal_mass) const
{
	return (volatile_solid_excretion_rate * typical_animal_mass) * (365 / 1000.0);
}

double Calculator::calcNitrogenExcretion(double nitrogen_excretion_rate, double animalMass)
{
	return (nitrogen_excretion_rate * animalMass) * (1000.0 / 365.0);
}

double Calculator::calcN20ManureManagement(int nHeads, string country, string animal)
{

	double annual_nitrogen_input_via_codigestate = 0.0;

	double n20_emmission_from_manure_management = 0.0;
	string region = myMaps.getRegionOfCountry(country);
	string climate = myMaps.getClimateofRegion(region);
	string animalCategory = myMaps.getAnimalCategoryForTypicalAnimalMass(animal); // applicable here
	double animalMass = myMaps.getTypicalAnimalMass(animal, country);

	string animalCategoryForNitrogenExcretion = myMaps.getAnimalCategoryforVolatileSolidExcretionRate(animal);

	double nitrogenExcretionRate = myMaps.getNitrogenExcretionRate(country, animal);

	double nitrogenExcretion = calcNitrogenExcretion(nitrogenExcretionRate, animalMass);

	for (auto pair : myMaps.AWMS[animalCategory][region])
	{
		n20_emmission_from_manure_management += (((nHeads * nitrogenExcretion) * (pair.second) + annual_nitrogen_input_via_codigestate) * (myMaps.getEmissionFactorNitrogenEmissionsFromManureMangement(pair.first)) * (44.0 / 28.0));
	}

	return n20_emmission_from_manure_management;
}

double Calculator::calcN2OManagedSoils(double FSN_FON_total_fertilizer, double EF1_avg, double EF1FR, double EF2_avg, double FOS_area_drained_soils, double FPRP_organic_fert, double EF3_avg)
{
	double N2O_N_inputs, N2O_N_OS, N2O_N_PRP, results;

	N2O_N_inputs = (FSN_FON_total_fertilizer * EF1_avg);

	results = N2O_N_inputs * (44.0 / 28.0) * CONVERT_Kg_TO_Tg;

	return results;
}

double Calculator::calcCH4Wetlands(double diffusiveEmissionRate, double area, int ice_free_period)
{
	return ice_free_period * diffusiveEmissionRate * area * 1e-6 * 100 * 0.001; // units: TgCH4/yr
	// 1e-6 is from IPCC formula, 100 converts from ha to sqkm, 0.001 converts from Gg to Tg
}


// Implementation file for Extractor.h
Extractor::Extractor()
{

	cout << "\nExtractor Constructed Invoked!. Remeber to set output directory" << endl;
}

Extractor::Extractor(string path, int firsthistyear, int lasthistyear)
{
	setOutputDirectory(path);
	cfluxFilePath = myOutputDirectory + "cflux.out";
	nitrogenFilePath = myOutputDirectory + "ngases.out";
	methaneFilepath = myOutputDirectory + "mch4.out";

	myFirstHistYear = firsthistyear;
	myLastHistYear = lasthistyear;
}

Extractor::~Extractor()
{
	cout << "\nExtractor Destructor invoked!" << endl;
}

void Extractor::setOutputDirectory(string path)
{
	myOutputDirectory = path;
}

void Extractor::startLPJGDataExtraction()
{

	fstream myReader = myFileManager.openFile(cfluxFilePath); // got the stream/. Cflux file opened

	// resize vectors
	int nyears = lpjg_end_year - lpjg_start_year + 1;
	myLPJGMethane.resize(nyears);
	myLPJGNitrogen.resize(nyears);
	myLPJGCflux.resize(nyears);

	string temp;

	myReader.ignore(10000, '\n'); // ignore headers
	while (myReader.good())
	{

		myReader >> temp;
		myReadCflux.lon = atof(temp.c_str());
		// cout << myCflux.lon << endl;

		myReader >> temp;
		myReadCflux.lat = atof(temp.c_str());
		// cout << myCflux.lat << endl;

		myReader >> temp;
		myReadCflux.year = atoi(temp.c_str());
		// cout << " cflux year: "<<myReadCflux.year << endl;

		myReader >> temp; // manure

		myReader >> temp;
		myReadCflux.veg = atof(temp.c_str());
		// cout << myCflux.veg << endl;

		myReader >> temp;
		myReadCflux.repr = atof(temp.c_str());
		// cout << myCflux.repr << endl;

		myReader >> temp;
		myReadCflux.soil = atof(temp.c_str());
		// cout << myCflux.soil << endl;

		myReader >> temp;
		myReadCflux.fire = atof(temp.c_str());
		// cout << myCflux.fire << endl;

		myReader >> temp;
		myReadCflux.est = atof(temp.c_str());
		// cout << myCflux.est << endl;

		// Dummy seed, harvest, LU_ch, Slow_h
		myReader >> temp;
		myReader >> temp;
		myReader >> temp;
		myReader >> temp;
		// Dummy seed, harvest, LU_ch, Slow_h

		myReader >> temp;
		myReadCflux.nee = atof(temp.c_str());
		// cout << "cflux on line: "<<myReadCflux.nee << endl; //grabbed the data here. Main stuff

		// ended here
		if (myReadCflux.year > (lpjg_start_year - 1))
		{
			myLPJGCflux[myReadCflux.year - lpjg_start_year].year = myReadCflux.year;
			myLPJGCflux[myReadCflux.year - lpjg_start_year].value += myReadCflux.nee * cdtarea(myReadCflux.lat, myReadCflux.lon, 1.25, 1.25) * CONVERT_g_Tg;
		}
	}

	// myFileManager.printToConsole(myLPJGCflux);
	myFileManager.closeFile(myReader);

	myReader = myFileManager.openFile(nitrogenFilePath);
	while (myReader.good())
	{

		myReader >> temp;
		myReadNitrogen.lon = atof(temp.c_str());
		// cout << myNgases.lon << endl;

		myReader >> temp;
		myReadNitrogen.lat = atof(temp.c_str());
		// cout << myNgases.lat << endl;

		myReader >> temp;
		myReadNitrogen.year = atoi(temp.c_str());
		// cout << myNgases.year << endl;

		myReader >> temp;
		myReadNitrogen.NH3_fire = atof(temp.c_str());
		// cout << myNgases.NH3_fire << endl;

		myReader >> temp;
		myReadNitrogen.NH3_soil = atof(temp.c_str());
		// cout << myNgases.NH3_soil << endl;

		myReader >> temp;
		myReadNitrogen.NOx_fire = atof(temp.c_str());
		// cout << myNgases.NOx_fire << endl;

		myReader >> temp;
		myReadNitrogen.NOx_soil = atof(temp.c_str());
		// cout << myNgases.NOx_soil << endl;

		myReader >> temp;
		myReadNitrogen.N20_fire = atof(temp.c_str());
		// cout << myNgases.N20_fire << endl;

		myReader >> temp;
		myReadNitrogen.N20_soil = atof(temp.c_str());
		// cout << myNgases.N20_soil << endl;

		myReader >> temp;
		myReadNitrogen.N2_fire = atof(temp.c_str());
		// cout << myNgases.N2_fire << endl;

		myReader >> temp;
		myReadNitrogen.N2_soil = atof(temp.c_str());
		// cout << myNgases.N2_soil << endl;

		myReader >> temp;
		myReadNitrogen.total = atof(temp.c_str());
		// cout <<  "nitrogen on line: "<< myReadNitrogen.total << endl;

		myReadNitrogen.sum_ngases = myReadNitrogen.N20_soil + myReadNitrogen.N20_fire;

		if (myReadNitrogen.year > (lpjg_start_year - 1))
		{
			myLPJGNitrogen[myReadNitrogen.year - lpjg_start_year].year = myReadNitrogen.year;
			myLPJGNitrogen[myReadNitrogen.year - lpjg_start_year].value += myReadNitrogen.sum_ngases * cdtarea(myReadNitrogen.lat, myReadNitrogen.lon, 1.25, 1.25) * CONVERT_Kg_Tg * 1e-4; // to convert from ha to m2
		}
	}
	// myFileManager.printToConsole(myLPJGNitrogen);
	myFileManager.closeFile(myReader);

	myReader = myFileManager.openFile(methaneFilepath);

	while (myReader.good())
	{

		myReader >> temp;
		myReadMethane.lon = atof(temp.c_str());
		// cout << myCH4.lon << endl;

		myReader >> temp;
		myReadMethane.lat = atof(temp.c_str());
		// cout << myCH4.lat << endl;

		myReader >> temp;
		myReadMethane.year = atoi(temp.c_str());
		// cout << "methane year: "<<myReadMethane.year << endl;

		myReader >> temp;
		myReadMethane.jan = atof(temp.c_str());
		// cout << myCH4.jan << endl;

		myReader >> temp;
		myReadMethane.feb = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.mar = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.apr = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.may = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.jun = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.jul = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.aug = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.sep = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.oct = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.nov = atof(temp.c_str());

		myReader >> temp;
		myReadMethane.dec = atof(temp.c_str());

		myReadMethane.sum_ch4 = myReadMethane.jan + myReadMethane.feb + myReadMethane.mar + myReadMethane.apr + myReadMethane.may + myReadMethane.jun + myReadMethane.jul + myReadMethane.aug + myReadMethane.sep + myReadMethane.oct + myReadMethane.nov + myReadMethane.dec;

		if (myReadMethane.year > (lpjg_start_year - 1))
		{
			myLPJGMethane[myReadMethane.year - lpjg_start_year].year = myReadMethane.year;
			myLPJGMethane[myReadMethane.year - lpjg_start_year].value += myReadMethane.sum_ch4 * cdtarea(myReadMethane.lat, myReadMethane.lon, 1.25, 1.25) * CONVERT_g_Tg;
		}
	}
	// myFileManager.printToConsole(myLPJGMethane);

	myFileManager.closeFile(myReader);
}

vector<dataHolder1> Extractor::getLPJGMethaneData()
{
	return myLPJGMethane;
}

vector<dataHolder1> Extractor::getLPJGNitrogenData()
{
	return myLPJGNitrogen;
}

vector<dataHolder1> Extractor::getLPJGCfluxData()
{
	return myLPJGCflux;
}

double Extractor::calcGridCellArea(double lon, double lat)
{
	return 1e06;
}

void Extractor::printLPJGEmissionsData(string methanePath, string nitrogenPath, string cfluxPath)
{

	myFileManager.printToFile(methanePath, myLPJGMethane);
	myFileManager.printToFile(nitrogenPath, myLPJGNitrogen);
	myFileManager.printToFile(cfluxPath, myLPJGCflux);
}

double Extractor::earth_radius(double lat, const std::string& unit)
{

	// returns latitudinal earth radius in metres
	double r = 6371000.0; // default radius in meters

	bool kilometers = false;
	if (unit == "km")
	{
		kilometers = true;
	}

	const double a = 6378137.0;         // equatorial radius
	const double b = 6356752.0;         // polar radius
	double latitude = lat * PI / 180.0; // Convert to radians
	r = (pow(a * a * cos(latitude), 2) + pow(b * b * sin(latitude), 2)) /
		(pow(a * cos(latitude), 2) + pow(b * sin(latitude), 2));
	r = sqrt(r);

	if (kilometers)
	{
		r /= 1000.0;
	}

	return r;
}

double Extractor::cdtarea(double lat, double lon, double dlat, double dlon, bool km2)
{
	std::string unit = km2 ? "km" : "";
	double R = earth_radius(lat, unit); // Get Earth's radius at the given latitude

	double dy = dlat * R * PI / 180.0;
	double dx = (dlon / 180.0) * PI * R * cos(lat * PI / 180.0);

	return std::abs(dx * dy);
}


FileManager::~FileManager() { //destructor
	cout << "File Manager destroyed!" << endl;
}

FileManager::FileManager() {
	cout << "File Manager constructed!" << endl;
}

fstream FileManager::openFile(string fileName, bool read) const {

	fstream myStream;
	if (read) {
		myStream.open(fileName, ios::in);
		cout << "\nAttempting to open File: " << fileName << endl;
	}
	else {
		myStream.open(fileName, ios::out);
		cout << "\nAttempting to open File: " << fileName << " opened" << endl;
	}

	if (read && !myStream.is_open()) {
		cout << "\nThe file: " << fileName << " failed to open!" << endl;
		exit(100);
	}

	return myStream;
}

void FileManager::closeFile(fstream& myStream) const {
	myStream.close();
	cout << "File closed! " << endl;
}

vector<dataHolder1> FileManager::loadFile2(string fileName)const {
	fstream myStream = openFile(fileName, true); //file opened
	int year;
	cout << "\nReading file: " << fileName << endl;
	vector<dataHolder1>myData;
	double value;
	while (!myStream.eof()) {
		//start reading here
		myStream >> year >> value;
		myData.push_back(dataHolder1(year, value));
	}
	cout << "\nCompleted reading file: " << fileName << " |vector size: " << myData.size() << endl;
	closeFile(myStream);
	return myData;
}

vector<dataHolder2>FileManager::loadFile3(string fileName) const {
	vector<dataHolder2>myData;
	fstream myStream = openFile(fileName, true); //file opened
	int year;
	double value1, value2;
	while (!myStream.eof()) {
		//start reading here
		myStream >> year >> value1 >> value2;
		myData.push_back(dataHolder2(year, value1, value2));
	}
	cout << "\nCompleted reading file: " << fileName << " |vector size: " << myData.size() << endl;
	closeFile(myStream);

	return myData;
}

void FileManager::loadFileCSV() const {


}

void FileManager::deleteFile(string filePath) const {
	const string command = "del " + filePath;
	system(command.c_str());

}

void FileManager::deleteFolder(string folderPath) const {


}

void FileManager::printToFile(string filePath, vector<dataHolder1>myVector, int precision)const {
	cout << "Writng to file: " << filePath << endl;
	fstream myWriter = openFile(filePath, false);
	myWriter << fixed << setprecision(precision);

	for (int i = 0; i < myVector.size(); i++) {
		myWriter << setw(6) << myVector[i].year << " " << setw(10) << myVector[i].value << endl;
	}
	closeFile(myWriter);
}

void FileManager::printToFile(string filePath, vector<dataHolder2>myVector, int precision)const {
	cout << "Writng to file: " << filePath << endl;
	fstream myWriter = openFile(filePath, false);
	myWriter << fixed << setprecision(precision);

	for (int i = 0; i < myVector.size(); i++) {
		myWriter << myVector[i].year << " " << setw(9) << myVector[i].value1 << " " << setw(9) << myVector[i].value2 << endl;
	}

}

void FileManager::printToConsole(vector<dataHolder1>myVector)const {
	if (myVector.empty()) {
		cout << "Vector is empty. Nothing to print!" << endl;
		exit(200);
	}
	else {
		for (int i = 0; i < myVector.size(); i++) {
			cout << fixed << myVector[i].year << " " << myVector[i].value << endl;
		}
	}
}

void FileManager::printToConsole(vector<dataHolder2>myVector)const {
	if (myVector.empty()) {
		cout << "Vector is empty. Nothing to print!" << endl;
		exit(200);
	}
	else {
		for (int i = 0; i < myVector.size(); i++) {
			cout << fixed << myVector[i].year << " " << myVector[i].value1 << " " << myVector[i].value2 << endl;
		}
	}
}


string Maps::getRegionOfCountry(string country)
{
	return MAP_CONVERT_COUNTRIES_TO_REGIONS[country];
}

string Maps::getAnimalCategoryforVolatileSolidExcretionRate(string animal)
{
	return MAP_FOR_ANIMAL_CATEGORY_FOR_VSE_RATE[animal];
}

double Maps::getVolatileSolidExcretionRate(string country, string animal)
{
	string animalCategory = getAnimalCategoryforVolatileSolidExcretionRate(animal);
	string region = getRegionOfCountry(country);

	return MAP_FOR_VOLATILE_SOLID_EXCRETION_RATE[region][animalCategory];
}

string Maps::getAnimalCategoryForTypicalAnimalMass(string animal)
{
	return MAP_FOR_ANIMAL_CATEGORIES_TYPICAL_ANIMAL_MASS[animal];
}

double Maps::getTypicalAnimalMass(string animal, string country)
{
	string animalCategoryForTypicalAnimalMass = getAnimalCategoryForTypicalAnimalMass(animal);
	string region = getRegionOfCountry(country);
	return MAP_WEIGHTS_FOR_ANIMAL_CATEGORIES[animalCategoryForTypicalAnimalMass][region];
}

string Maps::getAnimalCategoryforFRACGAS(string animal)
{
	return MAP_ANIMAL_TO_ANIMAL_CATEGORY_FOR_FRACGAS[animal];
}

string Maps::getClimateofRegion(string region)
{
	return MAP_REGIONS_TO_CLIMATE[region];
}

double Maps::getFRACGAS(string manureSytem, string animalCategory)
{
	return MAP_FRACGAS[manureSytem][animalCategory];
}

double Maps::getNitrogenExcretionRate(string country, string animal)
{
	string region = getRegionOfCountry(country);
	string animalCategory = getAnimalCategoryforVolatileSolidExcretionRate(animal);

	return MAP_NITROGEN_EXCRETION_RATE[region][animalCategory];
}

double Maps::getEmissionFactorNitrogenEmissionsFromManureMangement(string manure_management_system)
{
	return MAP_EMISSION_FACTOR_FOR_N2O_FROM_MANURE_MANAGEMENT[manure_management_system];
}

double Maps::getEmissionFactorForMethaneEmissionFromEntericfermentation(string country, string animal)
{
	double emissionFactor = 0.0;

	string region = getRegionOfCountry(country);
	string animalCategory = MAP_ANIMAL_CATEGORIES_FOR_ENTERIC_FERMENTATION[animal];
	emissionFactor = MAP_ENTERIC_FERMENTATION_EMISSION_FACTORS_FOR_BUFFALO_CATTLE[region][animalCategory];

	return emissionFactor;
}

string Maps::getClimateforCountryWetlands(string country)
{
	return MAP_WETLANDS_COUNTRIES_CLIMATE[country];
}

double Maps::getDiffusiveEmissionFactorForWetlands(string country)
{
	string climate = getClimateforCountryWetlands(country);
	return MAP_WETLANDS_CLIMATE_TO_DIFFUSION_EMISSION_FACTORS[climate];
}



MethaneEmissions::MethaneEmissions()
{
	cout << "Default constructor for methane emissions invoked!" << endl;
	cout << "Remember to set output file path" << endl;

	if (!simulate_ipcc_fao_owi_rice_cultivation_methane_emissions)
	{
		cout << "Warning!!! Rice cultivation methane emissions from IPCC + FAO + OWI turned off" << endl;
	}
}

MethaneEmissions::MethaneEmissions(string path)
{
	cout << "\nCustom contructor for Methane emissions invoked!" << endl;
	PLUMdataFilePath = path;

	if (!simulate_ipcc_fao_owi_rice_cultivation_methane_emissions)
	{
		cout << "Warning!!! Rice cultivation methane emissions from IPCC + FAO + OWI turned off" << endl;
	}
}

MethaneEmissions::~MethaneEmissions()
{
	cout << "\nDestructor for methane emissions invoked" << endl;
}

vector<dataHolder1> MethaneEmissions::getMethaneData()
{
	return myCH4Data;
}

void MethaneEmissions::startCalculation_methane_modelled_historic_1961_2009()
{

	myHistoricMethane_modelled_1961_2009.resize(49);
	fstream myStream = myFileManager.openFile(historic_livestock_counts_1961_2100_path);

	myStream.ignore(10000, '\n'); // ignore headers
	string line, temp;
	int year_to_start_reading = 1961;

	string FAO_items[10] = { "Asses", "Meat buffalo", "Meat cattle", "Meat goat", "Horses", "Mules", "Meat pig", "Meat sheep", "Turkey", "Meat Poultry" };

	while (getline(myStream, line))
	{

		stringstream ss(line); // string stream

		getline(ss, temp, ','); // country
		myPLUMData.country = temp;

		getline(ss, temp, ','); // code || N/A

		getline(ss, temp, ','); // year

		myPLUMData.year = stoi(temp);

		// Check
		//  if (myPLUMData.country == "World")
		//  {
		//  	cout << "World data here" << endl;
		//  }

		// Changed to use only the World data
		if ((myPLUMData.year > 1960 && myPLUMData.year < 2010) && myPLUMData.country != "World") // exclude World data
		{
			// set year
			myHistoricMethane_modelled_1961_2009[myPLUMData.year - year_to_start_reading].year = myPLUMData.year;

			// loop through FAO items, same in livestock-counts.csv and calculates emissions
			for (int i = 0; i < 10; i++)
			{

				// set the value and compute
				myPLUMData.item = FAO_items[i];

				getline(ss, temp, ',');
				myPLUMData.nheads = atof(temp.c_str());

				cout << "Value: " << myPLUMData.nheads << endl;
				// nheads
				myHistoricMethane_modelled_1961_2009[myPLUMData.year - year_to_start_reading].value += myCalculator.calcCH4EntericFermentation(myPLUMData.country, myPLUMData.item, myPLUMData.nheads) * CONVERT_Gg_TO_Tg;				   // units: GgCH4/yr
				myHistoricMethane_modelled_1961_2009[myPLUMData.year - year_to_start_reading].value += myCalculator.calcCH4ManureManagement(myPLUMData.country, myPLUMData.item, myPLUMData.nheads) * CONVERT_Kg_TO_Gg * CONVERT_Gg_TO_Tg; // units:

				//cout << "The sum of the two calc values is: " << myHistoricMethane_modelled_1961_2009[myPLUMData.year - year_to_start_reading].value << endl;
			}
		}
	}

	myFileManager.closeFile(myStream);

	// RICE CULTIVATION EMISSIONS
	myStream = myFileManager.openFile(rice_cultivation_emissions_file_path);
	cout << "FAO, OUR-WORLD IN DATA DRIVEN HISTROIC(1961-2009)-IPCC MODELLING ONGOING" << endl;

	myStream.ignore(10000, '\n');
	while (getline(myStream, line))
	{

		stringstream ss(line);

		getline(ss, myRiceMethaneData.domainCode, ',');
		getline(ss, myRiceMethaneData.domain, ',');
		getline(ss, myRiceMethaneData.areaCode, ',');
		getline(ss, myRiceMethaneData.Area, ',');
		getline(ss, myRiceMethaneData.elementCode, ',');
		getline(ss, myRiceMethaneData.element, ',');
		getline(ss, myRiceMethaneData.itemCode, ',');
		getline(ss, myRiceMethaneData.item, ',');
		getline(ss, myRiceMethaneData.yearCode, ',');
		getline(ss, temp, ',');

		myRiceMethaneData.year = stoi(temp); // year

		getline(ss, myRiceMethaneData.unit, ',');
		getline(ss, myRiceMethaneData.value, ',');
		getline(ss, myRiceMethaneData.flag, ',');
		getline(ss, myRiceMethaneData.flagDescription, ',');

		getline(ss, temp, '\n'); // methane emissions

		myRiceMethaneData.methaneEmissions = atof(temp.c_str()) * CONVERT_Gg_TO_Tg;

		// Turned rice cultivation emissions off here because LPJG simulates rice cultivation
		if (simulate_ipcc_fao_owi_rice_cultivation_methane_emissions)

		{ // Changed to use only the World data
			if (myRiceMethaneData.element == "Area harvested" && (myRiceMethaneData.year > 1960 && myRiceMethaneData.year < 2010) && myRiceMethaneData.Area == "World")
			{
				myHistoricMethane_modelled_1961_2009[myRiceMethaneData.year - year_to_start_reading].value += myRiceMethaneData.methaneEmissions;
			}
		}
		else
		{
			// do nothing
		}
	}

	// myFileManager.printToConsole(myHistoricMethane_modelled_1961_2009);
}

void MethaneEmissions::startCalculation_methane_scenario_2010_2100()
{

	fstream myReader = myFileManager.openFile(PLUMdataFilePath, true); // file opened
	string line, temp;
	double totalMethaneEmissionsPerLine = 0.0;
	double totalMethaneEmissionsPerYear = 0.0;
	double totalEntericFermentationMethaneEmissionsPerYear = 0.0;
	double totalManureMangementMethaneEmissionsPerYear = 0.0;

	cout << "CH4 Calculation with PLUM-IPCC (2010-2100) guidelines ongoing...Please wait" << endl;

	while (getline(myReader, line))
	{
		stringstream ss(line);	// line extracted
		getline(ss, temp, ','); // first column extracted = year

		myPLUMData.year = stoi(temp); // push year to plum data struct

		getline(ss, temp, ','); // get next data = countr
		myPLUMData.country = temp;

		getline(ss, temp, ','); // get next data = animal
		myPLUMData.item = temp;

		getline(ss, temp, ','); // get next data = nHeads in millions
		myPLUMData.nheads = stof(temp) * MILLION;

		double methane_enteric_fermentation_per_line = myCalculator.calcCH4EntericFermentation(myPLUMData.country, myPLUMData.item, myPLUMData.nheads); // units: GgCH4/yr

		double methane_manure_management_per_line = myCalculator.calcCH4ManureManagement(myPLUMData.country, myPLUMData.item, myPLUMData.nheads) * CONVERT_Kg_TO_Gg; // units: GgCH4/yr (after conversion)

		totalMethaneEmissionsPerLine = (methane_enteric_fermentation_per_line + methane_manure_management_per_line) * CONVERT_Gg_TO_Tg; // units = TgCH4/yr

		if (myPLUMData.year == yearTracker)
		{
			totalEntericFermentationMethaneEmissionsPerYear += (methane_enteric_fermentation_per_line * CONVERT_Gg_TO_Tg);
			totalManureMangementMethaneEmissionsPerYear += (methane_manure_management_per_line * CONVERT_Gg_TO_Tg);
			totalMethaneEmissionsPerYear += totalMethaneEmissionsPerLine;
		}
		else
		{
			myEntericCH4Data.push_back(dataHolder1(yearTracker, totalEntericFermentationMethaneEmissionsPerYear));
			myManureManagementCH4Data.push_back(dataHolder1(yearTracker, totalManureMangementMethaneEmissionsPerYear));
			myCH4Data.push_back(dataHolder1(yearTracker, totalMethaneEmissionsPerYear));
			yearTracker++;

			// reinitialize variables
			totalMethaneEmissionsPerYear = 0.0;
			totalEntericFermentationMethaneEmissionsPerYear = 0.0;
			totalManureMangementMethaneEmissionsPerYear = 0.0;
		}
	}
	myCH4Data.push_back(dataHolder1(yearTracker, totalMethaneEmissionsPerYear));
	myEntericCH4Data.push_back(dataHolder1(yearTracker, totalEntericFermentationMethaneEmissionsPerYear));
	myManureManagementCH4Data.push_back(dataHolder1(yearTracker, totalManureMangementMethaneEmissionsPerYear));
}

void MethaneEmissions::startCalculations()
{

	startCalculation_methane_modelled_historic_1961_2009(); // starts historic modelling (1961-2009)

	startCalculation_methane_scenario_2010_2100(); // starts scenario modelling (2010-2100)
}

void MethaneEmissions::setPLUMDataFilePath(string path)
{
	PLUMdataFilePath = path;
}

int MethaneEmissions::getYearTrackKeeper()
{
	return yearTracker;
}

void MethaneEmissions::setYearTrackkeeper(int value)
{
	yearTracker = value;
}

void MethaneEmissions::setMethaneEmissionsOutputFilePaths(string entericFilePath, string manureManagementFilePath, string totalFilePath)
{

	entericFermentationMethaneEmissionsOutputFilePath = entericFilePath;
	manureManagementMethaneEmissionsOutputFilePath = manureManagementFilePath;
	methaneEmissionsOutputFilePath = totalFilePath;
}

void MethaneEmissions::printMethaneEmissions()
{
	if (methaneEmissionsOutputFilePath == " ")
	{
		cout << "Output File Path for methane emissions not set!" << endl;
	}
	else
	{
		myFileManager.printToFile(methaneEmissionsOutputFilePath, myCH4Data);
	}
}

void MethaneEmissions::printEntericFermentationMethaneEmissions()
{

	if (entericFermentationMethaneEmissionsOutputFilePath == " ")
	{
		cout << "Output File Path for enteric fermenation methane emissions not set!" << endl;
	}
	else
	{
		myFileManager.printToFile(entericFermentationMethaneEmissionsOutputFilePath, myEntericCH4Data);
	}
}

void MethaneEmissions::printManureManagementMethaneEmissions()
{

	if (manureManagementMethaneEmissionsOutputFilePath == " ")
	{
		cout << "Output File Path for manure management methane emissions not set!" << endl;
	}
	else
	{
		myFileManager.printToFile(manureManagementMethaneEmissionsOutputFilePath, myManureManagementCH4Data);
	}
}

vector<dataHolder1> MethaneEmissions::getEntericFermentationMethane()
{
	return myEntericCH4Data;
}

vector<dataHolder1> MethaneEmissions::getManureManagementMethane()
{
	return myManureManagementCH4Data;
}

void MethaneEmissions::setAuxFilePath(string livestocks_counts_path, string fao_stats_path)
{
	historic_livestock_counts_1961_2100_path = livestocks_counts_path;
	rice_cultivation_emissions_file_path = fao_stats_path;
}

vector<dataHolder1> MethaneEmissions::get_historic_methane_1961_2009()
{
	return myHistoricMethane_modelled_1961_2009;
}


NitrogenEmissions::NitrogenEmissions()
{
	cout << "\nNitrogen Emmissions Contructor Invoked" << endl;

	if (!simulate_nitrogen_emissions_from_fertilizer_application)
	{
		cout << "WARNING!!! Nitrogen emissions from fertilizer application turned off!!" << endl;
	}
}

NitrogenEmissions::~NitrogenEmissions()
{
	cout << "\nNitrogen Emmissions Destructor Invoked" << endl;

	if (!simulate_nitrogen_emissions_from_fertilizer_application)
	{
		cout << "WARNING!!! Nitrogen emissions from fertilizer application turned off!!" << endl;
	}
}

NitrogenEmissions::NitrogenEmissions(string plumPath, string fertFilePath)
{
	setPLUMDataFilePath(plumPath);
	setFertDataFilePath(fertFilePath);
	cout << "my fert file path " << plumFertlizerPath << endl;
}

vector<dataHolder1> NitrogenEmissions::getNitrogenData()
{
	return myN2OData;
}

void NitrogenEmissions::startCalculations()
{
	startCalculations_historic_nitrogen_1961_2009();
	startCalculation_nitrogen_scenario_2010_2100();

	// myFileManager.printToConsole(modelled_historic_nitrogen_1961_2009);
}

void NitrogenEmissions::startCalculation_nitrogen_scenario_2010_2100()
{

	fstream myReader = myFileManager.openFile(PLUMdataFilePath, true); // file opened
	string line, temp;
	double totalNitrogenEmissionsPerLine = 0.0;
	double totalNitrogenEmissionsPerYear = 0.0;

	cout << "\nN2O Calculation with PLUM-IPCC guidelines ongoing...Please wait" << endl;

	while (getline(myReader, line))
	{
		stringstream ss(line);	// line extracted
		getline(ss, temp, ','); // first column extracted = year

		myPLUMData.year = stoi(temp); // push year to plum data struct

		getline(ss, temp, ','); // get next data = country
		myPLUMData.country = temp;

		getline(ss, temp, ','); // get next data = animal
		myPLUMData.item = temp;

		getline(ss, temp, ','); // get next data = nHeads in millions
		myPLUMData.nheads = stof(temp) * 1000000;
		// cout << "nheads:" << myPLUMData.nheads << endl;

		double nitrogen_emission_manure_managemnt = myCalculator.calcN20ManureManagement(myPLUMData.nheads, myPLUMData.country, myPLUMData.item); // units = KgN2O/yr

		// cout << "nitr on line: " << nitrogen_emission_manure_managemnt << endl;

		totalNitrogenEmissionsPerLine = nitrogen_emission_manure_managemnt * CONVERT_Kg_TO_Tg; // units = TgCH4/yr

		if (myPLUMData.year == yearTracker)
		{
			totalNitrogenEmissionsPerYear += totalNitrogenEmissionsPerLine;
		}
		else
		{

			myN2OData.push_back(dataHolder1(yearTracker, totalNitrogenEmissionsPerYear));
			yearTracker++;
			totalNitrogenEmissionsPerYear = 0.0; // reinitialize total
		}
	}
	myN2OData.push_back(dataHolder1(yearTracker, totalNitrogenEmissionsPerYear));
	myFileManager.closeFile(myReader);
	// Done with IPCC nitrogen emissions from manure managment

	// Turned nitrogen emissions off here because Daniel said LPJG simulaes rice cultivation on 31/10/2023
	if (simulate_nitrogen_emissions_from_fertilizer_application)
	{

		// Start N20 from fertilizer
		myPlumDataProcessor.setplumFertlizerPath(plumFertlizerPath);
		myPlumDataProcessor.readFertilizerData(); // gets into PLUM fertilizer data
		vector<dataHolder1> totalFertilizerAmount = myPlumDataProcessor.getTotalFertilizerAmounts();

		for (int i = 0; i < totalFertilizerAmount.size(); i++)
		{
			myN2ODataManagedSoils.push_back(dataHolder1(totalFertilizerAmount[i].year, myCalculator.calcN2OManagedSoils(totalFertilizerAmount[i].value)));
		}
		for (int i = 0; i < myN2ODataManagedSoils.size(); i++)
		{
			myN2OData[i].value += myN2ODataManagedSoils[i].value;
		}
	}
	else
	{

		// do nothing here
	}
}

void NitrogenEmissions::startCalculations_historic_nitrogen_1961_2009()
{

	modelled_historic_nitrogen_1961_2009.resize(49);
	fstream myStream = myFileManager.openFile(historic_livestock_counts_1961_2100_path);

	myStream.ignore(10000, '\n'); // ignore headers
	string line, temp;
	int year_to_start_reading = 1961;

	string FAO_items[10] = { "Asses", "Meat buffalo", "Meat cattle", "Meat goat", "Horses", "Mules", "Meat pig", "Meat sheep", "Turkey", "Meat Poultry" };

	while (getline(myStream, line))
	{

		stringstream ss(line); // string stream

		getline(ss, temp, ','); // country
		myPLUMData.country = temp;

		getline(ss, temp, ','); // code || N/A

		getline(ss, temp, ','); // year

		myPLUMData.year = stoi(temp);

		if (myPLUMData.year > 1960 && myPLUMData.year < 2010)
		{
			// set year
			modelled_historic_nitrogen_1961_2009[myPLUMData.year - year_to_start_reading].year = myPLUMData.year;

			// loop through FAO items, same in livestock-counts.csv and calculates emissions
			for (int i = 0; i < 10; i++)
			{

				// set the value and compute
				myPLUMData.item = FAO_items[i];

				getline(ss, temp, ',');
				myPLUMData.nheads = atof(temp.c_str());																																									// nheads
				modelled_historic_nitrogen_1961_2009[myPLUMData.year - year_to_start_reading].value += myCalculator.calcN20ManureManagement(myPLUMData.nheads, myPLUMData.country, myPLUMData.item) * CONVERT_Kg_TO_Tg; // units: TgN2O/yr
			}
		}
	}

	myFileManager.closeFile(myStream);

	if (simulate_nitrogen_emissions_from_fertilizer_application)
	{

		// start fertilizer here
		myStream = myFileManager.openFile(arable_land_nitrogen_fert_path);

		// read all land areas in hectares and feed into 2-d array, later multiply by fertilizer app rates
		// land areas are given from 1961-2018. contact plum for 2019-2100 future predictions (Done)

		string fertvalue_kg_per_ha_arable_land, arableland, line1, line2;
		int arable_land_areas[266][49];
		int rows = 0;
		myStream.ignore(1000, '\n');

		while (getline(myStream, line1))
		{
			stringstream ss(line1);
			for (int i = 0; i < 63; i++)
			{
				if (i < 5)
				{
					getline(ss, temp, ',');
				}
				else if (i > 4 && i < 54)
				{
					getline(ss, arableland, ',');
					arable_land_areas[rows][i - 5] = int((atof(arableland.c_str())));
				}
				else
				{
					getline(ss, temp, ',');
				}
			}
			rows++;
		}

		myFileManager.closeFile(myStream);

		myStream = myFileManager.openFile(nitrogen_histoic_fertilzer_file_path);
		rows = 0; // re-initilize rows here

		myStream.ignore(1000, '\n');
		while (getline(myStream, line2))
		{
			stringstream ss(line2);

			for (int i = 0; i < 63; i++)
			{
				if (i < 5)
				{
					getline(ss, temp, ',');
				}
				else if (i > 4 && i < 54)
				{
					int myarablelands[266][49];

					modelled_historic_nitrogen_1961_2009[i - 5].value += (atof(fertvalue_kg_per_ha_arable_land.c_str()) * arable_land_areas[rows][i - 5]) * CONVERT_Kg_TO_Tg;
				}
				else
				{
					getline(ss, temp, ',');
				}
			}
			rows++;
		}
		myFileManager.closeFile(myStream);
	}
}

void NitrogenEmissions::setPLUMDataFilePath(string path)
{
	PLUMdataFilePath = path;
}

void NitrogenEmissions::setNitrogenEmissionsOutputFilePath(string filePath)
{
	NitrogenEmissionsOutputFilePath = filePath;
}

void NitrogenEmissions::printNitrogenEmissions()
{

	if (NitrogenEmissionsOutputFilePath == " ")
	{
		cout << "Output File Path for nitrogen emissions not set!" << endl;
	}
	else
	{
		myFileManager.printToFile(NitrogenEmissionsOutputFilePath, myN2OData);
	}
}

void NitrogenEmissions::setFertDataFilePath(string path)
{
	plumFertlizerPath = path;
}

vector<dataHolder1> NitrogenEmissions::get_historic_nitrogen_1961_2009()
{
	return modelled_historic_nitrogen_1961_2009;
}

void NitrogenEmissions::setAuxFilePath(string livestocks_counts_path, string nitrogen_fetilizer_path, string arable_land_path)
{
	historic_livestock_counts_1961_2100_path = livestocks_counts_path;
	nitrogen_histoic_fertilzer_file_path = nitrogen_fetilizer_path;
	arable_land_nitrogen_fert_path = arable_land_path;
}



PlumDataProcessor::PlumDataProcessor() {
	cout << "\nPlumDataProcessor default constructor invoked! Ensure base path to Plum files is set" << endl;
}

PlumDataProcessor::PlumDataProcessor(string filePath, string filePath2) {
	cout << "\nPlumDataProcessor Custom Constructor invoked! Setting base file path!" << endl;
	basePathPLUMdata = filePath;
	plumFertilizerOutputPath = filePath2;

}

PlumDataProcessor::~PlumDataProcessor() {
	cout << "PlumDataProcessor destructor invoked!" << endl;
}

vector<dataHolder1> PlumDataProcessor::getTotalFertilizerAmounts() {
	return totalFertlizerAmountPerSSP;
}

vector<dataHolder1> PlumDataProcessor::getManureFertilizerAmount() {
	return manureFertilizerAmount;
}

vector<dataHolder1> PlumDataProcessor::getSyntheticFertilizerAmount() {
	return syntheticFertilizerAmount;
}

vector<dataHolder1> PlumDataProcessor::readFertilizerData() {
	if (plumFertlizerPath == " ") {
		cout << "plum fertilizer data path not set!" << endl;
		exit(100);
	}
	else {
		return myFileManager.loadFile2(plumFertlizerPath);
	}
}

void PlumDataProcessor::extractDataFromPlumLandUseFiles() {
	int nCols = 74; //number of columns in PLUM landuse file
	double myArray[74] = { 0.0 };
	double totalFertlizerPerYear = 0.0; //units =Kg/ha
	double croplandArea = 0.0;
	int lineCount = 1;

	//loop over ssps
	for (int i = 0; i < 5; i++) {
		//loop over ssps
		cout << "\nPROCESSING PLUM DATA FOR SSP" << i + 1 << endl;
		for (int j = 0; j < 91; j++) {
			cout << "\nProcessing PLUM data for ssp " << i + 1 << "| Year " << j + 2010 << endl;
			string plumFilePath = generateFilePath(to_string(i + 1), to_string(j + 2010));
			fstream myStream = myFileManager.openFile(plumFilePath);

			//ignore headers
			myStream.ignore(10000, '\n');

			while (myStream.good()) {
				for (int i = 0; i < nCols; i++) {
					myStream >> myArray[i];
					if (i == 7) {
						croplandArea = myArray[i];
					}
					//logic to pick up columns containing FQ
					if (i == 13 || ((i - 20 >= 0) && ((i - 20) % 7 == 0))) {
						totalFertlizerPerYear += myArray[i] * croplandArea;
					}
				}
				//cout << "Done processing line: " << lineCount << endl;
				lineCount++;
			}
			lineCount = 0;
			totalFertlizerAmountPerSSP.push_back(dataHolder1((j + 2010), totalFertlizerPerYear));
			myFileManager.closeFile(myStream);
			cout << "\nFinished Processing PLUM data for ssp" << i + 1 << " Year " << j + 2010 << endl;
		}
		printPLUMTotalFertilizer((i + 1)); //prints total fertilizer to file in KgN/yr


		//re-initialize
		totalFertlizerAmountPerSSP.clear();
		totalFertlizerPerYear = 0.0;
		croplandArea = 0.0;
		for (int i = 0; i < 74; i++) {
			myArray[i] = 0.0;
		}
		cout << "\nFINISHED PROCESSING DATA FOR SSP" << i + 1 << endl;
	}
}


void PlumDataProcessor::extractDataFromPlumLandUseFiles_v2() {


	string headers[7] = { "SSP", "Year", "PlumGroup", "Crop", "CropArea", "CropFert", "CropIrrig" }; //as a guide

	//method to preprocess plum v2 data
	for (int i = 0; i < 5; i++) {
		//loop over ssps
		string land_use_file_name = basePathPLUMdata + PLUMDataFilePath_v2;
		int index_of_1 = land_use_file_name.find("Y");
		string for_loop_index = to_string(i + 1);
		land_use_file_name = land_use_file_name.replace(index_of_1, 1, for_loop_index);


		cout << "land use file name: " << land_use_file_name << endl;

		fstream myStream = myFileManager.openFile(land_use_file_name);
		string line, temp;
		int year_tracker = 2010;
		int current_year = 2010;
		double cropFert_per_line = 0.0;
		double cropFert_per_year = 0.0;

		myStream.ignore(10000, '\n'); //ignore headers

		while (getline(myStream, line)) {
			stringstream ss(line);

			for (int i = 0; i < 7; i++) {
				getline(ss, temp, ',');

				if (i == 1) {
					//set year
					current_year = stoi(temp);

				}
				else if (i == 5) {
					cropFert_per_line = stof(temp);
				}
			}

			//line reading done: store cropFert_per_line
			if (current_year == year_tracker) {
				cropFert_per_year += cropFert_per_line;
			}
			else {
				totalFertlizerAmountPerSSP.push_back(dataHolder1(year_tracker, cropFert_per_year * 1e09)); //KgN: converted
				cropFert_per_year = 0.0;
				year_tracker++;
			}


		}
		totalFertlizerAmountPerSSP.push_back(dataHolder1(year_tracker, cropFert_per_year * 1e09)); //KgN: converted
		printPLUMTotalFertilizer((i + 1)); //prints total fertilizer to file in KgN/yr
		myFileManager.printToConsole(totalFertlizerAmountPerSSP);
		totalFertlizerAmountPerSSP.clear();

	}


}


string PlumDataProcessor::generateFilePath(string ssp, string year) {
	string results = PLUMDataFilePath;

	//substitute present ssp
	size_t pos = results.find("X");
	if (pos == string::npos) {
		cout << "Cannot find character to replace" << endl;
		exit(100);
	}
	else {
		results.replace(pos, ssp.length(), ssp);
	}

	//substitute present year
	pos = results.find("Y");
	if (pos == string::npos) {
		cout << "Cannot find character to replace" << endl;
		exit(100);
	}
	else {
		results.replace(pos, year.length(), year);
	}

	results = basePathPLUMdata + results;

	return results;
}






void PlumDataProcessor::printPLUMTotalFertilizer(int index) {

	string fileName = plumFertilizerOutputPath + to_string(index) + ".txt";
	myFileManager.printToFile(fileName, totalFertlizerAmountPerSSP, 8);
}


void PlumDataProcessor::setplumFertlizerPath(string filePath) {
	plumFertlizerPath = filePath;
}


//std::map<std::string, std::string> UtilityHandler::readConfig(const std::string& filename)
//{
//	std::map<std::string, std::string> config;
//	std::ifstream file(filename);
//	std::string line;
//	int lineNumber = 0;
//
//	if (!file.is_open())
//	{
//		throw std::runtime_error("Unable to open config file: " + filename);
//	}
//
//	while (std::getline(file, line))
//	{
//		lineNumber++;
//		// Skip empty lines or lines with only whitespace
//		if (line.empty() || std::all_of(line.begin(), line.end(), isspace))
//		{
//			continue;
//		}
//
//		std::istringstream is_line(line);
//		std::string key;
//		if (std::getline(is_line, key, '='))
//		{
//			std::string value;
//			if (std::getline(is_line, value))
//			{
//				config[UtilityHandler::trim(key)] = UtilityHandler::trim(value);
//			}
//			else
//			{
//				throw std::runtime_error("Parsing error in config file at line " + std::to_string(lineNumber));
//			}
//		}
//		else
//		{
//			throw std::runtime_error("Invalid format in config file at line " + std::to_string(lineNumber));
//		}
//	}
//
//	// Add checks for required keys here if necessary
//
//	return config;
//}

void UtilityHandler::printMap(const std::map<std::string, std::string>& map)
{
	for (const auto& pair : map)
	{
		std::cout << "Key: " << pair.first << ", Value: " << pair.second << std::endl;
	}
}

std::string UtilityHandler::replacePlaceholders(const std::string& path, const std::string& baseDirectory, const std::string& ssp, const std::string& rcp)
{
	std::string result = baseDirectory + path; // Prepend baseDirectory

	// Replace SSP placeholder if it exists
	// assumption: There's only one occurence of SSP as it should be
	size_t pos = result.find("SSP");
	if (pos != std::string::npos)
	{
		result.replace(pos, 3, ssp);
		// pos = result.find("SSP", pos + ssp.length()); // Find next occurrence, if any
	}

	// Replace RCP placeholder if it exists
	// assumption: There's only one occurence of RCP as it should be
	pos = result.find("RCP");
	if (pos != std::string::npos)
	{
		result.replace(pos, 3, rcp);
		// pos = result.find("RCP", pos + rcp.length()); // Find next occurrence, if any
	}

	return result;
}

std::vector<std::string> UtilityHandler::split(const std::string& str, char delimiter)
{
	std::vector<std::string> tokens;
	std::string token;
	std::istringstream tokenStream(str);

	while (std::getline(tokenStream, token, delimiter))
	{
		tokens.push_back(UtilityHandler::trim(token));
	}

	return tokens;
}

void UtilityHandler::printVector(const std::vector<std::string>& vector)
{
	for (const auto& element : vector)
	{
		std::cout << element << std::endl;
	}
}

// Trims whitespace from the start of a string
inline std::string& UtilityHandler::ltrim(std::string& str)
{
	str.erase(str.begin(), std::find_if(str.begin(), str.end(), [](unsigned char ch)
		{ return !std::isspace(ch); }));
	return str;
}

// Trims whitespace from the end of a string
inline std::string& UtilityHandler::rtrim(std::string& str)
{
	str.erase(std::find_if(str.rbegin(), str.rend(), [](unsigned char ch)
		{ return !std::isspace(ch); })
		.base(),
		str.end());
	return str;
}

// Trims whitespace from both ends of a string
inline std::string& UtilityHandler::trim(std::string& str)
{
	return ltrim(rtrim(str));
}

void UtilityHandler::replaceAll(std::string& str, const std::string& from, const std::string& to)
{
	size_t start_pos = 0;
	while ((start_pos = str.find(from, start_pos)) != std::string::npos)
	{
		str.replace(start_pos, from.length(), to);
		start_pos += to.length();
	}
}

void UtilityHandler::replaceSubstring(std::string& str, const std::string& from, const std::string& to)
{
	size_t startPos = 0;
	while ((startPos = str.find(from, startPos)) != std::string::npos)
	{
		str.replace(startPos, from.length(), to);
		startPos += to.length(); // Handles case if 'to' is a substring of 'from'
	}
}


Wetlands::Wetlands(string filePath) {
	setWetlandsAreaFilePath(filePath);
}

Wetlands::Wetlands() {
	cout << "Wetlands constructor invoked!" << endl;
}

Wetlands::~Wetlands() {
	cout << "Wetlands destructor invoked!" << endl;
}


void Wetlands::startCalculation() {

	fstream myReader = myFileManager.openFile(wetlandsAreaFilePath);
	string line, temp;
	while (getline(myReader, line)) {
		stringstream ss(line);

		getline(ss, temp, ',');
		myReadWetlands.country = temp;

		getline(ss, temp, ',');
		myReadWetlands.variable = temp;

		getline(ss, temp, ',');
		myReadWetlands.year = temp;

		getline(ss, temp, ',');
		myReadWetlands.measure = temp;

		getline(ss, temp, ',');
		myReadWetlands.value = temp;

		double diffusiveRate = myMaps.getDiffusiveEmissionFactorForWetlands(myReadWetlands.country);

		Ch4_wetlands_total += myCalculator.calcCH4Wetlands(diffusiveRate, stof(myReadWetlands.value));

	}

	for (int i = 1961; i <= 2100; i++) {
		wetlandsCH4.push_back(dataHolder1(i, Ch4_wetlands_total));
	}
}


vector <dataHolder1> Wetlands::getWetlandsMethaneData() {
	return wetlandsCH4;
}


void  Wetlands::setWetlandsAreaFilePath(string filePath) {
	wetlandsAreaFilePath = filePath;
}

void Wetlands::setWetlandsMethaneOutputFilePath(string filePath) {
	wetlandsMethaneOutputFilePath = filePath;
}
void Wetlands::printWetlandsMethaneData() {

	if (wetlandsMethaneOutputFilePath == "") {
		cout << "Output File Path for wetlands methane emissions not set!" << endl;
	}
	else {
		myFileManager.printToFile(wetlandsMethaneOutputFilePath, wetlandsCH4);
	}


}
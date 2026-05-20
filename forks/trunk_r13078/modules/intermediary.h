#include <unordered_map>
#include<map>
#include<fstream>
#include<iostream>
#include<vector>
#include<string>
#include <locale>

using namespace std;

class Maps
{

private:
    std::unordered_map<std::string, std::unordered_map<std::string, double>> MAP_ENTERIC_FERMENTATION_EMISSION_FACTORS_FOR_BUFFALO_CATTLE{

        // Chapter 10 Table 10.11 (Updated)
        // TIER 1 AND TIER 1A ENTERIC FERMENTATION EMISSION FACTORS FOR CATTLE AND BUFFALO (KG CH4/HEAD/YR)

        {"North America", {{"Dairy Cattle", 138}, {"Other Cattle", 64}, {"Buffalo", 0}}},
        {"Western Europe", {{"Dairy Cattle", 126}, {"Other Cattle", 52}, {"Buffalo", 78}}},
        {"Eastern Europe", {{"Dairy Cattle", 93}, {"Other Cattle", 58}, {"Buffalo", 68}}},
        {"Oceania", {{"Dairy Cattle", 93}, {"Other Cattle", 63}, {"Buffalo", 0}}},
        {"Latin America", {{"Dairy Cattle", 87}, {"Other Cattle", 56}, {"Buffalo", 68}}},
        {"Asia", {{"Dairy Cattle", 78}, {"Other Cattle", 54}, {"Buffalo", 76}}},
        {"Africa", {{"Dairy Cattle", 76}, {"Other Cattle", 52}, {"Buffalo", 81}}},
        {"Middle East", {{"Dairy Cattle", 76}, {"Other Cattle", 60}, {"Buffalo", 67}}},
        {"Indian Subcontinent", {{"Dairy Cattle", 73}, {"Other Cattle", 46}, {"Buffalo", 85}}},

        // Added world here. Values are averages of all other regional values
        {"World", {{"Dairy Cattle", 93}, {"Other Cattle", 56}, {"Buffalo", 58}}}

        // validated
    };

    std::unordered_map<std::string, double> MAP_ENTERIC_FERMENTATION_EMISSION_FACTORS_OTHERS{

        // Chapter 10 Table 10.10 (Updated)
        // ENTERIC FERMENTATION EMISSION FACTORS FOR TIER 1 METHOD(KG CH4/HEAD/YR)

        // avergaes of low productivity and high productivity systems currently used for all regions

        /* Caveat: For the application of the simple Tier 1, for all regions other than North America,
        Europe and Oceania the Tier 1 default values are the low productivity EFs.
        To be implemented later.

        Poultry emission factors have not yet been developed by IPCC.
        However, poultry emission factors can be calculated from an animal with a similar
        digestive system and to scale the emissions factor using the ratio of the weights of the animals raised to the 0.75 power.
        For poultry, ie (3.25/120)^0.75 ~ 0.067

        */

        {"Sheep", 7},
        {"Swine", 1.25},
        {"Goats", 7},
        {"Horses", 18},
        {"Camels", 46},
        {"Mules", 10},
        {"Asses", 10},
        {"Deer", 20},
        {"Ostrich", 5},
        {"Poultry", 0.067}

        // validated
    };

    std::unordered_map<std::string, std::string> MAP_ANIMAL_CATEGORIES_FOR_ENTERIC_FERMENTATION{
        // Intermediary map, mapping livestock category in PLUM data to livestock category in Table 10.10 and 10.11
        {"Meat cattle", "Other Cattle"},
        {"Milk whole fresh cow", "Dairy Cattle"},
        {"Milk whole fresh goat", "Goats"},
        {"Meat buffalo", "Buffalo"},
        {"Meat sheep", "Sheep"},
        {"Meat goat", "Goats"},
        {"Milk whole fresh sheep", "Sheep"},
        {"Meat pig", "Swine"},
        {"Meat Poultry", "Poultry"},
        {"Eggs Primary", "Hens"},

        // validated
    };

    std::unordered_map<std::string, std::string> MAP_CONVERT_COUNTRIES_TO_REGIONS{

        // Intermediary map for mapping countries to regions for which EF emmission factors is defined

        {"Kenya", "Africa"},
        {"Pakistan & Afghanistan", "Indian Subcontinent"},
        {"Russian Federation", "Eastern Europe"},
        {"Egypt", "Middle East"},
        {"Algeria", "Middle East"},
        {"Canada", "North America"},
        {"Nigeria", "Africa"},
        {"Australia & NZ", "Oceania"},
        {"Caribbean", "Latin America"},
        {"Central Africa", "Africa"},
        {"Argentina", "Latin America"},
        {"Ethiopia", "Africa"},
        {"Paraguay & Uruguay", "Latin America"},
        {"France Netherlands & Benlex", "Western Europe"},
        {"Germany Austria & Switzerland", "Western Europe"},
        {"Myanmar", "Asia"},
        {"Iraq", "Middle East"},
        {"United Republic of Tanzania", "Africa"},
        {"Bolivia and Chile", "Latin America"},
        {"Venezuela Guyana & Suriname", "Latin America"},
        {"Eastern Europe", "Eastern Europe"},
        {"Ukraine", "Eastern Europe"},
        {"Spain & Portugal", "Western Europe"},
        {"Turkey Cyprus & Greece", "Eastern Europe"},
        {"Bangladesh", "Indian Subcontinent"},
        {"Scandinavia", "Western Europe"},
        {"India  & Sri Lanka", "Asia"},
        {"Southern Africa other", "Africa"},
        {"Democratic Republic of the Congo", "Africa"},
        {"East Asia & Pacific_other", "Asia"},
        {"United Kingdom", "Western Europe"},
        {"Republic of Korea", "Asia"},
        {"ex-Yugoslavia", "Eastern Europe"},
        {"Poland", "Eastern Europe"},
        {"Morocco", "Middle East"},
        {"Middle East other", "Middle East"},
        {"West Africa", "Africa"},
        {"Other former USSR", "Eastern Europe"},
        {"Mexico", "Latin America"},
        {"Colombia", "Latin America"},
        {"Thailand", "Asia"},
        {"Peru & Ecuador", "Latin America"},
        {"Viet Nam & Cambodia", "Asia"},
        {"Nepal & Butan", "Indian Subcontinent"},
        {"Uganda", "Africa"},
        {"Italy", "Western Europe"},
        {"Central America", "Latin America"},
        {"Philippines & Malaysia", "Asia"},
        {"Indonesia", "Asia"},
        {"Brazil", "Latin America"},
        {"Iran (Islamic Republic of)", "Middle East"},
        {"Japan", "Asia"},
        {"South Africa", "Africa"},
        {"North Africa other", "Middle East"},
        {"United States of America", "North America"},
        {"China", "Asia"},
        {"Mongolia", "Asia"},
        {"Africa", "Africa"},
        {"Asia", "Asia"},
        {"Europe", "Western Europe"},
        {"Oceania", "Oceania"},
        {"South America", "Latin America"},

        // supplement added

        // validated

        {"World", "World"} };

    // Map for VSE rate
    std::unordered_map<std::string, std::unordered_map<std::string, double>> MAP_FOR_VOLATILE_SOLID_EXCRETION_RATE{

        // Chapter 10 Table 10.13A
        // DEFAULT VALUES FOR VOLATILE SOLID EXCRETION RATE (KG VS (1000 KG ANIMAL MASS)-1 DAY-1)

        {"North America", {{"Dairy Cattle", 9.3}, {"Other Cattle", 7.6}, {"Buffalo", 0.0}, {"Swine", 3.3}, {"Poultry", 14.5}, {"Hens", 9.4}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 5.65}, {"Sheep", 8.2}, {"Goats", 9}, {"Camels", 11.5}, {"Ducks", 7.4}}},
        {"Western Europe", {{"Dairy Cattle", 7.5}, {"Other Cattle", 5.7}, {"Buffalo", 7.7}, {"Swine", 4.5}, {"Poultry", 12.3}, {"Hens", 8.6}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 5.65}, {"Sheep", 8.2}, {"Goats", 9}, {"Camels", 11.5}, {"Ducks", 7.4}}},
        {"Eastern Europe", {{"Dairy Cattle", 6.7}, {"Other Cattle", 7.6}, {"Buffalo", 6.2}, {"Swine", 4.0}, {"Poultry", 12.6}, {"Hens", 9.4}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 5.65}, {"Sheep", 8.2}, {"Goats", 9}, {"Camels", 11.5}, {"Ducks", 7.4}}},
        {"Oceania", {{"Dairy Cattle", 6.0}, {"Other Cattle", 8.7}, {"Buffalo", 0.0}, {"Swine", 4.0}, {"Poultry", 15.4}, {"Hens", 8.6}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 5.65}, {"Sheep", 8.2}, {"Goats", 9}, {"Camels", 11.5}, {"Ducks", 7.4}}},
        {"Latin America", {{"Dairy Cattle", 7.9}, {"Other Cattle", 8.5}, {"Buffalo", 11.2}, {"Swine", 5.0}, {"Poultry", 13.5}, {"Hens", 10.1}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 7.2}, {"Sheep", 8.3}, {"Goats", 10.4}, {"Camels", 11.5}, {"Ducks", 7.4}}},
        {"Africa", {{"Dairy Cattle", 18.2}, {"Other Cattle", 12.0}, {"Buffalo", 12.9}, {"Swine", 7.2}, {"Poultry", 12.6}, {"Hens", 10.2}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 7.2}, {"Sheep", 8.3}, {"Goats", 10.4}, {"Camels", 11.5}, {"Ducks", 7.4}}},
        {"Middle East", {{"Dairy Cattle", 10.7}, {"Other Cattle", 14.1}, {"Buffalo", 9.8}, {"Swine", 4.3}, {"Poultry", 14.2}, {"Hens", 9.0}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 7.2}, {"Sheep", 8.3}, {"Goats", 10.4}, {"Camels", 11.5}, {"Ducks", 7.4}}},
        {"Asia", {{"Dairy Cattle", 9.0}, {"Other Cattle", 9.8}, {"Buffalo", 13.5}, {"Swine", 5.8}, {"Poultry", 11.2}, {"Hens", 9.3}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 7.2}, {"Sheep", 8.3}, {"Goats", 10.4}, {"Camels", 11.5}, {"Ducks", 7.4}}},
        {"Indian Subcontinent", {{"Dairy Cattle", 14.1}, {"Other Cattle", 12.2}, {"Buffalo", 0.0}, {"Swine", 7.7}, {"Poultry", 14.9}, {"Hens", 13.2}, {"Asses", 7.2}, {"Mules", 7.2}, {"Turkeys", 10.3}, {"Horses", 7.2}, {"Sheep", 8.3}, {"Goats", 10.4}, {"Camels", 11.5}, {"Ducks", 7.4}}}

        // validated

    };

    // Map to get animal category of animals for VSE rate
    std::unordered_map<string, string> MAP_FOR_ANIMAL_CATEGORY_FOR_VSE_RATE{

        // Intermediary map to map livestock categories in PLUM data (and FAO) to livestock categories in VSE rates in IPCC docs
        {"Meat pig", "Swine"},
        {"Meat Poultry", "Poultry"},
        {"Eggs Primary", "Hens"},
        {"Meat cattle", "Other Cattle"},
        {"Milk whole fresh cow", "Dairy Cattle"},
        {"Milk whole fresh goat", "Goats"},
        {"Meat sheep", "Sheep"},
        {"Meat goat", "Goats"},
        {"Milk whole fresh sheep", "Sheep"},
        {"Meat buffalo", "Buffalo"},
        {"Asses", "Asses"},
        {"Mules", "Mules"},
        {"Turkey", "Turkeys"},
        {"Horses", "Horses"},
        {"Camels", "Camels"},
        {"Ducks", "Ducks"}

        // validated
    };

    std::unordered_map<std::string, unordered_map<std::string, double>> MAP_WEIGHTS_FOR_ANIMAL_CATEGORIES{

        // DEFAULT VALUES FOR LIVE WEIGHTS FOR ANIMAL CATEGORIES (KG)
        // Table 10A.5 (NEW)
        {"Dairy Cattle", {{"North America", 650.0}, {"Western Europe", 600.0}, {"Eastern Europe", 550.0}, {"Oceania", 488.0}, {"Latin America", 508.0}, {"Africa", 260.0}, {"Middle East", 349.0}, {"Asia", 386.0}, {"Indian Subcontinent", 285.0}}},
        {"Other Cattle", {{"North America", 407.0}, {"Western Europe", 405.0}, {"Eastern Europe", 389.0}, {"Oceania", 359.0}, {"Latin America", 303.0}, {"Africa", 236.0}, {"Middle East", 275.0}, {"Asia", 299.0}, {"Indian Subcontinent", 226.0}}},
        {"Buffalo", {{"North America", 0.0}, {"Western Europe", 509.0}, {"Eastern Europe", 467.0}, {"Oceania", 0.0}, {"Latin America", 315.0}, {"Africa", 339.0}, {"Middle East", 381.0}, {"Asia", 336.0}, {"India Subcontinent", 321.0}}},
        {"Swine", {{"North America", 77.0}, {"Western Europe", 76.0}, {"Eastern Europe", 77.0}, {"Oceania", 61.0}, {"Latin America", 65.0}, {"Africa", 49.0}, {"Middle East", 59.0}, {"Asia", 58.0}, {"Indian Subcontinent", 59.0}}},
        {"Poultry", {{"North America", 1.4}, {"Western Europe", 1.4}, {"Eastern Europe", 1.3}, {"Oceania", 1.3}, {"Latin America", 1.1}, {"Africa", 0.9}, {"Middle East", 0.9}, {"Asia", 1.2}, {"Indian Subcontinent", 1.0}}},
        {"Sheep", {{"North America", 40.0}, {"Western Europe", 40.0}, {"Eastern Europe", 40.0}, {"Oceania", 40.0}, {"Latin America", 31.0}, {"Africa", 31.0}, {"Middle East", 31.0}, {"Asia", 31.0}, {"Indian Subcontinent", 31.0}}},
        {"Goats", {{"North America", 41.0}, {"Western Europe", 40.0}, {"Eastern Europe", 36.0}, {"Oceania", 33.0}, {"Latin America", 24.0}, {"Africa", 24.0}, {"Middle East", 24.0}, {"Asia", 24.0}, {"Indian Subcontinent", 24.0}}},
        {"Mules", {{"North America", 130}, {"Western Europe", 130}, {"Eastern Europe", 130}, {"Oceania", 130}, {"Latin America", 130}, {"Africa", 130}, {"Middle East", 130}, {"Asia", 130}, {"Indian Subcontinent", 130}}},
        {"Asses", {{"North America", 130}, {"Western Europe", 130}, {"Eastern Europe", 130}, {"Oceania", 130}, {"Latin America", 130}, {"Africa", 130}, {"Middle East", 130}, {"Asia", 130}, {"Indian Subcontinent", 130}}},
        {"Turkeys", {{"North America", 6.8}, {"Western Europe", 6.8}, {"Eastern Europe", 6.8}, {"Oceania", 6.8}, {"Latin America", 6.8}, {"Africa", 6.8}, {"Middle East", 6.8}, {"Asia", 6.8}, {"Indian Subcontinent", 6.8}}},
        {"Horses", {{"North America", 377}, {"Western Europe", 377}, {"Eastern Europe", 377}, {"Oceania", 377}, {"Latin America", 238}, {"Africa", 238}, {"Middle East", 238}, {"Asia", 238}, {"Indian Subcontinent", 238}}},
        {"Ducks", {{"North America", 2.7}, {"Western Europe", 2.7}, {"Eastern Europe", 2.7}, {"Oceania", 2.7}, {"Latin America", 2.7}, {"Africa", 2.7}, {"Middle East", 2.7}, {"Asia", 2.7}, {"Indian Subcontinent", 2.7}}},
        {"Camels", {{"North America", 217}, {"Western Europe", 217}, {"Eastern Europe", 217}, {"Oceania", 217}, {"Latin America", 217}, {"Africa", 217}, {"Middle East", 217}, {"Asia", 217}, {"Indian Subcontinent", 217}}},
        {"Hens", {{"North America", 1.5}, {"Western Europe", 1.9}, {"Eastern Europe", 1.9}, {"Oceania", 2.0}, {"Latin America", 1.4}, {"Africa", 1.4}, {"Middle East", 1.2}, {"Asia", 1.5}, {"Indian Subcontinent", 1.3}}}

        // validated
    };

    std::unordered_map<string, string> MAP_FOR_ANIMAL_CATEGORIES_TYPICAL_ANIMAL_MASS{

        // Intermediary to map PLUM animal categories to typical animal mass categories in Table 10A.5
        {"Meat pig", "Swine"},
        {"Meat Poultry", "Poultry"},
        {"Eggs Primary", "Hens"},
        {"Meat cattle", "Other Cattle"},
        {"Milk whole fresh cow", "Dairy Cattle"},
        {"Milk whole fresh goat", "Goats"},
        {"Meat sheep", "Sheep"},
        {"Meat goat", "Goats"},
        {"Milk whole fresh sheep", "Sheep"},
        {"Meat buffalo", "Buffalo"},
        {"Asses", "Asses"},
        {"Mules", "Mules"},
        {"Turkey", "Turkeys"},
        {"Horses", "Horses"},
        {"Camels", "Camels"},
        {"Ducks", "Ducks"}

        // validated

    };

    // NITROGEN MAPS
    // conversion map for FRACGAS
    std::unordered_map<std::string, std::string> MAP_ANIMAL_TO_ANIMAL_CATEGORY_FOR_FRACGAS{
        // Intermediary map mapping animal categories in PLUM data with animal categories in Fracgas data: Table 10.22 ch10

        {"Meat pig", "Swine"},
        {"Meat Poultry", "Poultry"},
        {"Eggs Primary", "Poultry"},
        {"Meat cattle", "Other cattle"},
        {"Milk whole fresh cow", "Dairy cattle"},
        {"Milk whole fresh goat", "Other animals"},
        {"Meat sheep", "Other animals"},
        {"Meat goat", "Other animals"},
        {"Milk whole fresh sheep", "Other animals"},
        {"Meat buffalo", "Other animals"},
        {"Asses", "Other animals"},
        {"Mules", "Other animals"},
        {"Turkey", "Other animals"},
        {"Horses", "Other animals"},
        {"Camels", "Other animals"},
        {"Ducks", "Other animals"}

        // validated
    };

    std::unordered_map<std::string, std::unordered_map<std::string, double>> MAP_FRACGAS{
        // DEFAULT VALUES FOR NITROGEN LOSS FRACTIONS DUE TO VOLATILISATION OF NH3 AND NOX AND LEACHING OF NITROGEN FROM MANURE MANAGEMENT (Fraction, no units)
        // TABLE 10.22

        {"Lagoon", {{"Swine", 0.40}, {"Dairy cattle", 0.35}, {"Poultry", 0.40}, {"Other cattle", 0.35}, {"Other animals", 0.35}}},
        {"Liquid/Slurry", {{"Swine", 0.29}, {"Dairy cattle", 0.29}, {"Poultry", 0.24}, {"Other cattle", 0.29}, {"Other animals", 0.09}}},
        {"Daily Spread", {{"Swine", 0.07}, {"Dairy cattle", 0.07}, {"Poultry", 0.07}, {"Other cattle", 0.07}, {"Other animals", 0.07}}},
        {"Solid Storage", {{"Swine", 0.36}, {"Dairy cattle", 0.23}, {"Poultry", 0.33}, {"Other cattle", 0.36}, {"Other animals", 0.09}}},
        {"Dry lot", {{"Swine", 0.45}, {"Dairy cattle", 0.30}, {"Poultry", 0.0}, {"Other cattle", 0.30}, {"Other animals", 0.30}}},
        {"Burned for fuel", {{"Swine", 0.0}, {"Dairy cattle", 0.0}, {"Poultry", 0.0}, {"Other cattle", 0.0}, {"Other animals", 0.0}}},
        {"Anaerobic Digestion", {{"Swine", 0.3}, {"Dairy cattle", 0.3}, {"Poultry", 0.3}, {"Other cattle", 0.3}, {"Other animals", 0.3}}},
        {"Pit", {{"Swine", 0.25}, {"Dairy cattle", 0.28}, {"Poultry", 0.28}, {"Other cattle", 0.25}, {"Other animals", 0.25}}},
        {"Composting", {{"Swine", 0.45}, {"Dairy cattle", 0.43}, {"Poultry", 0.56}, {"Other cattle", 0.55}, {"Other animals", 0.23}}},
        {"Deep bedding", {{"Swine", 0.40}, {"Dairy cattle", 0.25}, {"Poultry", 0.30}, {"Other cattle", 0.25}, {"Other animals", 0.40}}},
        {"Poultry manure", {{"Swine", 0.0}, {"Dairy cattle", 0.0}, {"Poultry", 0.44}, {"Other cattle", 0.0}, {"Other animals", 0.0}}},
        {"Aerobic treatment", {{"Swine", 0.53}, {"Dairy cattle", 0.53}, {"Poultry", 0.2}, {"Other cattle", 0.53}, {"Other animals", 0.24}}},

        // validated
    };

    std::unordered_map<std::string, std::unordered_map<std::string, double>> MAP_NITROGEN_EXCRETION_RATE{
        // DEFAULT VALUES FOR NITROGEN EXCRETION RATE (KG N/(1000 KG ANIMAL MASS)/DAY)
        // Table 10.19 (Updated) Ch10

        {"North America", {{"Dairy Cattle", 0.6}, {"Other Cattle", 0.4}, {"Buffalo", 0.0}, {"Swine", 0.39}, {"Poultry", 1.45}, {"Hens", 1.13}, {"Asses", 0.3}, {"Mules", 0.3}, {"Turkeys", 0.74}, {"Horses", 0.3}, {"Camels", 0.38}, {"Goats", 0.46}, {"Sheep", 0.35}, {"Ducks", 0.83}}},
        {"Western Europe", {{"Dairy Cattle", 0.50}, {"Other Cattle", 0.42}, {"Buffalo", 0.45}, {"Swine", 0.65}, {"Poultry", 0.99}, {"Hens", 0.87}, {"Asses", 0.26}, {"Mules", 0.26}, {"Turkeys", 0.74}, {"Horses", 0.26}, {"Camels", 0.38}, {"Goats", 0.46}, {"Sheep", 0.36}, {"Ducks", 0.83}}},
        {"Eastern Europe", {{"Dairy Cattle", 0.42}, {"Other Cattle", 0.47}, {"Buffalo", 0.35}, {"Swine", 0.63}, {"Poultry", 0.96}, {"Hens", 0.81}, {"Asses", 0.30}, {"Mules", 0.30}, {"Turkeys", 0.74}, {"Horses", 0.30}, {"Camels", 0.38}, {"Goats", 0.44}, {"Sheep", 0.36}, {"Ducks", 0.83}}},
        {"Oceania", {{"Dairy Cattle", 0.72}, {"Other Cattle", 0.46}, {"Buffalo", 0.0}, {"Swine", 0.54}, {"Poultry", 1.42}, {"Hens", 1.04}, {"Asses", 0.3}, {"Mules", 0.3}, {"Turkeys", 0.74}, {"Horses", 0.3}, {"Camels", 0.38}, {"Goats", 0.42}, {"Sheep", 0.43}, {"Ducks", 0.83}}},
        {"Latin America", {{"Dairy Cattle", 0.39}, {"Other Cattle", 0.31}, {"Buffalo", 0.41}, {"Swine", 0.59}, {"Poultry", 1.20}, {"Hens", 1.17}, {"Asses", 0.46}, {"Mules", 0.46}, {"Turkeys", 0.74}, {"Horses", 0.46}, {"Camels", 0.46}, {"Goats", 0.34}, {"Sheep", 0.32}, {"Ducks", 0.83}}},
        {"Africa", {{"Dairy Cattle", 0.44}, {"Other Cattle", 0.44}, {"Buffalo", 0.41}, {"Swine", 0.44}, {"Poultry", 1.29}, {"Hens", 1.20}, {"Asses", 0.46}, {"Mules", 0.46}, {"Turkeys", 0.74}, {"Horses", 0.46}, {"Camels", 0.46}, {"Goats", 0.34}, {"Sheep", 0.32}, {"Ducks", 0.83}}},
        {"Middle East", {{"Dairy Cattle", 0.50}, {"Other Cattle", 0.55}, {"Buffalo", 0.39}, {"Swine", 0.66}, {"Poultry", 1.29}, {"Hens", 1.11}, {"Asses", 0.46}, {"Mules", 0.46}, {"Turkeys", 0.74}, {"Horses", 0.46}, {"Camels", 0.46}, {"Goats", 0.34}, {"Sheep", 0.32}, {"Ducks", 0.83}}},
        {"Asia", {{"Dairy Cattle", 0.44}, {"Other Cattle", 0.38}, {"Buffalo", 0.44}, {"Swine", 0.61}, {"Poultry", 1.1}, {"Hens", 1.0}, {"Asses", 0.46}, {"Mules", 0.46}, {"Turkeys", 0.74}, {"Horses", 0.46}, {"Camels", 0.46}, {"Goats", 0.34}, {"Sheep", 0.32}, {"Ducks", 0.83}}},
        {"Indian Subcontinent", {{"Dairy Cattle", 0.65}, {"Other Cattle", 0.44}, {"Buffalo", 0.57}, {"Swine", 0.68}, {"Poultry", 1.62}, {"Hens", 1.65}, {"Asses", 0.46}, {"Mules", 0.46}, {"Turkeys", 0.74}, {"Horses", 0.46}, {"Camels", 0.46}, {"Goats", 0.34}, {"Sheep", 0.32}, {"Ducks", 0.83}}}

        // validated

    };

    std::unordered_map<std::string, std::string> MAP_REGIONS_TO_CLIMATE{

        // Intermediary
        // for methane emissions fatcor for manure management emissions
        {"North America", "Temperate"},
        {"Western Europe", "Temperate"},
        {"Eastern Europe", "Temperate"},
        {"Oceania", "Cool"},
        {"Latin America", "Warm"},
        {"Asia", "Warm"},
        {"Africa", "Warm"},
        {"Middle East", "Warm"},
        {"Indian Subcontinent", "Warm"}

        // validated
    };

    std::unordered_map<string, double> MAP_EMISSION_FACTOR_FOR_N2O_FROM_MANURE_MANAGEMENT{
        // DEFAULT EMISSION FACTORS FOR DIRECT N2O EMISSIONS FROM MANURE MANAGEMENT
        // Table 10.21

        {"Pasture Range and Paddock", 0.004}, // TODO:
        {"Daily Spread", 0.0},
        {"Solid Storage", 0.008},
        {"Dry lot", 0.02},
        {"Liquid/Slurry", 0.003},
        {"Anaerobic Digestion", 0.0006},
        {"Lagoon", 0.0},
        {"Burned for fuel", 0.004},
        {"Pit", 0.02},
        {"Composting", 0.007},
        {"Deep bedding", 0.04},
        {"Poultry manure", 0.001},
        {"Aerobic treatment", 0.008}

        // validated
    };

    unordered_map<string, string> MAP_WETLANDS_COUNTRIES_CLIMATE{

        // Intermediary map to map countries to climate zones for wetlands emissions calculations
        {"Australia", "Tropical Dry"},
        {"Austria", "Warm Temperate Moist"},
        {"Belgium", "Warm Temperate Moist"},
        {"Canada", "Polar Boreal Wet"},
        {"Czech Republic", "Cold Temperate Moist"},
        {"Denmark", "Cold Temperate Moist"},
        {"Finland", "Cold Temperate Moist"},
        {"France", "Warm Temperate Moist"},
        {"Germany", "Cold Temperate Moist"},
        {"Greece", "Warm Temperate Dry"},
        {"Hungary", "Warm Temperate Moist"},
        {"Iceland", "Polar Boreal Wet"},
        {"Ireland", "Warm Temperate Moist"},
        {"Italy", "Warm Temperate Moist"},
        {"Japan", "Warm Temperate Moist"},
        {"Korea", "Warm Temperate Moist"},
        {"Luxembourg", "Warm Temperate Moist"},
        {"Mexico", "Tropical Dry"},
        {"Netherlands", "Warm Temperate Moist"},
        {"Norway", "Cold Temperate Moist"},
        {"Poland", "Cold Temperate Moist"},
        {"Portugal", "Warm Temperate Moist"},
        {"Slovak Republic", "Cold Temperate Moist"},
        {"Spain", "Warm Temperate Dry"},
        {"Sweden", "Cold Temperate Moist"},
        {"Switzerland", "Cold Temperate Moist"},
        {"Turkey", "Warm Temperate Dry"},
        {"United Kingdom", "Cold Temperate Moist"},
        {"United States", "Warm Temperate Moist"},
        {"Afghanistan", "Tropical Dry"},
        {"Albania", "Warm Temperate Moist"},
        {"Algeria", "Tropical dry"},
        {"American Samoa", "Tropical Wet"},
        {"Andorra", "Warm Temperate Moist"},
        {"Angola", "Tropical Dry"},
        {"Anguilla", "Tropical Wet"},
        {"Antigua and Barbuda", "Tropical Wet"},
        {"Argentina", "Warm Temperate Dry"},
        {"Armenia", "Cold Temperate Moist"},
        {"Aruba", "Tropical Wet"},
        {"Azerbaijan", "Cold Temperate Moist"},
        {"Bahamas", "Tropical Wet"},
        {"Bahrain", "Tropical Dry"},
        {"Bangladesh", "Tropical Wet"},
        {"Barbados", "Tropical wet"},
        {"Belarus", "Cold Temperate Moist"},
        {"Belize", "Tropical Wet"},
        {"Benin", "Tropical Wet"},
        {"Bermuda", "Warm Temperate Moist"},
        {"Bhutan", "Warm Temperate Moist"},
        {"Bolivia", "Tropical Wet"},
        {"Bosnia and Herzegovina", "Cold Temperate Moist"},
        {"Botswana", "Tropical Dry"},
        {"Brazil", "Tropical Wet"},
        {"British Virgin Islands", "Tropical Wet"},
        {"Brunei Darussalam", "Tropical wet"},
        {"Bulgaria", "Warm Temperate Moist"},
        {"Burkina Faso", "Tropical Dry"},
        {"Burundi", "Tropical Dry"},
        {"Cambodia", "Tropical Wet"},
        {"Cameroon", "Tropical Wet"},
        {"Cabo Verde", "Tropical Wet"},
        {"Cayman Islands", "Tropical Wet"},
        {"Central African Republic", "Tropical Wet"},
        {"Chad", "Tropical Dry"},
        {"Chile", "Warm Temperate Dry"},
        {"China (People's Republic of)", "Cold Temperate Moist"},
        {"Colombia", "Tropical Wet"},
        {"Comoros", "Tropical Wet"},
        {"Congo", "Tropical Wet"},
        {"Cook Islands", "Tropical Wet"},
        {"Costa Rica", "Tropical Wet"},
        {"Cote d'Ivoire", "Tropical Wet"},
        {"Croatia", "Warm Temperate Moist"},
        {"Cuba", "Tropical Wet"},
        {"Cyprus", "Warm Temperate Dry"},
        {"Democratic People's Republic of Korea", "Cold Temperate Moist"},
        {"Democratic Republic of the Congo", "Tropical Wet"},
        {"Djibouti", "Tropical Dry"},
        {"Dominica", "Tropical Wet"},
        {"Dominican Republic", "Tropical Wet"},
        {"Ecuador", "Warm Temperate Moist"},
        {"Egypt", "Tropical Dry"},
        {"El Salvador", "Tropical Dry"},
        {"Equatorial Guinea", "Tropical Wet"},
        {"Eritrea", "Tropical Dry"},
        {"Estonia", "Cold Temperate Moist"},
        {"Ethiopia", "Tropical Dry"},
        {"Falkland Islands (Malvinas)", "Cold Temperate Moist"},
        {"Fiji", "Tropical Wet"},
        {"French Guiana", "Tropical Wet"},
        {"French Polynesia", "Tropical Wet"},
        {"Gabon", "Tropical Wet"},
        {"Gambia", "Tropical Wet"},
        {"Georgia", "Cold Temperate Moist"},
        {"Ghana", "Tropical Wet"},
        {"Gibraltar", "Warm Temperate Dry"},
        {"Greenland", "Polar Boreal Wet"},
        {"Grenada", "Tropical Wet"},
        {"Guadeloupe", "Tropical Wet"},
        {"Guam", "Tropical Wet"},
        {"Guatemala", "Tropical Wet"},
        {"Guinea", "Tropical Wet"},
        {"Guinea-Bissau", "Tropical Wet"},
        {"Guyana", "Tropical Wet"},
        {"Haiti", "Tropical Wet"},
        {"Honduras", "Tropical Wet"},
        {"India", "Tropical Moist"},
        {"Indonesia", "Tropical Wet"},
        {"Iran", "Tropical Dry"},
        {"Iraq", "Tropical Dry"},
        {"Israel", "Warm Temperate Dry"},
        {"Jamaica", "Tropical Wet"},
        {"Jordan", "Tropical Dry"},
        {"Kazakhstan", "Cold Temperate Moist"},
        {"Kenya", "Tropical Dry"},
        {"Kiribati", "Tropical Wet"},
        {"Kuwait", "Tropical Dry"},
        {"Kyrgyzstan", "Warm Temperate Dry"},
        {"Lao People's Democratic Republic", "Tropical Wet"},
        {"Latvia", "Cold Temperate Moist"},
        {"Lebanon", "Warm Temperate Dry"},
        {"Lesotho", "Warm Temperate Moist"},
        {"Liberia", "Tropical Wet"},
        {"Libya", "Tropical Dry"},
        {"Liechtenstein", "Cold Temperate Moist"},
        {"Lithuania", "Cold Temperate Moist"},
        {"North Macedonia", "Warm Temperate Dry"},
        {"Madagascar", "Tropical Wet"},
        {"Malawi", "Tropical Wet"},
        {"Malaysia", "Tropical Wet"},
        {"Maldives", "Tropical Wet"},
        {"Mali", "Tropical Dry"},
        {"Malta", "Warm temperate dry"},
        {"Marshall Islands", "Tropical Wet"},
        {"Martinique", "Tropical Wet"},
        {"Mauritania", "Tropical Dry"},
        {"Mauritius", "Tropical Moist"},
        {"Mayotte", "Tropical Wet"},
        {"Micronesia", "Tropical Wet"},
        {"Moldova", "Warm Temperate Moist"},
        {"Monaco", "Cold Temperate Moist"},
        {"Mongolia", "Cold Temperate Moist"},
        {"Montserrat", "Tropical Wet"},
        {"Morocco", "Tropical Wet"},
        {"Mozambique", "Tropical Dry"},
        {"Myanmar", "Tropical Wet"},
        {"Namibia", "Tropical Dry"},
        {"Nepal", "Warm Temperate Moist"},
        {"New Caledonia", "Tropical Wet"},
        {"Nicaragua", "Tropical Dry"},
        {"Niger", "Tropical Dry"},
        {"Nigeria", "Tropical Wet"},
        {"Northern Mariana Islands", "Tropical Wet"},
        {"Palestinian Authority or West Bank and Gaza Strip", "Tropical Dry"},
        {"Oman", "Tropical Dry"},
        {"Pakistan", "Tropical Dry"},
        {"Palau", "Tropical Wet"},
        {"Panama", "Tropical Wet"},
        {"Papua New Guinea", "Tropical Wet"},
        {"Paraguay", "Tropical Wet"},
        {"Peru", "Tropical Dry"},
        {"Philippines", "Tropical Wet"},
        {"Puerto Rico", "Tropical Wet"},
        {"Qatar", "Tropical Dry"},
        {"Reunion", "Tropical Wet"},
        {"Romania", "Warm Temperate Moist"},
        {"Russia", "Cold Temperate Moist"},
        {"Rwanda", "Tropical Dry"},
        {"Saint Helena", "Tropical Wet"},
        {"Saint Kitts and Nevis", "Tropical Wet"},
        {"Saint Lucia", "Tropical Wet"},
        {"Saint Pierre and Miquelon", "Cold Temperate Moist"},
        {"Saint Vincent and the Grenadines", "Tropical Wet"},
        {"Samoa", "Tropical Wet"},
        {"San Marino", "Warm Temperate Moist"},
        {"Saudi Arabia", "Tropical Dry"},
        {"Senegal", "Tropical Dry"},
        {"Seychelles", "Tropical Wet"},
        {"Sierra Leone", "Tropical Wet"},
        {"Singapore", "Tropical Wet"},
        {"Slovenia", "Warm Temperate Moist"},
        {"Solomon Islands", "Tropical Wet"},
        {"Somalia", "Tropical Dry"},
        {"South Africa", "Warm Temperate Dry"},
        {"Sri Lanka", "Tropical Wet"},
        {"Sudan", "Tropical Dry"},
        {"Suriname", "Tropical Wet"},
        {"Eswatini", "Tropical Dry"},
        {"Syrian Arab Republic", "Tropical Dry"},
        {"Tajikistan", "Warm Temperate Dry"},
        {"Tanzania", "Tropical Dry"},
        {"Thailand", "Tropical Wet"},
        {"Timor-Leste", "Tropical Wet"},
        {"Togo", "Tropical Wet"},
        {"Tokelau", "Tropical Wet"},
        {"Tonga", "Tropical Wet"},
        {"Trinidad and Tobago", "Tropical Wet"},
        {"Tunisia", "Tropical Wet"},
        {"Turkmenistan", "Warm Temperate Dry"},
        {"Turks and Caicos Islands", "Tropical Wet"},
        {"Tuvalu", "Tropical Wet"},
        {"Uganda", "Tropical Dry"},
        {"Ukraine", "Cold Temperate Moist"},
        {"United Arab Emirates", "Tropical Dry"},
        {"Uruguay", "Warm Temperate Moist"},
        {"Uzbekistan", "Warm Temprate Dry"},
        {"Vanuatu", "Tropical Wet"},
        {"Venezuela", "Tropical Wet"},
        {"Viet Nam", "Tropical Weet"},
        {"United States Virgin Islands", "Tropical Wet"},
        {"Wallis and Futuna", "Cold Temperate Moist"},
        {"Yemen", "Tropical Dry"},
        {"Zambia", "Tropical Dry"},
        {"Zimbabwe", "Tropical Wet"},

        // validated
    };

    unordered_map<string, double> MAP_WETLANDS_CLIMATE_TO_DIFFUSION_EMISSION_FACTORS{
        // CH4 MEASURED EMISSIONS FOR FLOODED LAND
        // TABLE 3A.2

        {"Polar Boreal Wet", 0.086},
        {"Cold Temperate Moist", 0.061},
        {"Warm Temperate Moist", 0.150},
        {"Warm Temperate Dry", 0.044},
        {"Tropical Wet", 0.630},
        {"Tropical Dry", 0.295},

        // validated
    };

public:
    std::unordered_map<std::string, std::unordered_map<std::string, std::unordered_map<std::string, double>>> MAP_EMISSION_FACTOR_FOR_METHANE_BY_MANURE_MANAGEMENT_SYSTEM{

        // METHANE EMISSION FACTORS BY ANIMAL CATEGORY, MANURE MANAGEMENT SYSTEM AND CLIMATE ZONE (G CH4 KG VS-1)

        {"Dairy Cattle", {
                             {"Lagoon", {{"Cool", 70.05}, {"Temperate", 92.35}, {"Warm", 97.91}}},
                             {"Liquid/Slurry", {{"Cool", 23.24}, {"Temperate", 48.33}, {"Warm", 87.4}}},
                             {"Pit", {{"Cool", 23.24}, {"Temperate", 48.33}, {"Warm", 87.4}}},
                             {"Solid Storage", {{"Cool", 2.45}, {"Temperate", 4.95}, {"Warm", 6.2}}},
                             {"Dry lot", {{"Cool", 1.25}, {"Temperate", 1.85}, {"Warm", 2.45}}},
                             {"Daily Spread", {{"Cool", 0.15}, {"Temperate", 0.6}, {"Warm", 1.25}}},
                             {"Anaerobic Digestion", {{"Cool", 6.2}, {"Temperate", 6.6}, {"Warm", 6.6}}},
                             {"Burned for fuel", {{"Cool", 12.4}, {"Temperate", 12.4}, {"Warm", 12.4}}},
                             {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                             {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                             {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                             {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                             {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                         }},
        {"Other Cattle", {
                             {"Lagoon", {{"Cool", 58.7}, {"Temperate", 77.38}, {"Warm", 82.06}}},
                             {"Liquid/Slurry", {{"Cool", 19.48}, {"Temperate", 40.48}, {"Warm", 73.23}}},
                             {"Pit", {{"Cool", 19.48}, {"Temperate", 40.48}, {"Warm", 73.23}}},
                             {"Solid Storage", {{"Cool", 2.05}, {"Temperate", 4.15}, {"Warm", 5.2}}},
                             {"Dry lot", {{"Cool", 1.05}, {"Temperate", 1.55}, {"Warm", 2.05}}},
                             {"Daily Spread", {{"Cool", 0.1}, {"Temperate", 0.5}, {"Warm", 1.05}}},
                             {"Anaerobic Digestion", {{"Cool", 5.8}, {"Temperate", 6.1}, {"Warm", 6.15}}},
                             {"Burned for fuel", {{"Cool", 10.4}, {"Temperate", 10.4}, {"Warm", 10.4}}},
                             {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                             {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                             {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                             {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                             {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},

                         }},
        {"Buffalo", {
                        {"Lagoon", {{"Cool", 49.25}, {"Temperate", 64.9}, {"Warm", 68.825}}}, {"Liquid/Slurry", {{"Cool", 16.325}, {"Temperate", 33.95}, {"Warm", 61.425}}}, {"Pit", {{"Cool", 16.325}, {"Temperate", 33.95}, {"Warm", 61.425}}}, {"Solid Storage", {{"Cool", 1.7}, {"Temperate", 3.5}, {"Warm", 4.4}}}, {"Dry lot", {{"Cool", 0.9}, {"Temperate", 1.3}, {"Warm", 1.7}}}, {"Daily Spread", {{"Cool", 0.1}, {"Temperate", 0.4}, {"Warm", 0.9}}}, {"Anaerobic Digestion", {{"Cool", 9.2}, {"Temperate", 9.5}, {"Warm", 9.5}}}, {"Burned for fuel", {{"Cool", 8.7}, {"Temperate", 8.7}, {"Warm", 8.7}}}, {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}}, {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}}, {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}}, {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}}, {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                        // Buffalo emmissions equivalent to low productivity non-diary cattles
                    }},
        {"Swine", {
                      {"Lagoon", {{"Cool", 140.04}, {"Temperate", 184.66}, {"Warm", 195.825}}},
                      {"Liquid/Slurry", {{"Cool", 46.475}, {"Temperate", 65.7}, {"Warm", 131.07}}},
                      {"Pit", {{"Cool", 46.475}, {"Temperate", 65.7}, {"Warm", 131.07}}},
                      {"Solid Storage", {{"Cool", 4.95}, {"Temperate", 9.95}, {"Warm", 12.4}}},
                      {"Dry lot", {{"Cool", 2.45}, {"Temperate", 3.7}, {"Warm", 4.95}}},
                      {"Daily Spread", {{"Cool", 0.25}, {"Temperate", 1.25}, {"Warm", 2.45}}},
                      {"Anaerobic Digestion", {{"Cool", 13.3}, {"Temperate", 13.95}, {"Warm", 14.1}}},
                      {"Burned for fuel", {{"Cool", 24.8}, {"Temperate", 24.8}, {"Warm", 24.8}}},
                      {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                      {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},

                  }},
        {"Poultry", {
                        {"Lagoon", {{"Cool", 118.6}, {"Temperate", 130.57}, {"Warm", 165.6}}},
                        {"Liquid/Slurry", {{"Cool", 39.68}, {"Temperate", 68.73}, {"Warm", 147.86}}},
                        {"Pit", {{"Cool", 39.68}, {"Temperate", 68.73}, {"Warm", 147.86}}},
                        {"Solid Storage", {{"Cool", 3.8}, {"Temperate", 6.45}, {"Warm", 7.75}}},
                        {"Dry lot", {{"Cool", 2.5}, {"Temperate", 3.15}, {"Warm", 3.8}}},
                        {"Daily Spread", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                        {"Anaerobic Digestion", {{"Cool", 3.8}, {"Temperate", 6.45}, {"Warm", 7.75}}},
                        {"Burned for fuel", {{"Cool", 2.5}, {"Temperate", 2.5}, {"Warm", 2.5}}},
                        {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                        {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                        {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                        {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                        {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},

                    }},
        {"Sheep", {
                      {"Lagoon", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Liquid/Slurry", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Pit", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Solid Storage", {{"Cool", 2.1}, {"Temperate", 4.3}, {"Warm", 5.4}}},
                      {"Dry lot", {{"Cool", 1.05}, {"Temperate", 1.6}, {"Warm", 2.1}}},
                      {"Daily Spread", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Anaerobic Digestion", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Burned for fuel", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                      {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                  }},
        {"Goats", {
                      {"Lagoon", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Liquid/Slurry", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Pit", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Solid Storage", {{"Cool", 2.05}, {"Temperate", 4.15}, {"Warm", 5.2}}},
                      {"Dry lot", {{"Cool", 1.55}, {"Temperate", 1.55}, {"Warm", 2.05}}},
                      {"Daily Spread", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Anaerobic Digestion", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Burned for fuel", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                      {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                  }},
        {"Camels", {
                       {"Lagoon", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Liquid/Slurry", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Pit", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Solid Storage", {{"Cool", 3.15}, {"Temperate", 6.3}, {"Warm", 7.85}}},
                       {"Dry lot", {{"Cool", 1.55}, {"Temperate", 2.35}, {"Warm", 3.5}}},
                       {"Daily Spread", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Anaerobic Digestion", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Burned for fuel", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                       {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                       {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                       {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                       {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                   }},
        {"Horses", {
                       {"Lagoon", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Liquid/Slurry", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Pit", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Solid Storage", {{"Cool", 3.75}, {"Temperate", 7.5}, {"Warm", 9.4}}},
                       {"Dry lot", {{"Cool", 1.85}, {"Temperate", 2.8}, {"Warm", 3.75}}},
                       {"Daily Spread", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Anaerobic Digestion", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Burned for fuel", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                       {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                       {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                       {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                       {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                       {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                   }},
        {"Mules", {
                      {"Lagoon", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Liquid/Slurry", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Pit", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Solid Storage", {{"Cool", 3.95}, {"Temperate", 7.9}, {"Warm", 9.9}}},
                      {"Dry lot", {{"Cool", 1.95}, {"Temperate", 2.95}, {"Warm", 3.95}}},
                      {"Daily Spread", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Anaerobic Digestion", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Burned for fuel", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                      {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                  }},
        {"Asses", {
                      {"Lagoon", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Liquid/Slurry", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Pit", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Solid Storage", {{"Cool", 3.95}, {"Temperate", 7.9}, {"Warm", 9.9}}},
                      {"Dry lot", {{"Cool", 1.95}, {"Temperate", 2.95}, {"Warm", 3.95}}},
                      {"Daily Spread", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Anaerobic Digestion", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Burned for fuel", {{"Cool", 0.0}, {"Temperate", 0.0}, {"Warm", 0.0}}},
                      {"Pasture Range and Paddock", {{"Cool", 0.6}, {"Temperate", 0.6}, {"Warm", 0.6}}},
                      {"Composting", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Deep bedding", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Poultry manure", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                      {"Aerobic treatment", {{"Cool", 0}, {"Temperate", 0}, {"Warm", 0}}},
                  }},

                  // validated
    };

    std::unordered_map<std::string, std::unordered_map<std::string, std::unordered_map<std::string, double>>> AWMS{

        // ANIMAL WASTE MANAGEMENT SYSTEM (AWMS) REGIONAL AVERAGES (fractions: no units)
        // Table 10A.9 Ch10

        {"Dairy Cattle", {
                             {"North America", {{"Lagoon", 0.26}, {"Liquid/Slurry", 0.24}, {"Solid Storage", 0.24}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.15}, {"Daily Spread", 0.11}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.43}, {"Solid Storage", 0.29}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.26}, {"Daily Spread", 0.02}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.05}, {"Solid Storage", 0.74}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.20}, {"Daily Spread", 0.01}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Oceania", {{"Lagoon", 0.05}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.94}, {"Daily Spread", 0.01}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.01}, {"Solid Storage", 0.21}, {"Dry lot", 0.29}, {"Pasture Range and Paddock", 0.38}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.11}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.01}, {"Dry lot", 0.49}, {"Pasture Range and Paddock", 0.30}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.20}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.05}, {"Dry lot", 0.38}, {"Pasture Range and Paddock", 0.57}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.20}, {"Dry lot", 0.29}, {"Pasture Range and Paddock", 0.45}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.06}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.14}, {"Dry lot", 0.35}, {"Pasture Range and Paddock", 0.46}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.05}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                         }},
        {"Other Cattle", {
                             {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.01}, {"Solid Storage", 0.43}, {"Dry lot", 0.14}, {"Pasture Range and Paddock", 0.42}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.22}, {"Solid Storage", 0.26}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.48}, {"Daily Spread", 0.04}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.64}, {"Solid Storage", 0.05}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.31}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.29}, {"Dry lot", 0.28}, {"Pasture Range and Paddock", 0.36}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.07}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.01}, {"Dry lot", 0.49}, {"Pasture Range and Paddock", 0.30}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.20}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.03}, {"Dry lot", 0.05}, {"Pasture Range and Paddock", 0.92}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.15}, {"Dry lot", 0.30}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.05}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                             {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.005}, {"Dry lot", 0.46}, {"Pasture Range and Paddock", 0.42}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.07}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                         }},
        {"Buffalo", {
                        {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.43}, {"Solid Storage", 0.40}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.17}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.34}, {"Solid Storage", 0.63}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.03}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.14}, {"Solid Storage", 0.66}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.2}, {"Daily Spread", 0.01}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.06}, {"Dry lot", 0.61}, {"Pasture Range and Paddock", 0.29}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.03}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Indian Subcontinent ", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.01}, {"Dry lot", 0.41}, {"Pasture Range and Paddock", 0.39}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.20}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.020}, {"Dry lot", 0.27}, {"Pasture Range and Paddock", 0.72}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.24}, {"Pasture Range and Paddock", 0.52}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.08}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.24}, {"Pasture Range and Paddock", 0.52}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.08}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                    }},
        {"Sheep", {

                      {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.54}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.46}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.83}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.48}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.52}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.50}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                  }},
        {"Goats", {
                      {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.75}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.25}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.5}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                  }},
        {"Poultry", {
                        {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                        {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                        {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                        {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                        {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                        {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                        {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                        {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                        {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 1}, {"Aerobic treatment", 0}}},
                    }},
        {"Swine", {
                      {"North America", {{"Lagoon", 0.28}, {"Liquid/Slurry", 0.31}, {"Solid Storage", 0.04}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0.17}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Western Europe", {{"Lagoon", 0.06}, {"Liquid/Slurry", 0.51}, {"Solid Storage", 0.15}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.01}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0.14}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Eastern Europe", {{"Lagoon", 0.005}, {"Liquid/Slurry", 0.22}, {"Solid Storage", 0.68}, {"Dry lot", 0.001}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0.004}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Oceania", {{"Lagoon", 0.91}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.01}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Asia", {{"Lagoon", 0.2}, {"Liquid/Slurry", 0.31}, {"Solid Storage", 0.1}, {"Dry lot", 0.08}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.03}, {"Anaerobic Digestion", 0.06}, {"Burned for fuel", 0.0}, {"Pit", 0.13}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Indian Subcontinent", {{"Lagoon", 0.09}, {"Liquid/Slurry", 0.27}, {"Solid Storage", 0.14}, {"Dry lot", 0.24}, {"Pasture Range and Paddock", 0.03}, {"Daily Spread", 0.06}, {"Anaerobic Digestion", 0.06}, {"Burned for fuel", 0.0}, {"Pit", 0.05}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Latin America", {{"Lagoon", 0.08}, {"Liquid/Slurry", 0.32}, {"Solid Storage", 0.14}, {"Dry lot", 0.28}, {"Pasture Range and Paddock", 0.03}, {"Daily Spread", 0.04}, {"Anaerobic Digestion", 0.03}, {"Burned for fuel", 0.0}, {"Pit", 0.05}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Africa", {{"Lagoon", 0.03}, {"Liquid/Slurry", 0.19}, {"Solid Storage", 0.11}, {"Dry lot", 0.51}, {"Pasture Range and Paddock", 0.03}, {"Daily Spread", 0.03}, {"Anaerobic Digestion", 0.03}, {"Burned for fuel", 0.0}, {"Pit", 0.05}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Middle East", {{"Lagoon", 0.08}, {"Liquid/Slurry", 0.30}, {"Solid Storage", 0.08}, {"Dry lot", 0.35}, {"Pasture Range and Paddock", 0.03}, {"Daily Spread", 0.03}, {"Anaerobic Digestion", 0.06}, {"Burned for fuel", 0.0}, {"Pit", 0.1}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                  }},
        {"Hens", {
                     {"North America", {{"Lagoon", 0.01}, {"Liquid/Slurry", 0.29}, {"Solid Storage", 0.70}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                     {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.50}, {"Daily Spread", 0.50}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                     {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.05}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0.93}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0.002}, {"Aerobic treatment", 0}}},
                     {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.23}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0.77}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                     {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.01}, {"Daily Spread", 0.01}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0.94}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                     {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 1}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.50}, {"Daily Spread", 0.50}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                     {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.58}, {"Solid Storage", 0.42}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                     {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.50}, {"Daily Spread", 0.50}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                     {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.00}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0.90}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0.10}, {"Aerobic treatment", 0}}},
                 }},
        {"Asses", {
                      {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.75}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.25}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.5}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                  }},
        {"Mules", {
                      {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.75}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.25}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.5}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                  }},
        {"Camels", {
                       {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.75}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.25}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.5}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                   }},
        {"Horses", {
                       {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.75}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.25}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                       {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.5}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                   }},
        {"Turkeys", {
                        {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.75}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.25}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                        {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.5}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                    }},
        {"Ducks", {
                      {"North America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Western Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Eastern Europe", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.75}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.25}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Oceania", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 1.0}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Asia", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Indian Subcontinent", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.5}, {"Dry lot", 0.0}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Latin America", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Africa", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.17}, {"Dry lot", 0.03}, {"Pasture Range and Paddock", 0.80}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                      {"Middle East", {{"Lagoon", 0.0}, {"Liquid/Slurry", 0.0}, {"Solid Storage", 0.0}, {"Dry lot", 0.5}, {"Pasture Range and Paddock", 0.5}, {"Daily Spread", 0.0}, {"Anaerobic Digestion", 0.0}, {"Burned for fuel", 0.0}, {"Pit", 0}, {"Composting", 0}, {"Deep bedding", 0}, {"Poultry manure", 0}, {"Aerobic treatment", 0}}},
                  }},

                  // validated

    };

public:
    // Returns region of country
    string getRegionOfCountry(string country);

    // Returns category of animal for VSE rate calculations
    string getAnimalCategoryforVolatileSolidExcretionRate(string animal);

    // Returns VSE rate
    double getVolatileSolidExcretionRate(string region, string animal);

    // returns animal category for typical animal mass calc
    string getAnimalCategoryForTypicalAnimalMass(string animal);

    // returns typical animal mass of animal
    double getTypicalAnimalMass(string animal, string country);

    // returns animal category for FRACGAS
    string getAnimalCategoryforFRACGAS(string animal);

    string getClimateofRegion(string region);

    double getFRACGAS(string manureSytem, string animalCategory);

    double getNitrogenExcretionRate(string region, string animalCategory);

    double getEmissionFactorNitrogenEmissionsFromManureMangement(string manure_management_system);

    double getEmissionFactorForMethaneEmissionFromEntericfermentation(string country, string animal);

    string getClimateforCountryWetlands(string country);

    double getDiffusiveEmissionFactorForWetlands(string country);
};


struct dataHolder1
{ // data container template for files with 2 columns (year and value)
    int year = 0.0;
    double value = 0.0;
    dataHolder1() = default;
    dataHolder1(int y, double v) : year(y), value(v) {}
};

struct dataHolder2
{ // data container template for files with 3 columns (year and 2 valuea)
    int year = 0.0;
    double value1 = 0.0;
    double value2 = 0.0;
    dataHolder2() = default;
    dataHolder2(int y, double v1, double v2) : year(y), value1(v1), value2(v2) {}
};

struct PLUMFileDataStruct
{
    int year = 0.0;
    string country;
    string item;
    double nheads = 0.0; // in millions
};

// structs to asssit read data from LPJG files
struct readcflux
{
    double lon, lat, veg, repr, soil, fire, est, nee;
    int year;
    double sum;
};

struct readNitrogen
{
    double lon, lat, NH3_fire, NH3_soil, NOx_fire, NOx_soil, N20_fire, N20_soil, N2_fire, N2_soil, total;
    int year;
    double sum_ngases;
};

struct readMethane
{
    double lon, lat, jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec;
    int year;
    double sum_ch4;
};

// wetlands
struct readWetlands
{
    string country, variable, year, measure, value;
};

// plum landuse
struct readPLUMLandUSe
{
    double Lon, Lat, area, suitable, managedForest, unmanagedForest, otherNatural, cropland, pasture, barren, urban, pasture_A, pasture_FI, pasture_FQ, pasture_II, pasture_IQ, pasture_OI, pasture_Y, energycrops_A, energycrops_FI, energycrops_FQ, energycrops_II, energycrops_IQ, energycrops_OI, energycrops_Y, wheat_A, wheat_FI, wheat_FQ, wheat_II, wheat_IQ, wheat_OI, wheat_Y, oilcrops_A, oilcrops_FI, oilcrops_FQ, oilcrops_II, oilcrops_IQ, oilcrops_OI, oilcrops_Y, maize_A, maize_FI, maize_FQ, maize_II, maize_IQ, maize_OI, maize_Y, rice_A, rice_FI, rice_FQ, rice_II, rice_IQ, rice_OI, rice_Y, pulses_A, pulses_FI, pulses_FQ, pulses_II, pulses_IQ, pulses_OI, pulses_Y, setaside_A, setaside_FI, setaside_FQ, setaside_II, setaside_IQ, setaside_OI, setaside_Y, starchyRoots_A, starchyRoots_FI, starchyRoots_FQ, starchyRoots_II, starchyRoots_IQ, starchyRoots_OI, starchyRoots_Y;
};

struct readRiceMethane
{
    string domainCode, domain, areaCode, Area, elementCode, element, itemCode, item, yearCode, unit, value, flag, flagDescription;
    int year;
    double methaneEmissions;
};

class FileManager {

public:
    //constructor
    FileManager();

    //destrcutor
    ~FileManager();

    //Reads data containing 2 columns (year, value) in file and returns vector containing data
    vector<dataHolder1>loadFile2(string fileName)const;

    ////Reads data containing 2 columns (year, value1, value2) in file and returns vector containing data
    vector<dataHolder2>loadFile3(string fileName)const;

    //opens a file and returns the stream. read=true if file will be read from and false if file will be written to.
    fstream openFile(string fileName, bool read = true) const;

    //closes file
    void closeFile(fstream& myStream) const;

    //deletes file
    void deleteFile(string fileName) const;

    //reads csv
    void loadFileCSV()const;

    //deletes folder and all contents
    void deleteFolder(string folderPath) const;

    //prints data in vector to file (2 columns)
    void printToFile(string filePath, vector<dataHolder1>myVector, int precision = 5)const;

    //prints data in vector to fil  (3 columns)
    void printToFile(string filePath, vector<dataHolder2>myVector, int precision = 5)const;

    //prints vector of 2 columns to console
    void printToConsole(vector<dataHolder1>myVector)const;

    //prints vector of 3 columns to console
    void printToConsole(vector<dataHolder2>myVector)const;
};


class PlumDataProcessor
{

private:
    vector<dataHolder1>totalFertlizerAmountPerSSP;
    vector<dataHolder1>manureFertilizerAmount;
    vector<dataHolder1>syntheticFertilizerAmount;
    FileManager myFileManager;
    string PLUMDataFilePath = "SSPX_s1_YYYY_LandUse.txt";
    string PLUMDataFilePath_v2 = "SSPY_s1_LandUseAgg.csv";
    string basePathPLUMdata = " ";
    string plumFertlizerPath = " ";
    string plumFertilizerOutputPath = " ";



public:

    PlumDataProcessor();

    PlumDataProcessor(string filePath, string filePath2);

    ~PlumDataProcessor();

    //returns totalFertizerAmount vector
    vector<dataHolder1> getTotalFertilizerAmounts();

    //returns manureFertilizerAmount vector
    vector<dataHolder1> getManureFertilizerAmount();

    //returns syntheticFertilizerAmount vector
    vector<dataHolder1> getSyntheticFertilizerAmount();

    void extractDataFromPlumLandUseFiles();

    string generateFilePath(string ssp, string year);

    void printPLUMTotalFertilizer(int index);

    vector<dataHolder1>readFertilizerData();

    void setplumFertlizerPath(string filePath);

    void extractDataFromPlumLandUseFiles_v2();
};


class Adder
{

private:
    // file manager to hamdle file management
    FileManager myFileManager;

    // To hold total CH4 and N20 data
    vector<dataHolder2> myTotalData_lpjg_ipcc_sim_calc;

    // To hold total CH4 data
    vector<dataHolder1> myTotalMethaneData;

    // To hold methane for LPJG+IPCC
    vector<dataHolder1> myLPJG_IPCC_Wetlands_only_methane;

    // To hold nitrogen for LPJG+IPCC
    vector<dataHolder1> myLPJG_IPCC_Wetlands_only_nitrogen;

    // To hold total N2O data
    vector<dataHolder1> myTotalNitrogenData; // to holdN20 data

    // file path for total methane and nitrogen single file
    string fileTotalMethaneNitrogenPath;

    // file path for IIASA non_lpjg from 1850_2009
    string IIASA_non_lpjg_1850_2100_file_path = " ";

    // file path for IIASA lpjg from 1850_2009
    string IIASA_lpjg_1850_2100_file_path = " ";

    // vector to hold IIASA non-lpjg data set from 1850_2100
    vector<dataHolder2> IIASA_non_lpjg_1850_2100;

    string lpjgcflux_plus_iiasa_lpjg_co2_file_path = " ";
    string IIASA_lpjg_co2_file_path = " ";

    // vector to hold IIASA lpjg data set from 1850_2100
    vector<dataHolder2> IIASA_lpjg_1850_2100;

    vector<dataHolder2> actual_lpjg_simulated_IIASA_1850_2009_lpjg_2010_2100;

    vector<dataHolder2> total_combined_iiasa_historic_1850_1960_lpjg__ipcc_fao_1961_2100;

    string file_LPJG_IPCC_only;

    vector<dataHolder2> LPJG_IPCC_Only_Methane_Nitrogen;

    vector<dataHolder1> IIASA_lpjg_co2;

    vector<dataHolder1> cflux_iiasa_co2_1850_1960_lpjg_2100;

    // method to read IIASA_non_lpjg_1850_2100 from file
    void read_IIASA_non_lpjg_1850_2010();

    // method to set IIASA_non_lpjg_1850_2100 file path
    void set_IIASA_non_lpjg_1850_2100_file_path(string path);

    // method to read IIASA_lpjg_1850_2100 from file
    void read_IIASA_lpjg_1850_2010();

    void read_IIASA_co2_lpjg_1850_2100();

    // method to set IIASA_lpjg_1850_2100 file path
    void set_IIASA_lpjg_1850_2100_file_path(string path);

public:
    // default contructor
    Adder();

    // custom constructor
    Adder(string total_methane_nitrogen_file_output_file_path, string IIASA_non_lpjg_1850_2009_file_path, string IIASA_lpjg_1850_2009_file_path, string filePath_LPJG_IPCC_only, string lpjgcflux_plus_iiasa_lpjg_co2, string IIASA_lpjg_co2_file);

    // destructor
    ~Adder();

    // main addition framework
    void startAddition(vector<dataHolder1>& LPJGCfluxData, vector<dataHolder1>& IPCCMethane, vector<dataHolder1>& WetlandsMethane, vector<dataHolder1>& LPJGMethane, vector<dataHolder1>& LPJGNitrogen, vector<dataHolder1>& IPCCNitrogen, vector<dataHolder1>& Historic_methane_1961_2009, vector<dataHolder1>& Historic_nitrogen_1961_2009);

    // prints total methane and nitrogen into single file ready for IMOGEN use
    void PrintTotalMethaneNitrogenToFile();

    // setter: sets total methane nitrogen path
    void setTotalMethaneNitrogenFilePath(string path);

    void set_actual_lpjg_simulated_IIASA_1850_2009_lpjg_2010_2100();

    std::vector<double> centeredMovingAverage(std::vector<double> data, int window_size = 3);

    vector<dataHolder2> get_total_data_iiasa_historic_lpjg_sim();
};


// Header file containing declarations of calculators needed to do all
// mathematical calcuations throughout this codebase

class Calculator
{

private:
    // vector to hold loaded countries ie if you wish to generate distinct countries from given PLUM data set
    vector<string> myCountries;

    // loads countries. If needed, call in constructor
    void loadCountries();

    // Maps
    Maps myMaps;

    // calculates volatile solid excretion for CH4 emmissions from manure management | units = KgVs/animal/yr
    double calcVolalileSolidExcretion(double volatile_solid_excretion_rate, double typical_animal_mass) const;

    // Calculates nitrogen excretion | units =
    double calcNitrogenExcretion(double nitrogen_excretion_rate, double animalMass);

    // converts: Kg to Tg
    const double CONVERT_Kg_TO_Tg = 1e-9;

public:
    // default constructor | Loads countries into myCountries vector (If needed)
    Calculator();

    // destructor
    ~Calculator();

    // calculates enteric fermentation emmissions from a livestock category | //units = TgCH4/yr
    double calcCH4EntericFermentation(string country, string animal, double nHeads);

    // calculates CH4 emmissions from manure management | units = TgCH4/yr
    double calcCH4ManureManagement(string country, string animal, int nHeads);

    // calculates N20 emissions from manure management | units = TgN2O/yr
    double calcN20ManureManagement(int nHeads, string country, string animal);

    // calculates methane emissions from wetlands | average ice free period = 250 | units=TgCH4/yr
    double calcCH4Wetlands(double diffusiveEmissionRate, double area, int ice_free_period = 250);

    // Calculates nitrous oxide gases from managed soils | units = TgN20/yr
    double calcN2OManagedSoils(double FSN_FON_total_fertilizer, double EF1_avg = 0.01, double EF1FR = 0.0, double EF2_avg = 0.0, double FOS_area_drained_soils = 0.0, double FPRP_organic_fert = 0.0, double EF3_avg = 0.0);
};




class DualStreamBuffer : public std::streambuf
{
private:
    std::streambuf* coutBuf;
    std::ofstream fileBuf;

protected:
    // Method called when the buffer overflows (i.e., when it's full or when std::flush is called)
    virtual int_type overflow(int_type c = traits_type::eof())
    {
        if (c != traits_type::eof())
        {
            // Write the character both to std::cout and the file
            coutBuf->sputc(c);
            fileBuf.put(c);
        }
        return c;
    }

    // Synchronizes the buffer (writes the buffer's content to its final destination)
    virtual int sync()
    {
        coutBuf->pubsync();
        fileBuf.flush();
        return 0;
    }

public:
    DualStreamBuffer(std::ostream& coutStream, const std::string& filename)
        : coutBuf(coutStream.rdbuf()), fileBuf(filename)
    {
        // Set the stream buffer of coutStream to this custom stream buffer
        coutStream.rdbuf(this);
    }

    ~DualStreamBuffer()
    {
        // Restore the original stream buffer of std::cout when the object is destroyed
        std::cout.rdbuf(coutBuf);
    }
};



class Extractor
{

private:
    // first and last year of lPJG run
    int myFirstHistYear, myLastHistYear;

    // file manager for file management
    FileManager myFileManager;

    // output directory where LPJG output is contained
    string myOutputDirectory;

    // relative path to cflux.out file
    string cfluxFilePath;

    // relative path to ngaes.out file
    string nitrogenFilePath;

    // relative path to mCH4.out file
    string methaneFilepath;

    // vector to gold methane data
    vector<dataHolder1> myLPJGMethane;

    // vector to hold nitrogen data
    vector<dataHolder1> myLPJGNitrogen;

    // vector to hold cflux data
    vector<dataHolder1> myLPJGCflux;

    // struct variable to help read cflux data
    readcflux myReadCflux;

    // struct variable to help read methane data
    readMethane myReadMethane;

    // struct variable to help read nitrogen data
    readNitrogen myReadNitrogen;

    double calcGridCellArea(double lon, double lat);

    // converter: g to Tg
    const double CONVERT_g_Tg = 1e-12;

    const double CONVERT_Kg_Tg = 1e-9;

    const double PI = 3.141592653589793;

    double earth_radius(double lat = 0.0, const std::string& unit = "");

    double cdtarea(double lat, double lon, double dlat, double dlon, bool km2 = false); // get gridcell area

public:
    // deafult constructor
    Extractor();

    // destructor
    ~Extractor();

    // constructor
    Extractor(string path, int firsthistyear, int lasthistyear); // sets output dir file path adn cflux, ngases, methane filepaths

    // setter: sets output directory
    void setOutputDirectory(string path);

    // main framework to start extraction
    void startLPJGDataExtraction();

    void printLPJGEmissionsData(string methanePath, string nitrogenPath, string cfluxPath);

    // vector to hold LPJG methane data
    vector<dataHolder1> getLPJGMethaneData();

    // vector to hold LPJG nitrogen data
    vector<dataHolder1> getLPJGNitrogenData();

    // vetcor to hold LPJG cflux data
    vector<dataHolder1> getLPJGCfluxData();
};







class MethaneEmissions
{

private:
    Calculator myCalculator;

    FileManager myFileManager;

    vector<dataHolder1> myCH4Data; // holds methane emissions data  units = TgCH4/yr

    vector<dataHolder1> myEntericCH4Data; // holds methane emissions from enteric fermentation data  units = TgCH4/yr

    vector<dataHolder1> myManureManagementCH4Data; // holds methane emissions from manure management data  units = TgCH4/yr

    vector<dataHolder1> myHistoricMethane_modelled_1961_2009;

    string PLUMdataFilePath;

    PLUMFileDataStruct myPLUMData;

    readRiceMethane myRiceMethaneData;

    string methaneEmissionsOutputFilePath = " ";

    string entericFermentationMethaneEmissionsOutputFilePath = " ";

    string manureManagementMethaneEmissionsOutputFilePath = " ";

    string historic_livestock_counts_1961_2100_path = " ";

    string rice_cultivation_emissions_file_path = " ";

    int yearTracker = 2010;

    double yearlyCH4 = 0.0;

    const double CONVERT_Kg_TO_Gg = 1e-6;

    const double CONVERT_Gg_TO_Tg = 1e-3;

    const int MILLION = 1000000;

    // Boolean to control rice cultivation emissions simulation

    //// Turned rice cultivation emissions off here because Daniel said LPJG simulaes rice cultivation on 31/10/2023
    bool simulate_ipcc_fao_owi_rice_cultivation_methane_emissions = false;

public:
    // default constructor
    MethaneEmissions();

    ~MethaneEmissions();

    // custom constructor to set path to PLUM data
    MethaneEmissions(string path);

    // returns methane data vector
    vector<dataHolder1> getMethaneData();

    // returns data for emissions from enteric fermentation
    vector<dataHolder1> getEntericFermentationMethane();

    // returns data for emissions from manure management
    vector<dataHolder1> getManureManagementMethane();

    // main computational function
    void startCalculations();

    // setter to set file path
    void setPLUMDataFilePath(string path);

    int getYearTrackKeeper();

    void setYearTrackkeeper(int value);

    void setMethaneEmissionsOutputFilePaths(string entericFilePath, string manureManagementFilePath, string totalFilePath);

    void printMethaneEmissions();

    void printEntericFermentationMethaneEmissions();

    void printManureManagementMethaneEmissions();

    void startCalculation_methane_modelled_historic_1961_2009();

    void startCalculation_methane_scenario_2010_2100();

    void setAuxFilePath(string livestocks_counts_path, string fao_stats_path);

    vector<dataHolder1> get_historic_methane_1961_2009();
};



class NitrogenEmissions
{

private:
    // Maps
    Maps myMaps;

    // vector containing N2O total data, need for N2O vector for manure management?
    vector<dataHolder1> myN2OData;

    // vector containing N2O emissions from managaed soils
    vector<dataHolder1> myN2ODataManagedSoils;

    // struct variable to hold data whilst reading plum data
    PLUMFileDataStruct myPLUMData;

    // path to fertlizer data from plum
    string plumFertlizerPath = " ";

    // plum data processor
    PlumDataProcessor myPlumDataProcessor;

    // calculator
    Calculator myCalculator;

    // file manager
    FileManager myFileManager;

    // path to plum data
    string PLUMdataFilePath;

    // path to nitrogen emissions outfile file
    string NitrogenEmissionsOutputFilePath = " ";

    string historic_livestock_counts_1961_2100_path = " ";

    string nitrogen_histoic_fertilzer_file_path = " ";

    string arable_land_nitrogen_fert_path = " ";

    // track year
    int yearTracker = 2010;

    // yearly n2O
    double yearlyN2O = 0.0;

    // kg to Tg convertor
    const double CONVERT_Kg_TO_Tg = 1e-9;

    vector<dataHolder1> modelled_historic_nitrogen_1961_2009;

    // boolean to control simulation of nitrogen emission from fertilizer application
    //  Turned nitrogen emissions off here because Daniel said LPJG simulaes rice cultivation on 31/10/2023
    bool simulate_nitrogen_emissions_from_fertilizer_application = false;

public:
    // default constructor
    NitrogenEmissions();

    // destructor
    ~NitrogenEmissions();

    // custom constructor to set path to PLUM data
    NitrogenEmissions(string plumPath, string fertFilePath);

    // returns methane data vector
    vector<dataHolder1> getNitrogenData();

    // main computational function
    void startCalculations();

    // setter to set file path
    void setPLUMDataFilePath(string path);

    int getYearTrackKeeper();

    // setter: sets nitrogen output file path
    void setNitrogenEmissionsOutputFilePath(string filePath);

    // prins n2O emissions data
    void printNitrogenEmissions();

    void setFertDataFilePath(string path);

    void startCalculations_historic_nitrogen_1961_2009();

    void setAuxFilePath(string livestocks_counts_path, string nitrogen_fetilizer_path, string arable_land_path);

    vector<dataHolder1> get_historic_nitrogen_1961_2009();

    void startCalculation_nitrogen_scenario_2010_2100();
};



//// scenario: cmip5 or cmip6
//extern std::string scenario;
//
//// config map
//extern std::map<std::string, std::string> config;
//
//// ssps, rcps vector specification
//extern std::vector<std::string> ssps, rcps;
//
//// first and last model simulation year
//extern int firstyear, lastyear;
//
//// Base dir and path to log file
//extern std::string baseDirectory, pathToLogFile;
//
//extern std::string myPLUMDataFilePath;
//
//// Path to LPJG ouput files
//extern std::string lpjgOutputDirectory;
//
//extern std::string methaneEmissionOutputFilePath;
//
//// File path for file containing methane emissions from enteric fermentation
//extern std::string entericFermentationMethaneOutputFilePath;
//
//// File path for file containing methane emissions from manure management systems
//extern std::string manureManagementMethaneOutputFilePath;
//
//// File path for file containing total nitrogen emissions
//extern std::string nitrogenEmissionOutputFilePath;
//
//// File path for file conatining nitrogen emissions from fertilizer
//extern std::string historic_nitrogen_fertiizer_file_path;
//
//// File path for file conatining nitrogen emissions from fertilizer
//extern std::string arable_lands_nitrogen_fertilizer_path;
//
//// File path for file containing total methane and total nitrogen emissions in one file
//extern std::string methaneNitrogenTotalOutputFilePath;
//
//// File path for file containing wetland areas
//extern std::string wetlandsAreaFilePath;
//
//// File path for file containing methane emissions from wetlands
//extern std::string wetlandsMethaneEmissionsOutputPath;
//
//// Folder path for plum land use data v1
//extern std::string basePathPLUMdata;
//
//// Folder path for plum land use data v2
//extern std::string basePathPLUMdata_v2;
//
//// File path for PLUM pre-processed fertilizer emissions output path
//extern std::string plumFertilizerOutputPath;
//
//// File path for file containing modelled nitrogen and methane emissions
//extern std::string file_LPJG_IPCC_Path;
//
//// File path for preprocessed plum fertilizers
//extern std::string plumFertlizerPath;
//
//// File path for LPJG methane
//extern std::string lpjgMethane;
//
//// File path for LPJG nitrogen
//extern std::string lpjgNitrogen;
//
//// File path for LPJG cflux
//extern std::string lpjgCflux;
//
//// File path for LPJG clfux + IIASA co2
//extern std::string lpjgCflux_plus_IIASA_lpjg_co2;
//
//// File path for LPJG co2 replacement (IIASA corresponding version)
//extern std::string IIASA_lpjg_co2_file_path;
//
//// File path for component of IIASA not simulated by LPJG and IPCC (ch4 and n2o only)
//extern std::string IIASA_non_lpjg_1850_2100;
//
//// File path for component of IIASA simulated by LPJG and IPCC (ch4 and n2o only)
//extern std::string IIASA_lpjg_1850_2100;
//
//// File path to OWI livestock counts
//extern std::string livestock_counts_path;
//
//// File path to FAO fertilizer and arable land data
//extern std::string fao_stats_path;
//
//extern int lpjg_start_year, lpjg_end_year;
//
//extern bool simulate_ipcc_fao_owi_rice_cultivation_methane_emissions;



class UtilityHandler
{
public:
    // Method to read and parse the configuration file
    static std::map<std::string, std::string> readConfig(const std::string& filename);

    static void printMap(const std::map<std::string, std::string>& map);

    static std::string replacePlaceholders(const std::string& path, const std::string& baseDirectory, const std::string& ssp, const std::string& rcp);

    static std::vector<std::string> split(const std::string& str, char delimiter);

    static void printVector(const std::vector<std::string>& vector);

    // Trims whitespace from the start of a string
    static inline std::string& ltrim(std::string& str);

    // Trims whitespace from the end of a string
    static inline std::string& rtrim(std::string& str);

    // Trims whitespace from both ends of a string
    static inline std::string& trim(std::string& str);

    static void replaceAll(std::string& str, const std::string& from, const std::string& to);

    static void replaceSubstring(std::string& str, const std::string& from, const std::string& to);
};




class Wetlands
{

private:
    //vector holding wetlands data
    vector<dataHolder1>wetlandsCH4;

    //average ice free period, later make it country specific
    const int ICE_FREE_PERIOD = 250;

    //conversion ratio from ha to sqkm
    const int CONVERTER_HA_SQKM = 100;

    //struct variable to hold components of wetlands area excel sheet
    readWetlands myReadWetlands;

    //file manager to handle file managemnt
    FileManager myFileManager;

    //calculaotor
    Calculator myCalculator;

    //Maps
    Maps myMaps;

    //wetalnds area file path
    string wetlandsAreaFilePath = " ";

    //path to methane emissions from wetlands
    string wetlandsMethaneOutputFilePath;

    //static total wetalnds
    double Ch4_wetlands_total = 0.0;

public:

    //default constructor
    Wetlands();

    //custom constructor
    Wetlands(string filePath);

    //detructor
    ~Wetlands();

    //main framework 
    void startCalculation();

    //getter: returns methane from wetlands vector
    vector < dataHolder1> getWetlandsMethaneData();

    //setter: setss wetlands area file path
    void setWetlandsAreaFilePath(string filePath);

    //sets wetlands methane emissions output path
    void setWetlandsMethaneOutputFilePath(string filePath);

    //prints wetlands output path to a file
    void printWetlandsMethaneData();

};
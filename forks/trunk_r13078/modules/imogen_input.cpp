///////////////////////////////////////////////////////////////////////////////////////
/// \file ImogenInput.cpp8
/// \brief Input module for CF conforming NetCDF files
///
/// \author Peter Anthoni
/// $Date: 2018-xx-xx xx:xx:xx $
///
///
///Note: native imogen ouput has gridpoints 3.75 x 2.5 deg
///      imogen seems midpoint but centered at c(0.0,0.0)
///
///////////////////////////////////////////////////////////////////////////////////////

#include "config.h"
#include "imogen_input.h"
#include "guess.h"
#include "driver.h"
#include "guessstring.h"
#include <fstream>
#include <sstream>
#include <string.h>
#include <algorithm>
#include <sys/stat.h>
#include <vector>
#include <cstddef> // für size_t 
#include <iostream>


// cru is at the moment still needed for soil code
#include "cruinput.h"

//DKB ifdef so it can run on platforms without MPI
#ifdef HAVE_MPI
#include <mpi.h>
#endif // MPI



namespace {
	int verbose = 1;
// I had the ff. in the gutil.cpp/h, but that one is somehow svn referenced
// so just define am local.

  template <typename T> xtring to_xtring(T value) {
    std::ostringstream os;
    os << value;
    return xtring(os.str().c_str());
  }


  /*
  Below is a regular void function. Notice it begins with static. the static means this funciton is not accessible outside this source file
   so the programmer can name the function the way he wants without worrying of name conflicts with other source file in the code base
  The purpose of this function is to create a directory. iT takes 2 paramters. 1. A constant character pointer pointing to the name of the direcroy 2. A file/directory permission code

  File permission codes (in unix) are used to specify the category of person who can perform a category of operations on a directory or a file
  There are three user categories: User (the owner of the file), Group (the security group you are in), and Other (for the world to see). Each category has three 
  permissions that can be set: r, w, and x to read, write, and execute a file, respectively. Permissions consist of three numbers: 4 for Read, 2 for Write, and 1 for Execute access.
  By adding these numbers together, you form the permissions that make up one digit.
  For example, 4 + 2 + 1 = 7, which grants read, write, and execute permissions; 4 + 1 = 5, which grants only read and execute permissions. Thus, 755 grants 7 (read, write, execute) 
  to the owner of the file, and 5 (read and execute) to the group the file is in and 5 (read and execute) to the world. 
  Each digit corresponds to a set of permissions (read, write, or execute) and the position of the digit corresponds to the user category (left = owner, middle = group, right = other).
  eg: 777 means all can read/write/execute (full access)
  755 - owner can rea/write/execute, group/others can read/execute

  Usually, there's a leading zero, so 755 can be written as 0755. The leading zero just means the following 3 digits are in the octal number system
  */

  static void _mkdir(const char *dir, int mode) {
    char tmp[256]; // character array of size 256 declared to hold the individual charcters for the directory paath. Remember this fucntion creates a directory
    char *p = NULL; //character pointer declared and initialized. Remember, using uninitialized pointer will crush your program
    size_t len; // size_t is a typedef(alias) of unsigned int. it is defined in the vcruntime.h file
    
    snprintf(tmp, sizeof(tmp),"%s",dir); // snprintf is a c function that prints a c-string into an array(unlike cout that prints unto the console). The parameters it takes are the 
	//the array to which it should print into, the size of that array which is given by sizeof(temp) and a c-style print ( given by the format specifier "%s" (which means a string) and the variable to be printed

    len = strlen(tmp); //len is asigned to the length of the character array created above

	//LOGIC
	if (tmp[len - 1] == '/')
	{
		tmp[len - 1] = 0; //subbing last character in temp with 0 if it's '/'. Not so sure why he wants to do so. He prolly wanted to fix a null character there or that's how file paths
		//are specified in linux? Confirm
	}
    for(p = tmp + 1; *p; p++)
      if(*p == '/') { // iterates through entire character array and chnages all foward slahes to 0. Linus direct path format stuff?
        *p = 0;
        //mkdir(tmp, mode); //depracated
		_mkdir(tmp,mode); 
        *p = '/';
      }
    //mkdir(tmp, mode); //depracated 
	_mkdir(tmp, mode); // the directory is created here
  }
  
  
//xtring gen_filename(xtring dir, xtring fname, int year, bool fmakedir) {
	  xtring gen_filename(xtring fname, int year, bool fmakedir) {

	  //xtring is a custom class created to handle the stream string. definition is in gutil.h
	  //this functions generates a filename. 

    // insert the run year into the file pathname: /scratch/.../rundir/imogen/2015/
    //param "file_temp"     (str "/scratch/anthoni-p/PLUM/crop_runs/couple_test/imogen/YYYY/T_anom.dat")
    
    // check if fname is absolute or relative, absolute starts with "/"
    //xtring pathbase = dir + xtring("/"); // pathbase is an xtring object. just like string pathbase. concatenation happening here. '/' appended to pathbase
	xtring pathbase;
	if (fname[0] == '/' || fname[0] == '\0') //fname is a formal parameter passed to this function
	{	
		//if fname is absolute(begins with a / or null character, then pathbase is equal to an empty string so that pathbase can be the relative base directory
		pathbase = xtring("");
	}
    
    //long position = fname.find("%Y"); // find returns -1 if it doesn't find what it's looking for
	long position = fname.find("Y");
    if (position != -1) {

		//if it doesn't return -1, fname is a year(int) so we gotta convert to string. We do that by making use of the to_string template created above
      xtring syear = to_xtring(year);
      
      if (fmakedir) {
        xtring pathname = pathbase + fname.left(position) + syear; //pathname is gotten here via concatenation
        _mkdir((char*) pathname, 0775);  //directory is crated
      }
      
      //fname = fname.left(position) + syear + fname.right(fname.len() - xtring("%Y").len() - position); //generates file name
	  fname = fname.left(position) + syear + fname.right(fname.len() - xtring("YYYY").len() - position); //generates file name
    }
    
    //return pathbase + fname; //base name of directory plus file path returned
	return fname;
  }

	template<typename T>
	void resize3DimVector(std::vector< std::vector< std::vector<T> > > & vec, size_t FirstDim, size_t SecDim, size_t ThirdDim)
	{
		vec.resize( FirstDim );
		for (size_t i = 0; i < FirstDim; ++i)
		{
			vec[i].resize( SecDim );
			for (size_t j = 0; j < SecDim; ++j)
				vec[i][j].resize( ThirdDim );
		}
	}
	
	template<typename T>
	void resize2DimVector(std::vector< std::vector<T> > & vec, size_t FirstDim, size_t SecDim)
	{
		vec.resize( FirstDim );
		for (size_t i = 0; i < FirstDim; ++i)
		{
			vec[i].resize( SecDim );
		}
	}
	
	/// Interpolates monthly data to quasi-daily values.


	//If imogen input is in months, you need to get them in days because LPJ takes them in days. There's an existing function to do the interpolation to generate the daily data out of the
	//monthly data
	//defined below
	void interp_climate(double* mtemp, double* mprec, double* msun, double* mdtr, double *mwet,
											double* dtemp, double* dprec, double* dsun, double* ddtr, long& seed) {
		interp_monthly_means_conserve(mtemp, dtemp);
		prdaily(mprec, dprec, mwet, seed);
		interp_monthly_means_conserve(msun, dsun, 0);
		interp_monthly_means_conserve(mdtr, ddtr, 0);
	}
	
	
}

//input model has to be registered so that framework.cpp will know about it and call it
REGISTER_INPUT_MODULE("imogen", ImogenInput) //syntax available in offial documentation

ImogenInput::ImogenInput() 
	: searchradius(0),
	ndep_timeseries("historic"),
    spinup_year_idx(0),
	firsthistyear(-1),
    lasthistyear(-1),
	monthly(true)
	//copying constructor
{

  offset_to_midpoint[0] = 0.0; //incase IMOGEN data have an offset to midpoint
  offset_to_midpoint[1] = 0.0;
  
	// Declare instruction file parameters
	declare_parameter("searchradius", &searchradius, 0, 100,
		"If specified, Imogen climate data will be searched for in a circle");
  
	declare_parameter("lon_offset_to_midpoint", &offset_to_midpoint[0], -10, 10,
		"If specified, longitude offset of Imogen climate to grid middle point.");
	declare_parameter("lat_offset_to_midpoint", &offset_to_midpoint[1], -10, 10,
		"If specified, latitude offset of Imogen climate to grid middle point.");
  
  declare_parameter("ndep_timeseries", &ndep_timeseries, 10, "Nitrogen deposition time series to use (historic, rcp26, rcp45, rcp60 or rcp85");

	declare_parameter("firsthistyear", &firsthistyear, 1871, 2300,	"the first year in the imogen climate [range 1871..2300]");
	declare_parameter("lasthistyear", &lasthistyear, 1871, 2300,	"the last year in the imogen climate [range 1871..2300]");
 
	declare_parameter("monthly_imogen", &monthly, "imogen produced monthly climate data (default=true)");


	//disabled since I am not using mPI
#ifdef HAVE_MPI
	int flag;
	if (MPI_Initialized(&flag)==MPI_SUCCESS && flag == true) {
		// running imogen input on more than one node requires mpi to be synced.
		MPI_Barrier(MPI_COMM_WORLD);
	}
#endif

}

//destuctor
ImogenInput::~ImogenInput() {
	  
#ifdef HAVE_MPI
	int flag;
	if (MPI_Initialized(&flag)==MPI_SUCCESS && flag == true) {
		// running imogen input on more than one node requires mpi to be synced.
		MPI_Barrier(MPI_COMM_WORLD);
	}
#endif

}


//intializing the model.Mandatory for all input models according to documentation. The init fucntion is already defined
void ImogenInput::init() {
  
//  file_cru = param["file_cru"].str;
  file_temp = param["file_temp"].str;

  file_prec = param["file_prec"].str;
  if (monthly)
		file_wetdays = param["file_wetdays"].str;
  file_insol = param["file_insol"].str;
  file_dtr = param["file_dtr"].str;

  spatial_resolution = parse_spatial_resolution();

  spinup_year_idx = 0;
  
  reread_file = true;

  searchradius = param["searchradius"].num;
	
	// Read list of grid coordinates and store in global Coord object 'gridlist'
	// This file should consist of any number of one-line records in the format:
	//   <longitude> <latitude> [<description>]
	double dlon,dlat;
	std::string descrip;

	// Retrieve name of grid list file as read from ins file
	xtring file_gridlist=param["file_gridlist"].str;

	std::string line;
	std::ifstream ifs(file_gridlist, std::ifstream::in);
	
	
	if (!ifs.good())
		fail("%s: could not open %s for input", __FUNCTION__, (char*)file_gridlist);
	
	gridlist.killall();
	first_call = true;
	while (!ifs.eof()) {
		std::getline(ifs, line);

		//reading grildlist, put all lons in a vector and all lats in vector and put -1 into coord line vector(as check)
		//if there's a description too, it puts that in c.descrip
		if (line.size()>0) {
			std::istringstream iss(line);
			iss >> dlon >> dlat;
			getline(iss, descrip);
			
			Coord& c=gridlist.createobj(); // add new coordinate to grid list

			c.lon=dlon;
			c.lat=dlat;
			c.descrip=xtring(descrip.c_str());
			
			//DKB: 08.08.22: do a longitudinal conversion here from imogen to LPJ so there's consistency in the rest of the code
			if (dlon > 180) {
				all_lon.push_back(dlon-360.0);
			}
			else {
				all_lon.push_back(dlon);
			}
			//all_lon.push_back(dlon);
			all_lat.push_back(dlat);
			coord_line.push_back(-1);
		}
	}
	
	
  // prepare storage for all the data, based on number gridpoints, number of years
  ngrid = gridlist.nobj;
	
  //DKB: Retrieve firsthistyear and lasthistyear from instruction file here
  firsthistyear = param["firsthistyear"].num;
  lasthistyear = param["lasthistyear"].num;

  //DKB: uncommented the code below as a safety check
  if ((firsthistyear < 0) || (lasthistyear < 0)) {
	  fail("imogen input requires firstimogenyear and lastimogenyear to be set");
  }


	// allways allow space from 1st spinup year
	nyears = (lasthistyear - FIRST_SPINUP_YEAR) + 1;

	stored_years.resize(nyears);

	last_store_index = 0;
	std::fill(stored_years.begin(), stored_years.end(), -1);
//  for (int store_index = 0; store_index < nyears; store_index++)
//    stored_years[store_index] = -1;
	
  
	//resizes all vector storage spaces to match nyears
	resize3DimVector(all_temp, nyears, ngrid, monthly?12:Date::MAX_YEAR_LENGTH);
  resize3DimVector(all_prec, nyears, ngrid, monthly?12:Date::MAX_YEAR_LENGTH);
	resize3DimVector(all_wetdays, nyears, ngrid, monthly?12:Date::MAX_YEAR_LENGTH);
	resize3DimVector(all_insol, nyears, ngrid, monthly?12:Date::MAX_YEAR_LENGTH);
  resize3DimVector(all_dtr, nyears, ngrid, monthly?12:Date::MAX_YEAR_LENGTH);

	all_co2.resize(nyears);
	
	// check the availability of climate data in a 1st spinup year climate file 
	//xtring filename = gen_filename(".", file_temp, FIRST_SPINUP_YEAR, false);
	xtring filename = gen_filename(file_temp, FIRST_SPINUP_YEAR, false);
	
	//checks for data in first spin up temp file
	lon_lat_lines_in_file(filename, all_lon, all_lat, coord_line);
	
	// this is allways this way: a) normal run with spinup, b) run with start from a state
	date.set_first_calendar_year(getfirsthistyear() - nyear_spinup);

	soilinput.init(param["file_soildata"].str);

}


bool ImogenInput::find_corresponding_gridlist (Gridcell gridcell) {
  
  bool found = false;
  
  gridlist.firstobj();
  while(gridlist.isobj) {
    Coord& c = gridlist.getobj();
    if (c.lon == gridcell.get_lon() && c.lat == gridcell.get_lat()) {
      found = true;
      break;
    }
    gridlist.nextobj();
  }
  
  return found;
}

//this method extracts data from a line, the lon, lat and data (yearly or monthly), pointer is passed so the space should have been allocated already
bool ImogenInput::extract_line_data(std::string line, double& dlon, double& dlat, double *data, bool monthly) {
	std::istringstream iss(line);
	iss >> dlon >> dlat;
	// convert imogen lon [0..180..356.25] to our lon [-180..0..176.25]
  // Note: imogen seems midpoint but centered at c(0.0,0.0)
	/*if (dlon > 180)
		dlon = dlon - 360.0;*/
	
	dlon += offset_to_midpoint[0];
	dlat += offset_to_midpoint[1];
	

	if (data) { // only if there was space set aside for the data
		if (monthly)
			for (int idx = 0; idx < (monthly?12:Date::MAX_YEAR_LENGTH); idx++) {
			iss >> data[idx];
		}
	}
	return true;
}

//this method extracts the just the lon and lat in a file and puts all lon in a vactor and all lats into another vector
bool ImogenInput::read_lon_lat_in_file(xtring fname, std::vector<double>& lons, std::vector<double>& lats) {
	std::string line;
	
	std::ifstream ifs(fname, std::ifstream::in);
	
	if (!ifs.good()) // good() returns true if file opens succesfully
		fail("%s: could not open %s for input", __FUNCTION__, (char*)fname);
	
	lons.clear(); // erases content of the vector
	lats.clear();
	while (!ifs.eof() && getline(ifs, line)) {
		//while there's still some more data to be read in the file

		double dlon, dlat;
		extract_line_data(line, dlon, dlat, NULL);

		lons.push_back(dlon);
		lats.push_back(dlat);
	}
	return true;
}

//bool ImogenInput::lon_lat_lines_in_file(xtring fname, std::vector<double> lons, std::vector<double> lats, std::vector<int>& lines) {
//	//pass lon and lat read from gridlist..lines usually is the vector that contains (-1) to track the stands kinda?
//
//	std::vector<double> file_lons; //to contain lon from file under consideration
//	std::vector<double> file_lats; //to contains lats from file under consideration
//	read_lon_lat_in_file(fname, file_lons, file_lats); //puts all lon and lats in file under consideration(name passed as xtring fname) into the respective vector(above)
//	if (file_lons.size()==0) //return false if file contains no data(if no lon was stored) - hand over control to calling method
//		return false;
//	
//	dprintf("ImogenInput: searching (with radius %g) the closest lon lat in climate files:\n", searchradius);
//	//searach logic starts here
//	for (int igrid=0; igrid < lons.size(); igrid++) {
//		lines[igrid]=0; //initially was -1. later used as a check. Remember was passed as reference so original value gets changed
//		int iline=0;
//		double last_dist=9999;
//		double dist;
//		dprintf("looking for (%g,%g)\n", lons[igrid], lats[igrid]);
//		while (iline < file_lons.size()) {
//			if (searchradius > 0.0) {
//				dist=sqrt((file_lons[iline] - lons[igrid])*(file_lons[iline] - lons[igrid]) + (file_lats[iline] - lats[igrid])*(file_lats[iline] - lats[igrid]));
//				if ((dist < last_dist)&&(dist < searchradius)) {
//					last_dist=dist;
//					lines[igrid]=iline+1;
//					//dprintf("  found (%g,%g) line %d dist %g\n", file_lons[iline], file_lats[iline], iline+1, dist);
//				}
//			} else { //
//				//debug print out grildlsit value and file values of lon and lat comparatively
//				//dprintf("gridlon: %f, gridlat: %f, filelon: %f, filelat: %f\n",lons[igrid], lats[igrid], file_lons[iline], file_lats[iline]);
//				//system("pause");
//
//				dist=sqrt((file_lons[iline] - lons[igrid])*(file_lons[iline] - lons[igrid])+(file_lats[iline] - lats[igrid])*(file_lats[iline] - lats[igrid]));
//
//
//				if (negligible(dist)) {
//					//HERE
//					lines[igrid]=iline+1;
//					dprintf("  found (%g,%g) line %d dist %g\n", file_lons[iline], file_lats[iline], iline+1, dist);
//
//					//DKB: 08.08.22: Added break statement to get out of the loop if the gridcell is found
//					break;
//				}
//			}
//			iline++;
//		}
//		if (lines[igrid]==0) {
//			dprintf("	no location found\n");
//
//    } else {
//      dprintf("  found (%g,%g) line %d dist %g\n", file_lons[lines[igrid]-1], file_lats[lines[igrid]-1], lines[igrid], last_dist);
//		}
//	}
//
//	return true;
//}


bool ImogenInput::lon_lat_lines_in_file(xtring fname, std::vector<double> lons, std::vector<double> lats, std::vector<int>& lines) {
	std::vector<double> file_lons;
	std::vector<double> file_lats;
	read_lon_lat_in_file(fname, file_lons, file_lats);

	//std::cout << "=== File Lon/Lat Values from " << fname << " ===\n";
	//for (size_t i = 0; i < file_lons.size(); ++i) {
	//	std::cout << "  file_lons[" << i << "] = " << file_lons[i]
	//		<< ", file_lats[" << i << "] = " << file_lats[i] << "\n";
	//}

	if (file_lons.empty()) {
		std::cout << "File is empty. No longitude values found.\n";
		return false;
	}

	std::cout << "ImogenInput: searching (with radius " << searchradius << ") the closest lon-lat in climate file: " << fname << "\n";

	for (int igrid = 0; igrid < lons.size(); igrid++) {
		lines[igrid] = 0;
		int iline = 0;
		double last_dist = 9999;
		double dist;

		std::cout << "===> Looking for grid point (" << lons[igrid] << ", " << lats[igrid] << ") [index " << igrid << "]\n";

		while (iline < file_lons.size()) {
			//check for IMOGEN native lon conv added
			dist = std::sqrt(((file_lons[iline] > 180 ? file_lons[iline] - 360 : file_lons[iline]) - lons[igrid]) * (file_lons[iline] - lons[igrid]) +
				(file_lats[iline] - lats[igrid]) * (file_lats[iline] - lats[igrid]));

			/*std::cout << "  Comparing to file point (" << file_lons[iline] << ", "
				<< file_lats[iline] << ") at line " << iline + 1
				<< ": dist = " << dist << "\n";*/

			if (searchradius > 0.0) {
				if ((dist < last_dist) && (dist < searchradius)) {
					last_dist = dist;
					lines[igrid] = iline + 1;
				}
			}
			else {
				if (negligible(dist)) {
					lines[igrid] = iline + 1;
					std::cout << "  Exact match found at line " << iline + 1 << "\n";
					break;
				}
			}
			iline++;
		}

		if (lines[igrid] == 0) {
			std::cout << "  --> No matching location found for grid point ("
				<< lons[igrid] << ", " << lats[igrid] << ")\n";
			//system("pause");
		}
		else {
			std::cout << "  --> Closest match for (" << lons[igrid] << ", "
				<< lats[igrid] << ") is ("
				<< file_lons[lines[igrid] - 1] << ", "
				<< file_lats[lines[igrid] - 1] << ") at line "
				<< lines[igrid] << " with dist " << last_dist << "\n";
			//system("pause");
		}
	}

	return true;
}

bool ImogenInput::read_lines_from_file(xtring fname, std::vector<double> lons, std::vector<double> lats, std::vector<int> lines, std::vector<std::vector<double> >& data, bool monthly) {
	std::string line;
	
	std::ifstream ifs(fname, std::ifstream::in);
	
	if (!ifs.good())
		fail("%s: could not open %s for input", __FUNCTION__, (char*)fname);
	
	int nlines=0;
	while (!ifs.eof() && getline(ifs, line)) {
		nlines++;
		// check if we need to extract the data of that line for one or more grid point(s) in the CPUs gridlist
		// (if all lines would have same length, one could seek to the positions in the file)
		// we need to check all the lines and extract the data into the corresponding igrid position within data
		for (int igrid=0;igrid < lines.size(); igrid++) {
			if (lines[igrid] == nlines) { // Note: lines and nlines are not zero based, it is 1..n
				double dlon, dlat;
				double temp_data[Date::MAX_YEAR_LENGTH];  // also enough for monthly
				extract_line_data(line, dlon, dlat, temp_data, monthly);
				for (int i=0; i < (monthly?12:Date::MAX_YEAR_LENGTH); i++) {
					data[igrid][i] = temp_data[i];
				}
			}
		}
	}
	return true;
}

int ImogenInput::readenv(std::vector<double> lons, std::vector<double> lats, int calendar_year, int store_index, std::vector<int> line_index) {
	// Extracts the climate data out of the imogen data files for (temperature, precipitation, shortwave radiation)
	// for the grid cells whose coordinates are given by lons and lats and line location is given by line_index
	// and stores only the data for those grid points at the store index in the class data stores
	
  // The temperature, precipitation and radiation files should be in FORTRAN ASCII text
  // format and contain one-line records for each coord.
  
  // The following is a sample record from the temperature file:
  //   " 281.250  82.500   236.450   236.450   ... 237.630   237.630   237.630"
  // corresponds to the following data:
  //   longitude 281.25 deg (0=greenwich, longitude goes from 0..360 )
  //   latitude 82.5 deg (+=N, latitude goes from -90 to 90)
  //   daily temperatures (K) 236.45 (1st-Jan), ..., 237.63 (31st-Dec)
  //
  // Precipitation is in (mm/day)  (convert for LPJ to kg m-2 s-1)  1m (m3/m2) * 1000 kg/m3 * 86400s/1day
  // Shortwave radiation is in (W/m^2)
	
	int ngrid_found = 0;
  bool readfile = false;
	//xtring filename = gen_filename(".", file_temp, calendar_year, false);
	xtring filename = gen_filename(file_temp, calendar_year, false);
	//std::cout << "File name is: " << filename << std::endl;
  if (verbose>1) dprintf("%s: file_temp %s\n", __FUNCTION__, (char *) filename);
	readfile = read_lines_from_file(filename, lons, lats, line_index, all_temp[store_index], monthly);
	if (readfile) {
		//filename = gen_filename(".", file_prec, calendar_year, false);
		filename = gen_filename(file_prec, calendar_year, false);
		//std::cout << "File name is: " << filename << std::endl;
		readfile = read_lines_from_file(filename, lons, lats, line_index, all_prec[store_index], monthly);
		//filename = gen_filename(".",file_insol, calendar_year, false);
		filename = gen_filename(file_insol, calendar_year, false);
		//std::cout << "File name is: " << filename << std::endl;
		readfile = read_lines_from_file(filename, lons, lats, line_index, all_insol[store_index], monthly);
		if (monthly) {
			//filename = gen_filename(".", file_wetdays, calendar_year, false);
			filename = gen_filename(file_wetdays, calendar_year, false);
			readfile = read_lines_from_file(filename, lons, lats, line_index, all_wetdays[store_index], monthly);
		}
		if (ifbvoc) {
			//filename = gen_filename(".",file_dtr, calendar_year, false);
			filename = gen_filename(file_dtr, calendar_year, false);
			readfile = read_lines_from_file(filename, lons, lats, line_index, all_dtr[store_index], monthly);
		}
		// already in init() determined, which grids have imogen climate coordinates lines
		for (int i=0; i < coord_line.size(); i++) {
			if (coord_line[i]>0)
				ngrid_found++;
		}
	}
	return ngrid_found;
}


void ImogenInput::get_climate_for_gridcell(int store_index, int igrid, long& seed) {
	
	if (monthly) {
		if (firemodel == BLAZE) {
			fail("%s: sorry, imogen input not setup for firemodel BLAZE, needs extra climate data and GWGEN",__FUNCTION__);
		}
		// Interpolate monthly spinup data to quasi-daily values
		double mtmp[12];
		double mprec[12];
		double minsol[12];
		double mdtr[12];
		double mwet[12];
		for (int i=0; i<12; i++) {
			mtmp[i] = all_temp[store_index][igrid][i];
			mprec[i] = all_prec[store_index][igrid][i] * 30; // imogen gives the average daily within a 30-day month, we need summed over month to distribute
			mwet[i] = all_wetdays[store_index][igrid][i];
			minsol[i] = all_insol[store_index][igrid][i];
			mdtr[i] = ifbvoc?all_dtr[store_index][igrid][i]:0.0;
		}
		interp_climate(mtmp,mprec,minsol,mdtr,mwet,dtemp,dprec,dinsol,ddtr,seed);

	} else {
		for (int i = 0; i < Date::MAX_YEAR_LENGTH; i++) {
			dtemp[i] = all_temp[store_index][igrid][i];
			dprec[i] = all_prec[store_index][igrid][i]; // * 86400 / 1000; // convert to precip rate in kg/m2/s
			dinsol[i] = all_insol[store_index][igrid][i];
			if (ifbvoc) ddtr[i] = all_dtr[store_index][igrid][i];
		}
	}
	
}

double ImogenInput::parse_spatial_resolution() {
  return (3.75/2); // 3.75x2.5 deg
  // https://en.wikipedia.org/wiki/HadCM3 resolution: 3.75 × 2.5 degrees in longitude × latitude. This gives 96 × 73 grid points???
}

bool ImogenInput::getgridcell(Gridcell& gridcell) {
  
	// Make sure we use the first gridcell in the first call to this function,
	// and then step through the gridlist in subsequent calls.
	if (first_call) {
		gridlist.firstobj();

		// Note that first_call is static, so this assignment is remembered
		// across function calls.
		first_call = false;

    current_grid_index = -1;
    // this requires that all yearly LU, Nfert, etc. are concat into one file !!!
    // Open landcover files
    landcover_input.init();
    // Open management files
    management_input.init();
    
	}
	else gridlist.nextobj();
  
  // are we done yet.
	if (!gridlist.isobj)
    return false;
	
	Coord coord;
	bool gridfound = false;
  while (!gridfound) {
		
		current_grid_index++;
		
    bool LUerror = false;
		
		coord.lon = gridlist.getobj().lon;
		coord.lat = gridlist.getobj().lat;
		
		dprintf("\nCommencing simulation for gridcell at (%g,%g)\n", coord.lon, coord.lat);
		// already checked in init() if there are climate data and set gridfound!
		gridfound = (coord_line[current_grid_index]>0);
		
    if (run_landcover && gridfound) {
      LUerror = landcover_input.loadlandcover(coord.lon, coord.lat);
      if(!LUerror)
        LUerror = management_input.loadmanagement(coord.lon, coord.lat);
      if(LUerror)
        dprintf("\nError: could not find stand at (%g,%g) in landcover/management data file(s)\n", coord.lon, coord.lat);
      if (LUerror)
        gridfound = false;
    }
    
    if(!gridfound) {
      dprintf("\nError: could not find stand at (%g,%g) in input data files\n", coord.lon, coord.lat);
      gridlist.nextobj();
			if (!gridlist.isobj)
				return false;
    }
    
  }

	// Tell framework the coordinates of this grid cell
	gridcell.set_coordinates(coord.lon, coord.lat);
	
	//FIXME: Is imogen shortwave daytotal (SWRAD_TS) or daylight total (SWRAD)?
	gridcell.climate.instype = SWRAD_TS;

	double cru_lon = coord.lon;
	double cru_lat = coord.lat;

	//DKB 09.08.22: Extract ndep time_series here
	ndep_timeseries = param["ndep_timeseries"].str;
	//DKB 09.08.22: Extract ndep time_series here


	// Get nitrogen deposition, using the found CRU coordinates
	//ndep.getndep(param["file_ndep"].str, cru_lon, cru_lat,Lamarque::parse_timeseries(ndep_timeseries));
	
	soilinput.get_soil(cru_lon, cru_lat, gridcell);
	
//  // Setup the soil type
//  soilparameters(gridcell.soiltype, soilcode);
  
  //dprintf("Using soil code and Nitrogen deposition for (%3.1f,%3.1f)\n", lon, lat);
  
  // new gridcell ensure, we start at index one for spinup
  spinup_year_idx = 0;
  
  xtring stime;
  unixtime(stime);
  dprintf("%s %s: starting simulation for (%f,%f)\n",__FUNCTION__, (char*) stime, gridcell.get_lon(), gridcell.get_lat());
  
  return true;
}

bool ImogenInput::getclimate(Gridcell& gridcell) {
  
  Climate& climate = gridcell.climate;
  
  int calendar_year = date.get_calendar_year();
  int firsthistyear = getfirsthistyear();
  
  bool found = true;
  if (gridlist.isobj) {
    // input selected the right gridlist for us. Hopefully!!!!
    double lon = gridlist.getobj().lon;
    double lat = gridlist.getobj().lat;
    if (fabs(lon - gridcell.get_lon()) > 0.1 || fabs(lat - gridcell.get_lat()) > 0.1) {
      dprintf("%s: gridcell not found in gridlist", __FUNCTION__);
      found = false;
    }
  }
  if (!found) {
    found = find_corresponding_gridlist (gridcell);
    if (!found) {
      dprintf("%s: gridcell not found in gridlist", __FUNCTION__);
      return false;
    }
  }
  
  Coord coord;
  coord.lon = gridcell.get_lon();
  coord.lat = gridcell.get_lat();
  
  bool spinup = (calendar_year < getfirsthistyear());
  int imogen_year = calendar_year;
  if (spinup) {
    imogen_year = FIRST_SPINUP_YEAR + spinup_year_idx;
  }
  
  if (date.day == 0) {
    
 		if (calendar_year > lasthistyear) {// Return false if last year was the last for the simulation
      xtring stime;
      unixtime(stime);
      dprintf("%s %s: end simulation for (%f,%f)\n",__FUNCTION__, (char*) stime, gridcell.get_lon(), gridcell.get_lat());
      return false;
		}
    
    if (spinup) {
      if (verbose>1 && spinup_year_idx==0) {
          xtring stime;
          unixtime(stime);
          dprintf("%s %s: (re-)starting spinup in year %d with climate of year %d\n",__FUNCTION__, (char*) stime, calendar_year, imogen_year);
      }
      spinup_year_idx++;
      if (spinup_year_idx >= NYEAR_SPINUP)
        spinup_year_idx = 0;
    }
		
    int store_index = -1;
    reread_file = true;
    for (int index = 0; index < nyears; index++) {
      if (stored_years[index] == imogen_year) {
        reread_file = false;
        store_index = index;
        break;
      }
    }
    if (store_index<0) {
      store_index = last_store_index++;
			if (verbose) {
				xtring stime;
				unixtime(stime);
				dprintf("%s %s: storing year %d into index %d\n",__FUNCTION__, (char*) stime, imogen_year, store_index);
			}
    }
    
    if (reread_file) {
      // read all the data for the all_lon and all_lat
      int nfound = readenv(all_lon, all_lat, imogen_year, store_index, coord_line);
      if (nfound == 0) {
        fail("%s: failed reading imogen climate for all grid points!\n",__FUNCTION__);
        return false;
      }
      if (date.year == 0)
        dprintf("%s: read %d of %d gridpoint(s) out of imogen climate!\n",__FUNCTION__, nfound, all_lon.size());
			
			// Read CO2 data from file
			//xtring filename = gen_filename(".", param["file_co2"].str, imogen_year, false);
			xtring filename = gen_filename(param["file_co2"].str, imogen_year, false);
			co2.load_file(filename);
			
			all_co2[store_index] = co2[imogen_year];
			/* if (!spinup) */
			if (verbose) dprintf("%s: file_co2 %s CO2 = %g ppm\n",__FUNCTION__, (char *) filename, co2[imogen_year]);
			if(co2[imogen_year] < 200) {
				dprintf("%s: co2 %f < 200ppm in year %d, day %d\n",__FUNCTION__,co2[imogen_year],date.get_calendar_year(), date.day);
			}
			
      stored_years[store_index] = imogen_year;  // there might be some grid point(s) that failed.
    }
    
    if (coord_line[current_grid_index] < 0) { // we did not find a grid point
        dprintf("%s: failed reading imogen climate for (%f,%f)!\n",__FUNCTION__, gridcell.get_lon(), gridcell.get_lat());
        return false;
    }
    get_climate_for_gridcell(store_index, current_grid_index, gridcell.seed);
    
    // Get monthly ndep values and convert to daily
	double mNHxdrydep[12], mNOydrydep[12];
	double mNHxwetdep[12], mNOywetdep[12];

	ndep.get_one_calendar_year(date.get_calendar_year(),
	                           mNHxdrydep, mNOydrydep,
							   mNHxwetdep, mNOywetdep);

	// Distribute N deposition
	distribute_ndep(mNHxdrydep, mNOydrydep,
					mNHxwetdep, mNOywetdep,
					dprec,dNH4dep,dNO3dep);
    
	climate.co2 = all_co2[store_index];
    if(climate.co2 < 200) {
      dprintf("%s: co2 %f < 200ppm in year %d, day %d\n",__FUNCTION__,climate.co2,date.get_calendar_year(), date.day);
    }

  }
  
  climate.temp = dtemp[date.day] - 273.15; // needed in degC
  climate.prec = dprec[date.day];
  climate.insol = dinsol[date.day];

  // bvoc
  if(ifbvoc){
    climate.dtr = ddtr[date.day];
  }
  
  // Nitrogen deposition
	gridcell.dNH4dep = dNH4dep[date.day];
	gridcell.dNO3dep = dNO3dep[date.day];
	
	// First day of year only ...	
	if (date.day == 0) {
		
		// Progress report to user and update timer
		
		if (tmute.getprogress()>=1.0) {
			
			int historic_years = max(lasthistyear - firsthistyear + 1,0);
			
			int years_to_simulate = nyear_spinup + historic_years;
			
			int cells_done = current_grid_index;
			
			double progress=(double)(cells_done*years_to_simulate+date.year)/(double)(ngrid*years_to_simulate);
			tprogress.setprogress(progress);
			dprintf("(y%d) %3d%% complete , %s elapsed, %s remaining\n", date.get_calendar_year(),
							(int)(progress*100.0),
							tprogress.elapsed.str,tprogress.remaining.str);
			tmute.settimer(MUTESEC);
		}
	}
	
  return true;
}

bool ImogenInput::getsoil(Gridcell& gridcell, const int soilmap_index){
  return true;
}

void ImogenInput::getlandcover(Gridcell& gridcell) {

	landcover_input.getlandcover(gridcell);
	landcover_input.get_land_transitions(gridcell);
}


int ImogenInput::getfirsthistyear() {
	int first_year = ImogenInput::FIRST_HIST_YEAR;
	if (firsthistyear < ImogenInput::FIRST_HIST_YEAR)
		first_year = firsthistyear;
	
  return first_year;
}

int ImogenInput::getnyear_hist() {

  if (nyears > 0) {
    return nyears;
  }
  return NYEAR_RUN;
}

void ImogenInput::reset(){}

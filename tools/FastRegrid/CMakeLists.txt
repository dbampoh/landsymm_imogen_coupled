cmake_minimum_required(VERSION 3.10)
project(FastRegrid VERSION 1.0 LANGUAGES CXX)

# [Block 8.2.5 (2026-05-26): Linux-adapted from version_B/.../FastRegrid/
#  CMakeLists.txt: (a) all target_link_libraries() use the keyword signature
#  (PRIVATE) so cmake doesn't error on plain/keyword mix; (b) lowercase
#  filenames per Linux case-sensitivity. - DKB block 8.2.5]

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Define the library
add_library(fastregrid SHARED regrid.cpp)
target_include_directories(fastregrid PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Example executable (the CLI binary; named fastregrid_example for historical
# consistency with version_B; effectively the production fastregrid binary
# used at block 8.2.5 Phase E for δ-B + δ-B-variant 62892-grid regridding)
add_executable(fastregrid_example fastregrid.cpp)
target_link_libraries(fastregrid_example PRIVATE fastregrid)

# Enable OpenMP for parallelization
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    target_link_libraries(fastregrid PRIVATE OpenMP::OpenMP_CXX)
    target_link_libraries(fastregrid_example PRIVATE OpenMP::OpenMP_CXX)
endif()

# Install library and headers
install(TARGETS fastregrid DESTINATION lib)
install(FILES regrid.h DESTINATION include/fastregrid)
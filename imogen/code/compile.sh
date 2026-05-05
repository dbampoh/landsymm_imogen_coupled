#!/bin/bash
# Stand-alone compile script for Fortran IMOGEN (alternative to Makefile).
# Produces: imogen_lpjg
# (Linux convention; the predecessor's .exe suffix was a Windows artefact.)
set -e
gfortran -c -ffixed-line-length-132 -O imogen_lpjg.f nonco2.f
gfortran -o imogen_lpjg imogen_lpjg.o nonco2.o
echo "Build complete: ./imogen_lpjg"

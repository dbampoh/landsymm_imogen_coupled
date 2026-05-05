#make file to control the compilation process: DKB 08-06-2022
FC=gfortran
SRC=imogen_lpjg.f nonco2.f
OBJ = ${SRC:.f=.o}

%.o: %.f
	${FC} -o $@ -c -ffixed-line-length-132 -O $<

imogen_lpjg:${OBJ}
	${FC} -o $@ ${OBJ}

clean:
	rm -f *.o
	rm -f imogen_lpjg imogen_lpjg.exe imogen

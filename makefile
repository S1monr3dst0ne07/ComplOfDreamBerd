

run:
	python3 src/main.py prg/test.db
	fasm build.asm build.o
	ld build.o runtime/build.o -o main

clean:
	-rm build.asm build.o main

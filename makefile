

TARGET=prg/hello.db

run: build
	./main

build: runtime
	python3 src/main.py prg/hello.db
	fasm build.asm build.o
	ld build.o runtime/build.o -o main \
		-z noexecstack

runtime:
	make -C runtime/

clean:
	-rm build.asm build.o main

.PHONY: clean build run runtime

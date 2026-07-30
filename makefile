

TARGET=prg/arith.db

run: build
	./main

build: runtime compile asm

compile:
	python3 src/main.py $(TARGET)

asm:
	fasm build.asm build.o
	ld build.o runtime/build.o -o main \
		-z noexecstack

runtime:
	make -C runtime/

clean:
	-rm build.asm build.o main

.PHONY: clean build run runtime asm compile

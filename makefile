

TARGET=prg/cool.db

run: build
	./main

decode: runtime_decode compile asm
	./main | python3 decode.py

build: runtime compile asm

compile:
	python3 src/main.py $(TARGET)

asm:
	fasm build.asm build.o
	ld build.o runtime/build.o -o main \
		-z noexecstack

runtime:
	make -B -C runtime/

runtime_decode:
	make -B decode -C runtime/

clean:
	-rm build.asm build.o main

.PHONY: clean build run runtime asm compile

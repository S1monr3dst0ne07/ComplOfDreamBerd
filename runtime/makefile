


build.o: src/*.c
	gcc -g -c src/all.c -o $@ -Isrc/ \
		-Wno-builtin-declaration-mismatch \
		-Wno-free-nonheap-object \
		-O0

clean:
	-rm build.o

.PHONY: build




build.o: src/*.c
	gcc -g -c src/all.c -o $@ -Isrc/ \
		-Wno-builtin-declaration-mismatch \
		-Wno-free-nonheap-object \
		-O0

decode:
	gcc -g -c src/all.c -o build.o -Isrc/ \
		-Wno-builtin-declaration-mismatch \
		-Wno-free-nonheap-object \
		-O0 \
		-DHEAP_DECODE


clean:
	-rm build.o

.PHONY: build

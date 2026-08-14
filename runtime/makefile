


build.o: src/*.c
	gcc -g -c src/all.c -o $@ -Isrc/ \
		-ffreestanding \
		-O0

decode:
	gcc -g -c src/all.c -o build.o -Isrc/ \
		-ffreestanding \
		-O0 \
		-DHEAP_DECODE


clean:
	-rm build.o

.PHONY: build

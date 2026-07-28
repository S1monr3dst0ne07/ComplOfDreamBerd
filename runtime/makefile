


build.o: src/*.c
	gcc -g -c $< -o $@ -Isrc/ \
		-Wno-builtin-declaration-mismatch \
		-Wno-free-nonheap-object

clean:
	-rm build.o

.PHONY: build

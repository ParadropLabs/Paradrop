all:
	mkdir -p build
	gcc src/main.c -o build/hello-world

install:
	install -t ../deployment/chute/ build/hello-world

clean:
	rm -rf build
	rm -rf ../deployment/chute/*

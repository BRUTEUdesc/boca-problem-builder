#include "testlib.h"
#include <string>

using namespace std;

int main(int argc, char *argv[]) {
    registerTestlibCmd(argc, argv);

    int n = ouf.readInt(1, 9, "n");

    quitf(_ok, "%d lines", n);
}

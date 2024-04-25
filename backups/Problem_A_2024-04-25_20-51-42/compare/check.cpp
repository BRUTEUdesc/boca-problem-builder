#include "testlib.h"
#include <string>

using namespace std;

int main(int argc, char *argv[]) {
    registerTestlibCmd(argc, argv);

    using ll = long long;
    const int mx = 1e9;

    int N = inf.readInt(1, 30000, "N");
    vector<int> inp;
    for (int i = 0; i < N; i++) {
        int x = inf.readInt(1, mx, "x");
        inp.push_back(x);
    }

    vector<int> p1, p2;

    for (int i = 0; i < N; i++) {
        int x = ouf.readInt(1, N, "x");
        p1.push_back(inp[x - 1]);
    }
    for (int i = 0; i < N; i++) {
        int x = ans.readInt(1, N, "x");
        p2.push_back(inp[x - 1]);
    }

    if (p1 != p2) {
        quitf(_wa, "Different answers");
    }

    quitf(_ok, "OK");

    return 0;
}


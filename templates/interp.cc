
#include <interpolate/Interpolate.h>


#include <iostream>

using std::cerr;
using std::endl;
using std::cout;

using vector::Vector;


int main(int argc, char* argv[])
{
    if (argc != 6) {
        cerr << "Usage: " << argv[0] << " x1 y1 x2 y2 t" << endl;
        return 1;
    }

    vector::Vector p1(strtod(argv[1], nullptr), strtod(argv[2], nullptr));
    vector::Vector p2(strtod(argv[3], nullptr), strtod(argv[4], nullptr));
    double t = strtod(argv[5], nullptr);
    vector::Vector result = interpolate::interpolate(p1, p2, t);
    cout << "Interpolated point: (" << result.x << ", " << result.y << ")" << endl;
    return 0;
}

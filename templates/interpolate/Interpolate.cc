
#include "Interpolate.h"

using vector::Vector;

namespace interpolate
{
    Vector interpolate(const Vector& p1, const Vector& p2, double t)
    {
        return p1 + (p2 - p1) * t;
    }
}

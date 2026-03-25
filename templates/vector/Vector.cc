
#include "Vector.h"

namespace vector {

Vector Vector::operator+(const Vector& other) const {
    return Vector(x + other.x, y + other.y);
}

Vector Vector::operator*(double scalar) const {
    return Vector(x * scalar, y * scalar);
}

Vector& Vector::operator+=(const Vector& other) {
    x += other.x;
    y += other.y;
    return *this;
}

Vector& Vector::operator*=(double scalar) {
    x *= scalar;
    y *= scalar;
    return *this;
}

Vector Vector::operator-(const Vector& other) const {
    return Vector(x - other.x, y - other.y);
}

} // namespace vector

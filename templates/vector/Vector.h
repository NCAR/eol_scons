
namespace vector {

    struct Vector {
        double x{0.0};
        double y{0.0};

        Vector() = default;
        Vector(double x, double y) : x(x), y(y) {}

        Vector operator+(const Vector& other) const;
        Vector operator*(double scalar) const;
        Vector& operator+=(const Vector& other);
        Vector& operator*=(double scalar);
        Vector operator-(const Vector& other) const;
    };

}

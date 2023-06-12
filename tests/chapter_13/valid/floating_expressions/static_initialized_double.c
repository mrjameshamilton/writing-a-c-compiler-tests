// Test reading and writing a local static double

// Return old value, then increment by one
double return_static_variable(void) {
    static double d = 0.5;
    double ret = d;
    d = d + 1.0;
    return ret;
}

int main(void) {
    double d1 = return_static_variable();
    double d2 = return_static_variable();
    double d3 = return_static_variable();
    return (d1 == 0.5 && d2 == 1.5 && d3 == 2.5);
}
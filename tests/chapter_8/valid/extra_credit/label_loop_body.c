int main(void) {
    int result = 0;
    goto label;
    while (0)
    label: { result = 1; }

    return result;
}
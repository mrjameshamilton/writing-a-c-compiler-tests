int main()
{
    int x = 4; // initialization is a dead store
    int *ptr = &x;
    return ptr == 0;
}
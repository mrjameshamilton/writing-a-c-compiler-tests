/* movl x, y does not cause interference b/t x and y
 * look for: no spills - exactly five callee-saved regs conflict at any time */

int glob0 = 0;
int glob1 = 1;
int glob2 = 2;
int glob3 = 3;
int glob4 = 4;
int glob5 = 5;

// use this to force pseudoregs to be callee-saved
int reset_globals()
{
    glob0 = 0;
    glob1 = 0;
    glob2 = 0;
    glob3 = 0;
    glob4 = 0;
    glob5 = 0;
    return 0;
}

int use_value(int v)
{
    glob0 = glob0 + v;
    return 0;
}

int client(int flag)
{
    /* define some values - must be in calle-saved regs */
    int a = glob0;
    int b = glob1;
    int c = glob2;
    int d = glob3;
    int e = glob4;
    int f;
    int g;
    int h;
    int i;
    int j;
    // put this in conditional so copy prop doesn't get rid of these copies
    if (flag)
    {
        reset_globals();
        f = a; // now f interferes w/ b, c, d, and e but not a
        use_value(a);
        g = b; // now g interferes w/ c, d, e, f but not a, b
        use_value(b);
        h = c; // h interferes with d, e, f, g, h but not a, b or c
        use_value(c);
        i = d; // i interferes with e, f, g, h but not a, b, c, or d
        use_value(d);
        j = e; // j interferes with f, g, h, i but not a, b, c,d, e
        use_value(e);
    }
    else
    {
        e = 0;
        f = 0;
        g = 0;
        h = 0;
    }
    if (e != 0)
        return 0;
    if (f != -1)
        return 0;
    if (g != -2)
        return 0;
    if (h != -3)
        return 0;
    if (glob0 != 6)
        return 0;
    return 1;
}

int main()
{
    return client(1);
}
int i = 0;

int putchar(int i);
void foo(void) { i = 90; }

int main(void) {
  // print the alphabet
  for (foo(); i >= 65; i = i - 1)
    putchar(i);
  return 0;
}
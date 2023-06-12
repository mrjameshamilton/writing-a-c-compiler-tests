int target(void) {
  char i = 200;
  signed char j = i;
  // w/ constant folding, should be able to reduce this to 1
  // this tests that we can propagate chars to replace sigend chars and vice
  // versa they're effectively the same type
  return i == j;
}

int main(void) { return target(); }
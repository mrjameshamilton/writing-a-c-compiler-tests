int count_down() {
  static int i = 10;
  i = i - 1;
  return i;
}

int sum = 0;

int callee() { return 5; }

int use(int i) { return sum = sum + i; }

int target() {
  int y = 10; // gen y = 10
  int x = y;  // gen x = y
  while (count_down()) {
    x = callee(); // kill x = y
    use(x);
    x = y; // gen x = y
  }

  return x; // should become "return 10"
}

int main() {
  int result = target();
  return result == 10 && sum == 45;
}
struct s {
  int a;
};

int main(void) {
  struct s x = {1};
  struct s y = {2};
  return x == y;
}
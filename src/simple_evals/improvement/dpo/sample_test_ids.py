import polars as pl
from dot_slash import dot_slash

random_seed = 2476
all_test_ids = pl.read_csv(dot_slash("test_ids.csv"))
N = 100
sampled = all_test_ids.sample(n=N, seed=random_seed)
sampled.write_csv(dot_slash("sampled_test_ids_100.csv"), include_header=False)

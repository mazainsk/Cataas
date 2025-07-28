from tqdm import tqdm
from time import sleep, time

items = [0, 10, 50, 70, 100]

pbar = tqdm(total=20, unit_scale=False)

for i in range(200):
    sleep(0.1)
    pbar.update(0.1)

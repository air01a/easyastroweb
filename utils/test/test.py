from pysiril.wrapper import Wrapper
from pysiril.siril import *
from pathlib import Path
import time

app = Siril()
siril = Wrapper(app)
app.Open()

siril.cd("C:\\Users\\eniquet\\Documents\\dev\\easyastroweb\\utils\\test")
siril.start_ls(rotate=True)
fits_dir = Path("C:\\Users\\eniquet\\Documents\\dev\\easyastroweb\\utils\\test\\target")
fits_files =  list(fits_dir.glob("*.fits"))
fits_files.sort()

for i in fits_files:
    print(f"livestack {i}")
    print("=============================",siril.livestack(f"{i}"))
print("____________________________________________________________________________")
siril.stop_ls()
siril.close()
app.Close()


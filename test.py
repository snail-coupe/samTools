from samTools.samDisk import DSK, SamDos, MasterDos
import samTools.samBasic
from pathlib import Path

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dsk", type=Path, default=(Path.cwd() / "untitled.mgt.gz"))
parser.add_argument("--file", type=int, default=4)
                    
args = parser.parse_args()

## print("opening")
sddsk = SamDos(DSK(args.dsk))
mddsk = MasterDos(DSK(args.dsk))

#print("%s:"%sddsk.diskName)
#sddsk.ls()
# mddsk.ls()
# mddsk.cd(3)
# print("%s%s"%(mddsk.diskName,mddsk.pwd()))
# mddsk.ls()

# for f in iter(sddsk):
#    if  f.fileTypeStr == "BASIC":
#        print(f)
# print("extracting file #2")
f = sddsk.extractFile(args.file)

# print("Converting SamBASIC to text")
print(samTools.samBasic.basicToAscii(f[1],sddsk.directory[args.file]))
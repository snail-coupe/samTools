from samTools.samDisk import DSK, SamDos, MasterDos
import samTools.samBasic

## print("opening")
# dsk = SamDos(DSK("Example.zip"))
dsk = MasterDos(DSK("untitled.mgt"))
## print("listing")
dsk.ls(1)
## print("extracting file #2")
# f = dsk.extractFile(2)
## print("Converting SamBASIC to text")
# samTools.samBasic.basicToAscii(f[1])
from samTools.samDisk import DSK, SamDos, MasterDos
import samTools.samBasic

## print("opening")
sddsk = SamDos(DSK("untitled.mgt.gz"))
mddsk = MasterDos(DSK("untitled.mgt.gz"))

#print("%s:"%sddsk.diskName)
#sddsk.ls()
mddsk.cd(3)
print("%s%s"%(mddsk.diskName,mddsk.pwd()))
mddsk.ls()

#for f in iter(dsk):
#    if  f.fileTypeStr == "BASIC":
#        print(f)
## print("extracting file #2")
#f = dsk.extractFile(2)
## print("Converting SamBASIC to text")
#print(samTools.samBasic.basicToAscii(f[1]))
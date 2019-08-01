# class for doing stuff with DSK files
import zipfile
import struct

class DiskImage():
  def __init__(self, sides: int, tracksPerSide: int, sectorsPerTrack: int):
    self.sides = sides
    self.tracks = tracksPerSide
    self.sectors = sectorsPerTrack
    self.sectorMap = {}
    for side in range(0,sides):
      self.sectorMap[side] = {}
      for track in range(0,self.tracks):
        self.sectorMap[side][track] = {}
        for sector in range(0,self.sectors):
          self.sectorMap[side][track][sector] = bytes(512)

  def write(self, side: int, track:int , sector:int , data: bytes):
    self.sectorMap[side][track][sector] = data

  def read(self, side: int, track: int, sector: int) -> bytes:
    #print("%d:%d:%d"%(side,track,sector))
    return self.sectorMap[side][track][sector]

class SamDos():
  pass 

  class dirEnt():
    fileTypes = {
      5: ("ZX Snapshot file","SNP 48k"),
      16: ("SAM BASIC program","BASIC"),
      17: ("Numeric array","D ARRAY"),
      18: ("String array","$ ARRAY"),
      19: ("Code file","CODE"),
      20: ("Screen file","SCREEN$")
    }

    def __init__(self, data: bytes):
      if len(data)!=256:
        raise ValueError("Wrong sized record")
      self.raw = data
      self.deleted = (data[0] == 0)
      self.hidden = data[0]>0x80
      self.protected = data[0]&0x40
      self.fileType = data[0]&0x3f
      self.filename = data[1:11] #.decode()
      (self.sectors, self.track, self.sector)=struct.unpack_from(">HBB",data,11)
      self.sectorAddressMap = data[15:210]
      (pages, remain) = struct.unpack_from("<BH",data,239)
      self.totalBytes = 16384*pages + remain

    def __str__(self):
      return("%10s %8d %s"%(self.filename.decode(), self.totalBytes, self.lookupType(self.fileType)))

    def lookupType(self, code):
      if code in self.fileTypes:
        return self.fileTypes[code][1]
      return "???"
  
  def __init__(self, disk: DiskImage):
    self.diskImage = disk
    self.directory = {}
    for fileNum in range(0,80):
      trackOs = int(fileNum/20)
      sectorOs = 1 + int((fileNum%20)/2)
      data = self.diskImage.read(0,trackOs,sectorOs)
      if(fileNum&1):
        data = data[256:]
      else:
        data = data[:256]
      self.directory[fileNum+1] = self.dirEnt(data)

  def ls(self):
    for entry in self.directory.keys():
      if self.directory[entry].fileType:
        print("%2d %s"%(entry, self.directory[entry]))

  def extractFile(self, fileNum):
    fileInfo = self.directory[fileNum]
    if(fileInfo.deleted):
      raise FileNotFoundError()
    track = fileInfo.track
    sector = fileInfo.sector
    data = bytes()
    while track or sector:
      side = track&0x80
      dd = self.diskImage.read(side, track&0x7f, sector)
      data += dd[:510]
      track = dd[510]
      sector = dd[511]
    if len(data)<(9+fileInfo.totalBytes):
      raise EOFError("Read %d expected %d"%(len(data),fileInfo.totalBytes))
    fileHdr = data[:9]
    data = data[9:]
    return fileHdr,data[:fileInfo.totalBytes]


class DSK(DiskImage):
  pass
  
  def __init__(self, filename):
    self.filename = filename
    super().__init__(2,80,10)
    if zipfile.is_zipfile(filename):
      with zipfile.ZipFile(filename, 'r') as zf:
        data = zf.read(zf.infolist()[0])
    else:
      with open(filename, 'rb') as ff:
        data = ff.read()
    print("Len: %d bytes"%len(data))
    for track in range(0,80):
      for side in range(0,2):
        for sector in range(1,11):
          super().write(side, track, sector, data[:512])
          data = data[512:]
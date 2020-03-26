# class for doing stuff with DSK files
import zipfile
import gzip
import struct
import typing

class DiskImage():
  ''' Basic disk image in memory '''

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

class Dos():
  class dirEnt():
    fileTypes = {
      5: ("ZX Snapshot file","SNP 48k"),
      16: ("SAM BASIC program","BASIC"),
      17: ("Numeric array","D ARRAY"),
      18: ("String array","$ ARRAY"),
      19: ("Code file","CODE"),
      20: ("Screen file","SCREEN$")
    }

    def __init__(self, fileNum: int, data: bytes):
      if len(data)!=256:
        raise ValueError("Wrong sized record")
      self.raw = data
      self.fileNum = fileNum
      self.deleted = (data[0] == 0)
      self.hidden = data[0]>0x80
      self.protected = data[0]&0x40
      self.fileType = data[0]&0x3f
      self.fileTypeStr = self.lookupType(self.fileType)
      self.filename = data[1:11] #.decode()
      (self.sectors, self.track, self.sector)=struct.unpack_from(">HBB",data,11)
      self.sectorAddressMap = data[15:210]
      (pages, remain) = struct.unpack_from("<BH",data,239)
      self.totalBytes = 16384*pages + remain

    def __str__(self):
      return("%3d: %10s %8d %s"%(self.fileNum, self.filename.decode(), self.totalBytes, self.lookupType(self.fileType)))

    def lookupType(self, code):
      if code in self.fileTypes:
        return self.fileTypes[code][1]
      return "???"

  DE = typing.TypeVar('DE', bound=dirEnt)

class SamDos(Dos):
  ''' tools for reading files from a SamDOS file system '''

  def __init__(self, disk: DiskImage):
    self.diskImage = disk
    self.directory = {}
    self.diskName = "SAM DOS"
    for fileNum in range(0,80):
      trackOs = int(fileNum/20)
      sectorOs = 1 + int((fileNum%20)/2)
      data = self.diskImage.read(0,trackOs,sectorOs)
      if(fileNum&1):
        data = data[256:]
      else:
        data = data[:256]
      self.directory[fileNum+1] = self.dirEnt(fileNum+1,data)

  def ls(self):
    for entry in iter(self):
      print(entry)

  def extractFile(self, fileNum: int) -> bytes:
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

  def __iter__(self):
    self.ptr = 0
    return self

  def __next__(self) -> Dos.DE:
    while True:
      self.ptr+=1
      if self.ptr not in self.directory.keys():
        raise StopIteration
      if self.directory[self.ptr].fileType:
        return self.directory[self.ptr]    
      
class MasterDos(SamDos):
  ''' overload SamDOS class with MasterDOS extensions '''

  class dirEnt(SamDos.dirEnt):
    # clone fileTypes so don't modify base case
    fileTypes = SamDos.dirEnt.fileTypes.copy()

    def __init__(self, fileNum: int, data: bytes):
      # extend fileTypes before calling super init
      self.fileTypes[21] = ("Sub Directory","DIR")
      # Generic stuff
      super().__init__(fileNum, data)
      # MasterDOS specific
      self.isDir = (self.fileType == 21)
      self.inDir = data[254]
      self.dirTag = data[250]

    def __str__(self):
      return("%3d %10s %8d %s"%(self.fileNum, self.filename.decode(), self.totalBytes, self.lookupType(self.fileType)))

  def __init__(self, disk: DiskImage):
    # Start of disk looks like SamDOS
    super().__init__(disk)
    # set working directory
    self.curDir = 0

    # MasterDOS Specific
    firstSector = self.diskImage.read(0,0,0)
    extraDirTracks = firstSector[255]
    if firstSector[210]:
      self.diskName = firstSector[210:220].decode().strip()
    else:
      self.diskName = "MASTER DOS"

    if extraDirTracks:
      extraEnts = 20*extraDirTracks - 2
      for fileNum in range(80,80+extraEnts):
        trackOs = int((2+fileNum)/20)
        sectorOs = 1 + int(((2+fileNum)%20)/2)
        data = self.diskImage.read(0,trackOs,sectorOs)
        if(fileNum&1):
          data = data[256:]
        else:
          data = data[:256]
        self.directory[fileNum+1] = self.dirEnt(fileNum+1,data)

  def __next__(self) -> Dos.DE:
    while True:
      # use SamDos iterator but filter on working directory
      ret = super().__next__()
      if ret.inDir == self.directory[self.curDir].dirTag:
        return ret

  def pwd(self, subDir: int=None):
    if subDir == None:
      subDir = self.curDir
    if subDir == 0:
      return ":"
    de = self.directory[subDir]
    return self.pwd(de.inDir) + "\\" + de.filename.decode().strip()

  def cd(self, subDir: int = None):
    if subDir == None: 
      subDir = self.curDir
    if self.directory[subDir].isDir:
      self.curDir = subDir
    else:
      raise TypeError("Not a Directory")

  def parentDir(self, subDir: int = None):
    if subDir == None:
      subDir = self.curDir
    if subDir == 0:
      return 0
    return self.directory[subDir].inDir

class DSK(DiskImage):
  ''' Specialised DiskImage - imports from standard DSK file '''
  
  def __init__(self, filename):
    self.filename = filename
    self.zip = False
    super().__init__(2,80,10)
    if zipfile.is_zipfile(filename):
      self.zip = True
      with zipfile.ZipFile(filename, 'r') as zf:
        data = zf.read(zf.infolist()[0])
    else:
      try:
        with gzip.open(filename) as ff:
          data = ff.read()
      except gzip.BadGzipFile:
        with open(filename, 'rb') as ff:
          data = ff.read()
    for track in range(0,80):
      for side in range(0,2):
        for sector in range(1,11):
          super().write(side, track, sector, data[:512])
          data = data[512:]

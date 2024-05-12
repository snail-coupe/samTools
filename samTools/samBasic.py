import struct
import string 
from typing import Union, List
from .samDisk import Dos
import math
import pprint

class FPCError(Exception):
  ''' error in Floating Point Calculator '''

class BasicEncodingError(Exception):
  ''' Error in BASIC encoding '''

def hexDump(data: bytes, prefix: str='') -> str:
  ret = ""
  printables = range(32,128)
  while(data):
    ret += prefix
    chars = []
    row = data[:16]
    data = data[16:]
    for b in row:
      ret += "%2.2x "%b
      if b in printables:
        chars.append(chr(b))
      else:
        chars.append('.')
    for _ in range(len(row), 16):
      ret += "   "
    ret += "    "
    ret += "".join(chars)
    ret += f"\n" 
  return ret
    
commands = {
  144: "DIR",     183: "REM",       222: "ON",
  145: "FORMAT",  184: "READ",      223: "GET",
  146: "ERASE",   185: "DATA",      224: "OUT",
  147: "MOVE",    186: "RESTORE",   225: "POKE",
  148: "SAVE",    187: "PRINT",     226: "DPOKE",
  149: "LOAD",    188: "LPRINT",    227: "RENAME",
  150: "MERGE",   189: "LIST",      228: "CALL",
  151: "VERIFY",  190: "LLIST",     229: "ROLL",
  152: "OPEN",    191: "DUMP",      230: "SCROLL",
  153: "CLOSE",   192: "FOR",       231: "SCREEN",
  154: "CIRCLE",  193: "NEXT",      232: "DISPLAY",
  155: "PLOT",    194: "PAUSE",     233: "BOOT",
  156: "LET",     195: "DRAW",      234: "LABEL",
  157: "BLITZ",   196: "DEFAULT",   235: "FILL",
  158: "BORDER",  197: "DIM",       236: "WINDOW",
  159: "CLS",     198: "INPUT",     237: "AUTO",
  160: "PALETTE", 199: "RANDOMIZE", 238: "POP",
  161: "PEN",     200: "DEF FN",      239: "RECORD",
  162: "PAPER",   201: "DEF KEYCODE", 240: "DEVICE",
  163: "FLASH",   202: "DEF PROC",    241: "PROTECT",
  164: "BRIGHT",  203: "END PROC",    242: "HIDE",
  165: "INVERSE", 204: "RENUM",       243: "ZAP",
  166: "OVER",    205: "DELETE",      244: "POW",
  167: "FATPIX",  206: "REF",         245: "BOOM",
  168: "CSIZE",   207: "COPY",        246: "ZOOM",
  169: "BLOCKS",  208: "Reserved",    247: "Reserved",
  170: "MODE",    209: "KEYIN",       248: "Reserved",
  171: "GRAB",    210: "LOCAL",       249: "Reserved",
  172: "PUT",     211: "LOOP IF",     250: "Reserved",
  173: "BEEP",    212: "DO",          251: "Reserved",
  174: "SOUND",   213: "LOOP",        252: "Reserved",
  175: "NEW",     214: "EXIT IF",     253: "Reserved",
  176: "RUN",     215: "IF",          254: "Reserved",    # 215 Long IF
  177: "STOP",    216: "IF",          255: "Not usable",  # 216 Short IF
  178: "CONTINUE",  217:  "ELSE",                         # 217 Long ELSE
  179: "CLEAR",     218: "ELSE",                          # 218 Short ELSE
  180: "GO TO",     219: "END IF",
  181: "GO SUB",    220: "KEY",
  182: "RETURN",    221: "ON ERROR",    
}

# short IF -> IF test THEN cmd: ELSE cmd:
# long IF -> IF test: cmd: cmd: ELSE IF test2: cmd: cmd: [ ELSE: cmd : ]END IF

qualifiers = {
  133: "USING", 137: "OFF",   141: "THEN",
  134: "WRITE", 138: "WHILE", 142: "TO",
  135: "AT",    139: "UNTIL", 143: "STEP",
  136: "TAB",   140: "LINE",    
}

functions = {
  59: "PI",84: "COS", 109: "VAL$", 
  60: "RND",85: "TAN",110: "VAL",
  61: "POINT",86: "ASN", 111: "TRUNC$",
  62: "FREE",87: "ACS", 112: "CHR$",
  63: "LENGTH",88: "ATN",113: "STRS",
  64: "ITEM",89: "LN", 114: "BIN$",
  65: "ATTR",90: "EXP", 115: "HEX$", 
  66: "FN",91: "ABS", 116: "USR$", 
  67: "BIN",92: "SGN",117: "Reserved",
  68: "XMOUSE",93: "SQR",118: "NOT",
  69: "YHOUSE",94: "INT",119: "Reserved",
  70: "XPEN",95: "USR",120: "Reserved",
  71: "YPEN",96: "IN",121: "Reserved",
  72: "RAMTOP",97: "PEEK",122: "MOD",
  73: "Reserved",98: "LPEEK",123: "DIV",
  74: "INSTR",99: "DVAR",124: "BOR", 
  75: "INKEY$", 100: "SVAR",125: "Reserved", 
  76: "SCREEN$", 101: "BUTTON",126: "BAND", 
  77: "MEM$", 102: "EOF",127: "OR",
  78: "Reserved",103: "PTR",128: "AND", 
  79: "PATH$", 104: "Reserved", 129: "<>",
  80: "STRING$", 105: "UDG", 130: "<=", 
  81: "Reserved",106: "Reserved", 131: ">=", 
  82: "Reserved",107: "LEN",132: "Reserved",
  83: "SIN",108: "CODE",    
}

def expandLine(data: bytes) -> str:
  l = ""
  while(len(data)>1):
    if data[0]==0xff:
      if data[1] in functions:
        l+=functions[data[1]]+" "
      else:
        l += "<function %d>"%data[1]
      data = data[1:]
    elif data[0] >= 0x90:
      if data[0] in commands:
        l+=commands[data[0]]+" "
      else:
        l += "<command %d>"%data[0]
    elif data[0] >= 0x85:
      if data[0] in qualifiers:
        l+=" %s "%qualifiers[data[0]]
      else:
        l += "<qualifier %d>"%data[0]
    elif data[0] == 0x0e:
      # 0x fd fd pg ll hh appears to be an undocumented special
      # case for the address of the DEF PROC
      l += f"<<{hexDump(data[1:6])}>>"
      l += f"<inline {fpc(data[1:6])}>" 
      data = data[5:]
    elif data[0]<0x20:
      l += "<%d>"%data[0]
    else:
      l += chr(data[0])
    data = data[1:]
  if not data or data[0] != 0x0d:
    l += "<BAD EOL>"
  return l

def fpc(value: bytes) -> Union[int, float]:
  if len(value) != 5:
    raise FPCError(f"fpc input should be 5 bytes not {len(value)}")
  
  if value[0] == 0:  # int
    sgn = value[1]
    val = struct.unpack("<H", value[2:4])[0]
    zero = value[4]
    if zero != 0:
      raise FPCError("Invlid Int (non-zero terminated)")
    if not sgn:
      return val
    elif sgn == 0xff:
      return -(65536-val)
    else:
      raise FPCError(f"Invalid Int (bad sign 0x{sgn})")
  
  # float
  e, sm = struct.unpack(">BI", value)
  e = e-0x80
  sgn = sm & 0x80000000
  m = sm | 0x80000000 
  val = 2**e * (m / 2**32)
  if sgn:
    val = -val
  return val

def unpackSvarNumberArray(data: bytes, dimlengths: List[int]):
  if len(dimlengths)==1:
    return [fpc(data[5*x:5*(x+1)]) for x in range(0,dimlengths[0])]
  elif dimlengths.count==0:
    raise BasicEncodingError("Can't have zero dimensioned array")
  chunksize = math.prod(dimlengths[1:], start=5)
  return [
    unpackSvarNumberArray(data[x*chunksize:(x+1)*chunksize], dimlengths[1:])
    for x in range(0, dimlengths[0])
  ]

def unpackSvarStringArray(data: bytes, dimlengths: List[int]):
  if len(dimlengths)==2:
    slen = dimlengths[1]
    return [data[x*slen:(1+x)*slen].decode() for x in range(0,dimlengths[0])]
  elif dimlengths.count==0:
    raise BasicEncodingError("Can't have zero dimensioned array")
  chunksize = math.prod(dimlengths[1:-1], start=dimlengths[-1])
  return [
    unpackSvarStringArray(data[x*chunksize:(x+1)*chunksize], dimlengths[1:])
    for x in range(0, dimlengths[0])
  ]

def processSvarBlock(data: bytes) -> str:
  ret = "SVAR Block (Strings and Arrays)\n"
  while data:
    hidden = data[0]&0x80
    arraytype = data[0]&0x60
    namelen = data[0]&0x1f
    name = data[1:1+namelen].decode()
    data=data[11:]
    if not arraytype:
      (pages, remain) = struct.unpack_from("<BH",data,0)
      string_len = pages*16384 + remain
      ret += f"  {name}$ [{string_len} bytes]\n{hexDump(data[3:string_len+3],'  | ')}"
      data = data[3+string_len:]
    else:
      (pages, remain) = struct.unpack_from("<BH",data,0)
      array_len = pages*16384 + remain
      adata = data[3:array_len+3]
      data = data[3+array_len:]
      dimensions = adata[0]
      dimlengths = []
      adata = adata[1:]
      for _ in range(dimensions):
        dimlengths.append(struct.unpack("<H",adata[:2])[0])
        adata = adata[2:]
      if arraytype&0x40:
        retarray = unpackSvarStringArray(adata, dimlengths)
        ret += f"  {name}$({', '.join([str(x) for x in dimlengths])}) [{array_len} bytes]\n"
      else:
        retarray = unpackSvarNumberArray(adata, dimlengths)
        ret += f"  {name}({', '.join([str(x) for x in dimlengths])}) [{array_len} bytes]\n"
      ret += ''.join([f"  | {x}" for x in pprint.pformat(retarray).splitlines(True)])
      ret += "\n"
  ret += hexDump(data)
  return ret

def processNvarBlock(data: bytes) -> str:
  ret = "NVAR Block (Ints and Floats)\n"
  invalid = bytes([0xff,0xff])
  offsets = [
    (chr(0x61 + x), 2*x + 1 + struct.unpack_from("<H", data, 2*x)[0])
    for x in range(26)
    if data[2*x:2*(x+1)] != invalid
  ]
  for firstchar, offset in offsets:
    while offset < len(data):
      nextoffset = struct.unpack_from("<H", data, offset+1)[0]
      namelen = data[offset]&0x1f
      name = firstchar + data[offset+3:offset+3+namelen].decode()
      try:
        if data[offset]&0x40: # for next
          value = fpc(data[offset+3+namelen:offset+3+namelen+5])
          limit = fpc(data[offset+8+namelen:offset+8+namelen+5])
          step = fpc(data[offset+13+namelen:offset+13+namelen+5])
          (pages, remain) = struct.unpack_from("<BH",data,offset+18+namelen)
          loopaddr = pages*16384 + remain
          loopstatment = data[offset+21+namelen]
          ret = ret + f"  {name}: {value} (Limit: {limit}, Step:{step}, Addr:{loopaddr}, Stmnt:{loopstatment})\n"
        else:
          ret = ret + f"  {name}: {fpc(data[offset+3+namelen:offset+3+namelen+5])}\n"
      except FPCError as exc:
        print(f"error parsing {name} {exc}")
      offset = offset + nextoffset + 2
      if nextoffset == invalid:
        break

  return ret

def basicToAscii(data: bytes, dirent: Dos.dirEnt) -> str:
  offsets: Dos.dirEnt.dirEntBasicInfo = dirent.getExtendedInfo()
  ret = ""
  offset = 0
  while offset < len(data):
    if data[offset] == 0xff:
      ret += "[%07d]   EOF End of Listing\n"%(dirent.startAddress+offset)
      break
    if offset+4 > len(data):
      raise BasicEncodingError("Program Listing does not end on 0xff")
    
    lineNum=struct.unpack_from(">H",data,offset)[0]
    lineLen=struct.unpack_from("<H",data,offset+2)[0]
    offset += 4
    line = data[offset:offset+lineLen]
    try:
      print(hexDump(line,"                 "))
      print("[%07d] %5d %s\n"%(dirent.startAddress+offset-4, lineNum, expandLine(line)))
      ret += "[%07d] %5d %s\n"%(dirent.startAddress+offset-4, lineNum, expandLine(line))
    except (BasicEncodingError, FPCError) as exc:
      ret += "[%07d] %5d %s\n"%(dirent.startAddress+offset-4, lineNum, f"ERROR: {exc}")
    offset += lineLen

  nvarblock = data[offsets.nvarStart:offsets.nvarEnd]
  ret += "[%07d]  NVAR %d bytes\n"%(offsets.nvarStart+dirent.startAddress, len(nvarblock))

  padding = data[offsets.nvarEnd:offsets.svarStart]
  ret += "[%07d]       %d bytes of padding\n"%(offsets.nvarEnd+dirent.startAddress, len(padding))
  
  svarblock = data[offsets.svarStart:]
  ret += "[%07d]  SVAR %d bytes\n"%(offsets.svarStart+dirent.startAddress, len(svarblock))
  
  ret += "\n"
  ret += processNvarBlock(nvarblock)
  ret += "\n"
  ret += processSvarBlock(svarblock)

  return ret
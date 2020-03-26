import struct

def hexDump(data: bytes) -> str:
  ret = ""
  while(data):
    row = data[:16]
    data = data[16:]
    for b in row:
      ret += "%2.2x "%b
    ret += "\n"
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
      data = data[5:]
    elif data[0]<0x20:
      l += "<%d>"%data[0]
    else:
      l += chr(data[0])
    data = data[1:]
  if data[0] != 0x0d:
    l += "<BAD EOL>"
  return l

def processDataBlock(data: bytes) -> str:
  ret = "[ %d long data section ]\n"%len(data)
  return ret + hexDump(data)

def basicToAscii(data: bytes) -> str:
  ret = ""
  while len(data)>4:
    if data[0] == 0xff:
      ret += processDataBlock(data[1:])
      data = b''
    else:
      lineNum=struct.unpack_from(">H",data,0)[0]
      lineLen=struct.unpack_from("<H",data,2)[0]
      data=data[4:]
      line = data[:lineLen]
      data = data[lineLen:]
      ret += "%5d: %s\n"%(lineNum, expandLine(line))
  return ret
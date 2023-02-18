import binascii
import struct
import json

def get_packet_size(packet, st):
    packet_size = list(struct.unpack('<L', binascii.unhexlify(packet[st+16:st+24])))[0]
    return packet_size

def get_packet_starts(packets):
    i = 0
    lst = []
    while i < len(packets):
        size = get_packet_size(packets,i)
        lst.append(i)
        i = i + size*8
    return lst

def convert_key(bytes):
    key = list(struct.unpack('<l', binascii.unhexlify(bytes)))[0] #key Field Name
    return str(struct.pack('<l', key))[2:6]

def convert_pos_typ(bytes):
    pos = list(struct.unpack('<l', binascii.unhexlify(bytes[0:6]+b'00')))[0]
    typ = list(struct.unpack('B', binascii.unhexlify(bytes[6:8])))[0]
    return pos,typ

def convert_val(bytes):
    val = list(struct.unpack('<l', binascii.unhexlify(bytes)))[0]
    return val

def convert_lvls(bytes,rlvl):
    n_lvls = len(bytes)
    n_lvls = int(n_lvls*0.5)
    lvl_lst=[]
    blvls = list(struct.unpack(f'{n_lvls}B', binascii.unhexlify(bytes)))
    for blvl in blvls:
        lvl = blvl/2 - 127.5 + rlvl
        lvl_lst.append(lvl)
    return lvl_lst

def get_header(header):
    i = 0
    while i < len(header):
        pack_type = binascii.unhexlify(header[8:16])
        pack_size = list(struct.unpack('<l', binascii.unhexlify(header[16:24])))[0]
        pack_id = list(struct.unpack('<l', binascii.unhexlify(header[24:32])))[0]
        pack_form = list(struct.unpack('<l', binascii.unhexlify(header[32:40])))[0]
        pack_time = list(struct.unpack('<l', binascii.unhexlify(header[40:48])))[0]
        pack_nano = list(struct.unpack('<l', binascii.unhexlify(header[48:56])))[0]
        source_id = list(struct.unpack('<L', binascii.unhexlify(header[56:64])))[0]
        return source_id

def get_fields(packet):
    i = 88
    key_lst = []
    pos_lst = []
    val_lst = []
    title_lst = []
    value_lst = []
    source_id = get_header(packet[0:64])
    source_title = "source_id"
    title_lst.append(source_title)
    value_lst.append(source_id)
    while i < len(packet):
        
        if (packet[i:i+8] == b'00000000'):
            break
        key = convert_key(packet[i:i+8])
        pos, typ = convert_pos_typ(packet[i+8:i+16])
        if key == 'PDAT':
            lvl_lst = []
            rlev_n = key_lst.index('RLEV')
            rlev = val_lst[rlev_n]
            key_lst.append(key)
            pos_lst.append(pos)
            lvl_lst = convert_lvls(packet[i+16:i+pos*8],rlev)
            val_lst.append('lvl_lst')
            title_lst.append('lvls')
            value_lst.append(lvl_lst)
            i = i + pos*8
            continue
        if key == 'NANO':
            #val = datetime.fromtimestamp(list(struct.unpack('<L', binascii.unhexlify(packet[40:48])))[0])
            utim_n = key_lst.index('UTIM')
            val = convert_val(packet[i+16:i+24])
            utim = val_lst[utim_n] + val/1000000000
            key_lst.append(key)
            pos_lst.append(pos)
            val_lst.append('utim')
            title_lst.append('timestamp')
            value_lst.append(utim)
            i = i + pos*8
            continue
        if key == 'FSPM':
            fstp_n = key_lst.index('FSTP')
            val = convert_val(packet[i+16:i+24])
            fstp = val_lst[fstp_n] + val/1000000000
            key_lst.append(key)
            pos_lst.append(pos)
            val_lst.append('fstp')
            title_lst.append('stop_frq')
            value_lst.append(fstp)
            i = i + pos*8
            continue
        if key == 'FSAM':
            fsta_n = key_lst.index('FSTA')
            val = convert_val(packet[i+16:i+24])
            fsta = val_lst[fsta_n] + val/1000000000
            key_lst.append(key)
            pos_lst.append(pos)
            val_lst.append('fsta')
            title_lst.append('start_frq')
            value_lst.append(fsta)
            i = i + pos*8
            continue
        val = convert_val(packet[i+16:i+24])
        key_lst.append(key)
        pos_lst.append(pos)
        val_lst.append(val)
        i = i + pos*8
    return dict(zip(title_lst, value_lst))

def ncp_to_json(ncp_bytes):
    starts = get_packet_starts(ncp_bytes)
    i=1
    fields_lst = []
    for start in starts:
        if i > len(starts)-1:
            break
        n_packet = ncp_bytes[starts[i-1]:starts[i]]
        field = get_fields(n_packet)
        fields_lst.append(field)
        i = i + 1
    return json.dumps(fields_lst)
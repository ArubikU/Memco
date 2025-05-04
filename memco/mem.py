import zlib
import struct
from typing import List, Dict, Any, Optional

# Helper functions
def encode_str(s: Optional[str]) -> bytes:
    if s is None:
        return struct.pack('<I', 0xFFFFFFFF)
    data = s.encode('utf-8')
    return struct.pack('<I', len(data)) + data

def decode_str(data: bytes, offset: int):
    (length,) = struct.unpack_from('<I', data, offset)
    offset += 4
    if length == 0xFFFFFFFF:
        return None, offset
    s = data[offset:offset+length].decode('utf-8')
    return s, offset + length
def encode_embedding(embedding: Optional[List[float]]) -> bytes:
    if embedding is None:
        return struct.pack('<I', 0xFFFFFFFF)
    out = struct.pack('<I', len(embedding))
    for f in embedding:
        out += struct.pack('<f', f)
    return out

def decode_embedding(data: bytes, offset: int):
    (length,) = struct.unpack_from('<I', data, offset)
    offset += 4
    if length == 0xFFFFFFFF:
        return None, offset
    embedding = []
    for _ in range(length):
        (val,) = struct.unpack_from('<f', data, offset)
        offset += 4
        embedding.append(val)
    return embedding, offset

def encode_list_str(lst: Optional[List[str]]) -> bytes:
    if lst is None:
        return struct.pack('<I', 0xFFFFFFFF)
    out = struct.pack('<I', len(lst))
    for item in lst:
        out += encode_str(item)
    return out

def decode_list_str(data: bytes, offset: int):
    (length,) = struct.unpack_from('<I', data, offset)
    offset += 4
    if length == 0xFFFFFFFF:
        return None, offset
    lst = []
    for _ in range(length):
        s, offset = decode_str(data, offset)
        lst.append(s)
    return lst, offset

def encode_dict(d: Optional[Dict[str, Any]]) -> bytes:
    if d is None:
        return struct.pack('<I', 0xFFFFFFFF)
    out = struct.pack('<I', len(d))
    for k, v in d.items():
        out += encode_str(k)
        out += encode_str(str(v))  # Convert values to string
    return out

def decode_dict(data: bytes, offset: int):
    (length,) = struct.unpack_from('<I', data, offset)
    offset += 4
    if length == 0xFFFFFFFF:
        return None, offset
    d = {}
    for _ in range(length):
        k, offset = decode_str(data, offset)
        v, offset = decode_str(data, offset)
        d[k] = v
    return d, offset

def serialize_mem(mem: dict) -> bytes:
    parts = [
        encode_str(mem['id']),
        encode_str(mem['content']),
        encode_list_str(mem.get('tags')),
        encode_dict(mem.get('metadata')),
        struct.pack('<f', mem.get('importance', 0.0)),
        struct.pack('<d', mem.get('created_at', 0.0) or 0.0),
        struct.pack('<d', mem.get('updated_at', 0.0) or 0.0),
        encode_str(mem.get('source')),
        encode_embedding(mem.get('embedding')),
        struct.pack('<?', mem.get('encrypted', False)),
    ]
    raw_data = b''.join(parts)
    compressed = zlib.compress(raw_data)
    return struct.pack('<I', len(compressed)) + compressed

def deserialize_mem(data: bytes, offset: int = 0):
    (compressed_len,) = struct.unpack_from('<I', data, offset)
    offset += 4
    compressed_data = data[offset:offset + compressed_len]
    offset += compressed_len
    raw = zlib.decompress(compressed_data)

    idx = 0
    id_, idx = decode_str(raw, idx)
    content, idx = decode_str(raw, idx)
    tags, idx = decode_list_str(raw, idx)
    metadata, idx = decode_dict(raw, idx)
    (importance,) = struct.unpack_from('<f', raw, idx)
    idx += 4
    (created_at,) = struct.unpack_from('<d', raw, idx)
    idx += 8
    (updated_at,) = struct.unpack_from('<d', raw, idx)
    idx += 8
    source, idx = decode_str(raw, idx)
    embedding, idx = decode_embedding(raw, idx)
    (encrypted,) = struct.unpack_from('<?', raw, idx)

    return {
        'id': id_,
        'content': content,
        'tags': tags,
        'metadata': metadata,
        'importance': importance,
        'created_at': created_at,
        'updated_at': updated_at,
        'source': source,
        'embedding': embedding,
        'encrypted': encrypted
    }, offset

# File functions
def save_mems_to_file(filename: str, mems: List[dict]):
    with open(filename, 'wb') as f:
        for mem in mems:
            f.write(serialize_mem(mem))

def load_mems_from_file(filename: str) -> List[dict]:
    mems = []
    with open(filename, 'rb') as f:
        data = f.read()
        offset = 0
        while offset < len(data):
            mem, offset = deserialize_mem(data, offset)
            mems.append(mem)
    return mems

def save_mem_to_file(filename: str, mem: dict):
    with open(filename,
                'wb') as f:
            f.write(serialize_mem(mem))
def load_mem_from_file(filename: str) -> dict:
    with open(filename, 'rb') as f:
        data = f.read()
        mem, _ = deserialize_mem(data)
        return mem
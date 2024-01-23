from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HashBlock(_message.Message):
    __slots__ = ("hash", "prev_hash", "data_hash")
    HASH_FIELD_NUMBER: _ClassVar[int]
    PREV_HASH_FIELD_NUMBER: _ClassVar[int]
    DATA_HASH_FIELD_NUMBER: _ClassVar[int]
    hash: str
    prev_hash: str
    data_hash: str
    def __init__(self, hash: _Optional[str] = ..., prev_hash: _Optional[str] = ..., data_hash: _Optional[str] = ...) -> None: ...

class HashBlocksRequest(_message.Message):
    __slots__ = ("hash",)
    HASH_FIELD_NUMBER: _ClassVar[int]
    hash: str
    def __init__(self, hash: _Optional[str] = ...) -> None: ...

class Block(_message.Message):
    __slots__ = ("header", "transactions")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    TRANSACTIONS_FIELD_NUMBER: _ClassVar[int]
    header: str
    transactions: str
    def __init__(self, header: _Optional[str] = ..., transactions: _Optional[str] = ...) -> None: ...

class BlocksRequest(_message.Message):
    __slots__ = ("string_block",)
    STRING_BLOCK_FIELD_NUMBER: _ClassVar[int]
    string_block: str
    def __init__(self, string_block: _Optional[str] = ...) -> None: ...

class BlockRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class BlockResponse(_message.Message):
    __slots__ = ("block",)
    BLOCK_FIELD_NUMBER: _ClassVar[int]
    block: Block
    def __init__(self, block: _Optional[_Union[Block, _Mapping]] = ...) -> None: ...

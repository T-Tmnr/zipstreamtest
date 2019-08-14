import struct
from datetime import datetime
import binascii
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod

from dosdatetime import to_dos_datetime


NEED_MINIMUM_VERSION = 10
MY_ZIP_VERSION = 63


class ZipTarget(ABC):
    """Zip対象の抽象クラス。
    """
    @abstractmethod
    def entry_path(self) -> str:
        """Zipエントリー上のパスを返す
        パス区切りは '/' 推奨
        :return:
        """
        return None

    @abstractmethod
    def create_datetime(self) -> datetime:
        """ Zipエントリー上のファイル作成日
        :return:
        """
        return None

    @abstractmethod
    def open(self):
        """対象を開く処理
        対象の処理開始時に呼び出される。
        :return:
        """
        return

    @abstractmethod
    def close(self):
        """対象を閉じる処理
        対象の処理完了後に呼び出される。
        :return:
        """
        return

    @abstractmethod
    def read(self, size) -> bytes:
        """対象の内容を指定サイズ分返す
        コンテンツの終了時には falsy な値を返す
        :param size: 読込サイズ(byte)
        :return:
        """
        return None


class LocalFileTarget(ZipTarget):
    def __init__(self, path):
        self.file_path = path
        self.target_file = Path(path)
        self.file = None

    def entry_path(self):
        return self.file_path.replace('\\', '/')

    def create_datetime(self):
        return datetime.fromtimestamp(self.target_file.stat().st_ctime)

    def open(self):
        self.file = self.target_file.open("rb")

    def close(self):
        self.file.close()

    def read(self, size):
        return self.file.read(size)


def create_local_header(file_name: str,
                        file_date: datetime,
                        crc32: int = 0,
                        size: int = 0) -> bytes:
    """Local Header を生成する。
    圧縮無しのエントリーとして生成する。

    local file header signature     4 bytes  (0x04034b50)
    version needed to extract       2 bytes
    general purpose bit flag        2 bytes
    compression method              2 bytes
    last mod file time              2 bytes
    last mod file date              2 bytes
    crc-32                          4 bytes
    compressed size                 4 bytes
    uncompressed size               4 bytes
    file name length                2 bytes
    extra field length              2 bytes

    file name (variable size)
    extra field (variable size)

    :param file_name: ファイル名
    :param file_date: 作成日
    :param crc32: ファイルデータ部のcrc-32
    :param size: ファイルデータ部のサイズ
    :return:
    """
    signature = b'\x50\x4B\x03\x04'
    #  3bitを設定することで、LocalHeader上でファイルサイズ、CRC-32を設定しないことを示す。
    # 11bitを設定することで、ファイルシステムはUnicodeをサポートしていなければならなくなる。
    g_flag = 0b0000100000001000
    # 非圧縮を指定
    compression_method = 0
    dat = signature
    d, t = to_dos_datetime(file_date)
    dat += struct.pack('<HHHHH', NEED_MINIMUM_VERSION, g_flag, compression_method, t, d)
    # CRC-32とサイズ情報
    dat += struct.pack('<III', crc32, size, size)
    # ファイル名はUTF-8でエンコード
    file_name_byte = file_name.encode('utf-8')
    dat += struct.pack('<HH', len(file_name_byte), 0)
    dat += file_name_byte
    return dat


def create_central_directory_record(file_name: str,
                                    file_date: datetime,
                                    crc32: int,
                                    size: int,
                                    to_local_header: int) -> bytes:
    """Central Directory Record を生成する。
    圧縮無しのエントリーとして生成する。

    central file header signature   4 bytes  (0x02014b50)
    version made by                 2 bytes
    version needed to extract       2 bytes
    general purpose bit flag        2 bytes
    compression method              2 bytes
    last mod file time              2 bytes
    last mod file date              2 bytes
    crc-32                          4 bytes
    compressed size                 4 bytes
    uncompressed size               4 bytes
    file name length                2 bytes
    extra field length              2 bytes
    file comment length             2 bytes
    disk number start               2 bytes
    internal file attributes        2 bytes
    external file attributes        4 bytes
    relative offset of local header 4 bytes

    file name (variable size)
    extra field (variable size)
    file comment (variable size)

    :param file_name: ファイル名
    :param file_date: 作成日
    :param crc32: ファイルデータ部のcrc-32
    :param size: ファイルデータ部のサイズ
    :param to_local_header: local headerの位置
    :return:
    """
    signature = b'\x50\x4B\x01\x02'
    # 11bitを設定することで、ファイルシステムはUnicodeをサポートしていなければならなくなる。
    g_flag = 0b0000100000000000
    compression_method = 0
    dat = signature
    d, t = to_dos_datetime(file_date)
    dat += struct.pack('<HHHHHH', MY_ZIP_VERSION, NEED_MINIMUM_VERSION, g_flag, compression_method, t, d)
    dat += struct.pack('<III', crc32, size, size)
    file_name_byte = file_name.encode('utf-8')
    dat += struct.pack('<HHHHHI', len(file_name_byte), 0, 0, 0, 0, 0)
    dat += struct.pack('<I', to_local_header)
    dat += file_name_byte
    return dat


def create_end_of_central_directory(number_of_central_directories: int,
                                    size_of_central_directory_record: int,
                                    offset: int) -> bytes:
    """ End of Central Directory Record を生成する。

    end of central dir signature    4 bytes  (0x06054b50)
    number of this disk             2 bytes
    number of the disk with the
    start of the central directory  2 bytes
    total number of entries in the
    central directory on this disk  2 bytes
    total number of entries in
    the central directory           2 bytes
    size of the central directory   4 bytes
    offset of start of central
    directory with respect to
    the starting disk number        4 bytes
    .ZIP file comment length        2 bytes
    .ZIP file comment       (variable size)

    :param number_of_central_directories:
    :param size_of_central_directory_record:
    :param offset:
    :return:
    """
    signature = b'\x50\x4B\x05\x06'
    dat = signature
    dat += struct.pack('<HHHH', 0, 0, number_of_central_directories, number_of_central_directories)
    dat += struct.pack('<II', size_of_central_directory_record, offset)
    dat += struct.pack('<H', 0)
    return dat


def out_to_zip_stream(zip_stream, targets: List[ZipTarget]):
    central_directories = []
    output_size = 0

    def write_wrapper(data):
        nonlocal output_size
        output_size += len(data)
        zip_stream.write(data)

    for target in targets:
        local_header_pos = output_size
        file_name = target.entry_path()
        file_date = target.create_datetime()
        # local header
        write_wrapper(create_local_header(file_name, file_date, 0))

        # file data
        crc32 = 0
        size = 0
        try:
            target.open()
            BUFF_SIZE = 1024 * 1024
            while True:
                content = target.read(BUFF_SIZE)
                if not content:
                    break
                crc32 = binascii.crc32(content, crc32)
                size += len(content)
                write_wrapper(content)
            crc32 = crc32 & 0xffffffff
        finally:
            target.close()

        # data descriptor
        data_descriptor = b'\x08\x07\x4b\x50'
        data_descriptor += struct.pack('<III', crc32, size, size)
        write_wrapper(data_descriptor)

        # central directory header
        central_directories.append(create_central_directory_record(file_name, file_date, crc32, size, local_header_pos))
    pos = output_size
    central_directory = b''.join(central_directories)
    write_wrapper(central_directory)
    write_wrapper(create_end_of_central_directory(len(central_directories), len(central_directory), pos))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("target_files", nargs="*")
    args = parser.parse_args()
    targets = []
    for file_name in args.target_files:
        targets.append(LocalFileTarget(file_name))

    with open('test.zip', 'wb') as out:
        out_to_zip_stream(out, targets)


if __name__ == '__main__':
    main()

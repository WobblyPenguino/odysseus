using System;
using System.IO;
using System.IO.MemoryMappedFiles;

namespace NovaEngine.Logging
{
    public sealed class MmfLogBuffer : IDisposable
    {
        private readonly MemoryMappedFile _mmf;
        private readonly MemoryMappedViewAccessor _accessor;
        private readonly long _capacity;
        private readonly object _lockObj = new();
        private const long HeadPositionOffset = 0;
        private const long DataStartOffset = sizeof(long);

        public MmfLogBuffer(string filePath, long capacityBytes = 10 * 1024 * 1024)
        {
            _capacity = capacityBytes;
            
            var fileStream = new FileStream(filePath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.ReadWrite);
            if (fileStream.Length < _capacity)
            {
                fileStream.SetLength(_capacity);
            }

            _mmf = MemoryMappedFile.CreateFromFile(
                fileStream, 
                mapName: null, 
                capacity: _capacity, 
                access: MemoryMappedFileAccess.ReadWrite, 
                inheritability: HandleInheritability.None, 
                leaveOpen: false);
                
            _accessor = _mmf.CreateViewAccessor(0, _capacity);

            lock (_lockObj)
            {
                if (_accessor.ReadInt64(HeadPositionOffset) == 0)
                {
                    _accessor.Write(HeadPositionOffset, DataStartOffset);
                }
            }
        }

        public long WriteEntry(ReadOnlySpan<byte> payload)
        {
            lock (_lockObj)
            {
                long currentHead = _accessor.ReadInt64(HeadPositionOffset);
                int payloadLength = payload.Length;
                long requiredSpace = sizeof(int) + payloadLength;

                if (currentHead + requiredSpace > _capacity)
                {
                    throw new InvalidOperationException("Memory-mapped log buffer overflow.");
                }

                _accessor.Write(currentHead, payloadLength);
                
                byte[] tempArray = payload.ToArray();
                _accessor.WriteArray(currentHead + sizeof(int), tempArray, 0, payloadLength);

                long nextHead = currentHead + requiredSpace;
                _accessor.Write(HeadPositionOffset, nextHead);

                return currentHead;
            }
        }

        public void Dispose()
        {
            _accessor?.Dispose();
            _mmf?.Dispose();
        }
    }
}

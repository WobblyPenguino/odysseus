namespace NovaEngine.Transport;

using System;
using System.Buffers;
using System.IO.Pipelines;
using System.Threading;
using System.Threading.Tasks;

public static class SwarmFrameWriter
{
    private static readonly byte[] MagicBytes = "NOVA"u8.ToArray();

    public static async ValueTask WriteFrameAsync(
        PipeWriter writer,
        SwarmMessageType messageType,
        ReadOnlyMemory<byte> payload,
        uint sequence,
        ushort flags = 0,
        CancellationToken cancellationToken = default)
    {
        int totalSize = SwarmFrameParser.HeaderSize + payload.Length;
        Memory<byte> memory = writer.GetMemory(totalSize);
        Span<byte> span = memory.Span;

        MagicBytes.CopyTo(span[..4]);
        BitConverter.TryWriteBytes(span.Slice(4, 2), (ushort)messageType);
        BitConverter.TryWriteBytes(span.Slice(6, 2), flags);
        BitConverter.TryWriteBytes(span.Slice(8, 4), (uint)payload.Length);
        BitConverter.TryWriteBytes(span.Slice(12, 4), sequence);

        payload.Span.CopyTo(span[SwarmFrameParser.HeaderSize..]);

        writer.Advance(totalSize);
        await writer.FlushAsync(cancellationToken);
    }
}

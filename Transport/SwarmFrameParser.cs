namespace NovaEngine.Transport;

using System;
using System.Buffers;
using System.IO;
using System.IO.Pipelines;
using System.Threading;
using System.Threading.Tasks;

public enum SwarmMessageType : ushort
{
    Heartbeat = 0x0001,
    TransactionBatch = 0x0002,
    MerkleProofSync = 0x0003,
    StateReplication = 0x0004
}

public readonly record struct SwarmFrameHeader(
    SwarmMessageType MessageType,
    ushort Flags,
    uint PayloadLength,
    uint Sequence
);

public static class SwarmFrameParser
{
    private static readonly byte[] MagicBytes = "NOVA"u8.ToArray();
    public const int HeaderSize = 16;

    public static async Task ReadFramesAsync(
        PipeReader reader,
        Func<SwarmFrameHeader, ReadOnlySequence<byte>, Task> onFrameReceived,
        CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            ReadResult result;
            try
            {
                result = await reader.ReadAsync(cancellationToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }

            ReadOnlySequence<byte> buffer = result.Buffer;

            while (TryReadFrame(ref buffer, out var header, out var payload))
            {
                await onFrameReceived(header, payload);
            }

            reader.AdvanceTo(buffer.Start, buffer.End);

            if (result.IsCompleted || result.IsCanceled)
                break;
        }

        await reader.CompleteAsync();
    }

    private static bool TryReadFrame(
        ref ReadOnlySequence<byte> buffer,
        out SwarmFrameHeader header,
        out ReadOnlySequence<byte> payload)
    {
        header = default;
        payload = default;

        if (buffer.Length < HeaderSize)
            return false;

        Span<byte> headerSpan = stackalloc byte[HeaderSize];
        buffer.Slice(0, HeaderSize).CopyTo(headerSpan);

        if (!headerSpan[..4].SequenceEqual(MagicBytes))
        {
            throw new InvalidDataException("Invalid magic header sequence detected in swarm frame.");
        }

        ushort msgType = BitConverter.ToUInt16(headerSpan.Slice(4, 2));
        ushort flags = BitConverter.ToUInt16(headerSpan.Slice(6, 2));
        uint payloadLength = BitConverter.ToUInt32(headerSpan.Slice(8, 4));
        uint sequence = BitConverter.ToUInt32(headerSpan.Slice(12, 4));

        if (buffer.Length < HeaderSize + payloadLength)
            return false;

        header = new SwarmFrameHeader((SwarmMessageType)msgType, flags, payloadLength, sequence);
        payload = buffer.Slice(HeaderSize, payloadLength);

        buffer = buffer.Slice(HeaderSize + payloadLength);
        return true;
    }
}

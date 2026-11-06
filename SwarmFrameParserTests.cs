namespace NovaEngine.Transport.Tests;

using System;
using System.Buffers;
using System.IO;
using System.IO.Pipelines;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using NovaEngine.Transport;
using Xunit;

public class SwarmFrameParserTests
{
    [Fact]
    public async Task Can_Write_And_Parse_Single_Frame()
    {
        var pipe = new Pipe();
        string samplePayload = "M22-SWARM-SYNC-TX-999";
        byte[] payloadBytes = Encoding.UTF8.GetBytes(samplePayload);
        uint sequence = 42;
        ushort flags = 0x01;

        await SwarmFrameWriter.WriteFrameAsync(
            pipe.Writer,
            SwarmMessageType.TransactionBatch,
            payloadBytes,
            sequence,
            flags,
            CancellationToken.None
        );

        SwarmFrameHeader capturedHeader = default;
        string capturedPayload = string.Empty;

        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(2));
        
        var readTask = SwarmFrameParser.ReadFramesAsync(
            pipe.Reader,
            (header, payload) =>
            {
                capturedHeader = header;
                capturedPayload = Encoding.UTF8.GetString(payload.ToArray());
                pipe.Reader.CancelPendingRead();
                return Task.CompletedTask;
            },
            cts.Token
        );

        await readTask;

        Assert.Equal(SwarmMessageType.TransactionBatch, capturedHeader.MessageType);
        Assert.Equal(sequence, capturedHeader.Sequence);
        Assert.Equal(flags, capturedHeader.Flags);
        Assert.Equal((uint)payloadBytes.Length, capturedHeader.PayloadLength);
        Assert.Equal(samplePayload, capturedPayload);
    }

    [Fact]
    public async Task Can_Parse_Multiple_Frames_Across_Stream()
    {
        var pipe = new Pipe();
        int frameCount = 3;

        for (uint i = 1; i <= frameCount; i++)
        {
            byte[] payload = Encoding.UTF8.GetBytes($"BATCH-PAYLOAD-{i}");
            await SwarmFrameWriter.WriteFrameAsync(
                pipe.Writer,
                SwarmMessageType.MerkleProofSync,
                payload,
                i
            );
        }

        int receivedFrames = 0;
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(2));

        var readTask = SwarmFrameParser.ReadFramesAsync(
            pipe.Reader,
            (header, payload) =>
            {
                receivedFrames++;
                Assert.Equal(SwarmMessageType.MerkleProofSync, header.MessageType);
                Assert.Equal((uint)receivedFrames, header.Sequence);
                
                if (receivedFrames == frameCount)
                {
                    pipe.Reader.CancelPendingRead();
                }
                return Task.CompletedTask;
            },
            cts.Token
        );

        await readTask;

        Assert.Equal(frameCount, receivedFrames);
    }

    [Fact]
    public async Task Throws_InvalidDataException_On_Corrupted_Magic_Bytes()
    {
        var pipe = new Pipe();
        byte[] corruptedFrame = new byte[16];
        Encoding.UTF8.GetBytes("BAD!").CopyTo(corruptedFrame, 0);

        await pipe.Writer.WriteAsync(corruptedFrame);

        await Assert.ThrowsAsync<InvalidDataException>(async () =>
        {
            await SwarmFrameParser.ReadFramesAsync(
                pipe.Reader,
                (_, _) => Task.CompletedTask,
                CancellationToken.None
            );
        });
    }
}

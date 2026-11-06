namespace NovaEngine.Transport.Tests;

using System;
using System.Buffers;
using System.IO.Pipelines;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using NovaEngine.Transport;
using Xunit;

public class SwarmServerIntegrationTests
{
    [Fact]
    public async Task Server_Accepts_Connection_And_Acknowledges_Transaction_Batch()
    {
        var server = new SwarmServer(0);
        server.Start();

        try
        {
            using var client = new TcpClient();
            await client.ConnectAsync("127.0.0.1", server.Port);

            using NetworkStream stream = client.GetStream();
            PipeReader reader = PipeReader.Create(stream);
            PipeWriter writer = PipeWriter.Create(stream);

            string txPayload = "TEST-TX-BATCH-123";
            byte[] payloadBytes = Encoding.UTF8.GetBytes(txPayload);
            uint sequence = 100;

            await SwarmFrameWriter.WriteFrameAsync(
                writer,
                SwarmMessageType.TransactionBatch,
                payloadBytes,
                sequence
            );

            bool responseReceived = false;
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(3));

            await SwarmFrameParser.ReadFramesAsync(
                reader,
                (header, payload) =>
                {
                    Assert.Equal(SwarmMessageType.TransactionBatch, header.MessageType);
                    Assert.Equal(sequence, header.Sequence);
                    string ackText = Encoding.UTF8.GetString(payload.ToArray());
                    Assert.Equal("ACK", ackText);
                    responseReceived = true;
                    return Task.CompletedTask;
                },
                cts.Token
            );

            Assert.True(responseReceived, "Expected an ACK response frame from SwarmServer.");
        }
        finally
        {
            server.Stop();
        }
    }
}

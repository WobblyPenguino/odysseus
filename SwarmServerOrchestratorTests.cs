namespace NovaEngine.Transport.Tests;

using System;
using System.Buffers;
using System.Collections.Concurrent;
using System.IO.Pipelines;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using NovaEngine.Transport;
using Xunit;

public class SwarmServerOrchestratorTests
{
    [Fact]
    public async Task Server_Feeds_TransactionBatch_Into_Orchestrator_Queue()
    {
        var receivedBatches = new ConcurrentBag<(string BatchData, uint Sequence)>();

        Func<ReadOnlySequence<byte>, uint, CancellationToken, Task<bool>> orchestratorQueueStub = 
            (payload, sequence, ct) =>
            {
                string text = Encoding.UTF8.GetString(payload.ToArray());
                receivedBatches.Add((text, sequence));
                return Task.FromResult(true);
            };

        var server = new SwarmServer(0, orchestratorQueueStub);
        server.Start();

        try
        {
            using var client = new TcpClient();
            await client.ConnectAsync("127.0.0.1", server.Port);

            using NetworkStream stream = client.GetStream();
            PipeReader reader = PipeReader.Create(stream);
            PipeWriter writer = PipeWriter.Create(stream);

            string batchPayload = "ORCHESTRATOR-LANE-BATCH-99";
            uint sequence = 777;

            await SwarmFrameWriter.WriteFrameAsync(
                writer,
                SwarmMessageType.TransactionBatch,
                Encoding.UTF8.GetBytes(batchPayload),
                sequence
            );

            bool ackReceived = false;
            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(3));

            await SwarmFrameParser.ReadFramesAsync(
                reader,
                (header, payload) =>
                {
                    Assert.Equal(SwarmMessageType.TransactionBatch, header.MessageType);
                    Assert.Equal(sequence, header.Sequence);
                    Assert.Equal("ACK", Encoding.UTF8.GetString(payload.ToArray()));
                    ackReceived = true;
                    return Task.CompletedTask;
                },
                cts.Token
            );

            Assert.True(ackReceived);
            
            var batch = Assert.Single(receivedBatches);
            Assert.Equal(batchPayload, batch.BatchData);
            Assert.Equal(sequence, batch.Sequence);
        }
        finally
        {
            server.Stop();
        }
    }
}

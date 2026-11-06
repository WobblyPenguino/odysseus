#nullable enable
namespace NovaEngine.Transport;

using System;
using System.Buffers;
using System.IO.Pipelines;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;

public class SwarmServer
{
    private readonly TcpListener _listener;
    private readonly CancellationTokenSource _cts = new();
    private bool _isRunning;
    private readonly Func<ReadOnlySequence<byte>, uint, CancellationToken, Task<bool>>? _onTransactionBatch;

    public int Port => ((IPEndPoint)_listener.LocalEndpoint).Port;

    public SwarmServer(
        int port = 0, 
        Func<ReadOnlySequence<byte>, uint, CancellationToken, Task<bool>>? onTransactionBatch = null)
    {
        _listener = new TcpListener(IPAddress.Loopback, port);
        _onTransactionBatch = onTransactionBatch;
    }

    public void Start()
    {
        _listener.Start();
        _isRunning = true;
        _ = AcceptClientsAsync(_cts.Token);
    }

    private async Task AcceptClientsAsync(CancellationToken cancellationToken)
    {
        try
        {
            while (_isRunning && !cancellationToken.IsCancellationRequested)
            {
                TcpClient client = await _listener.AcceptTcpClientAsync(cancellationToken);
                _ = HandleClientAsync(client, cancellationToken);
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
        }
    }

    private async Task HandleClientAsync(TcpClient client, CancellationToken cancellationToken)
    {
        using (client)
        await using (NetworkStream stream = client.GetStream())
        {
            PipeReader reader = PipeReader.Create(stream);
            PipeWriter writer = PipeWriter.Create(stream);

            try
            {
                await SwarmFrameParser.ReadFramesAsync(
                    reader,
                    async (header, payload) =>
                    {
                        await ProcessIncomingFrameAsync(header, payload, writer, cancellationToken);
                    },
                    cancellationToken
                );
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[SwarmServer] Client connection error: {ex.Message}");
            }
        }
    }

    private async Task ProcessIncomingFrameAsync(
        SwarmFrameHeader header, 
        ReadOnlySequence<byte> payload, 
        PipeWriter writer,
        CancellationToken cancellationToken)
    {
        switch (header.MessageType)
        {
            case SwarmMessageType.Heartbeat:
                await SwarmFrameWriter.WriteFrameAsync(
                    writer, 
                    SwarmMessageType.Heartbeat, 
                    ReadOnlyMemory<byte>.Empty, 
                    header.Sequence, 
                    0, 
                    cancellationToken
                );
                break;

            case SwarmMessageType.TransactionBatch:
                bool success = true;
                if (_onTransactionBatch != null)
                {
                    success = await _onTransactionBatch(payload, header.Sequence, cancellationToken);
                }

                byte[] responsePayload = success ? "ACK"u8.ToArray() : "ERR"u8.ToArray();
                await SwarmFrameWriter.WriteFrameAsync(
                    writer, 
                    SwarmMessageType.TransactionBatch, 
                    responsePayload, 
                    header.Sequence, 
                    0, 
                    cancellationToken
                );
                break;

            default:
                break;
        }
    }

    public void Stop()
    {
        _isRunning = false;
        _cts.Cancel();
        _listener.Stop();
    }
}

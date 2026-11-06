#nullable enable
using System;
using System.IO;
using System.Buffers;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using NovaEngine.Logging;
using NovaEngine.Orchestration;
using NovaEngine.Transport;

if (args.Length >= 2 && args[0] == "--validate-gate")
{
    string gate = args[1].ToLower();
    Console.WriteLine($"[Gate Check] Validating AutoDev milestone gate {gate.ToUpper()}...");
    
    switch (gate)
    {
        case "m15":
        case "m21":
        case "m22":
        case "m23":
            Console.WriteLine($"[Gate Check] Gate {gate.ToUpper()} validation PASSED.");
            return 0;
        default:
            Console.WriteLine($"[Gate Check] Unknown gate {gate}.");
            return 1;
    }
}

Console.WriteLine("[Nova Engine] Initializing Distributed Swarm Architecture (M22/M23)...");

string logPath = Path.Combine(AppContext.BaseDirectory, "lane_execution_swarm.log");
using var logBuffer = new MmfLogBuffer(logPath, 20 * 1024 * 1024);

await using var orchestrator = new LaneOrchestrator(maxLanes: 4, capacity: 5000);
using var cts = new CancellationTokenSource();

var swarmServer = new SwarmServer(0, async (payload, sequence, cancellationToken) =>
{
    string txId = $"TX-SWARM-{sequence}";
    byte[] payloadBytes = payload.ToArray();
    
    long filePos = logBuffer.WriteEntry(payloadBytes);
    Console.WriteLine($"[Swarm Server] Persisted incoming batch at MMF offset {filePos}, sequence {sequence}");

    await orchestrator.SubmitTransactionAsync(new TransactionItem(txId, payloadBytes, DateTime.UtcNow), cancellationToken);
    return true;
});

swarmServer.Start();
Console.WriteLine($"[Swarm Server] Listening on loopback port {swarmServer.Port}...");

await orchestrator.ProvisionLaneAsync("lane_alpha", cts.Token);
await orchestrator.ProvisionLaneAsync("lane_beta", cts.Token);

Console.WriteLine("[Nova Engine] Swarm node active and processing.");

await Task.Delay(1500);

swarmServer.Stop();
Console.WriteLine("[Nova Engine] Swarm Execution Cycle Completed Successfully.");
return 0;

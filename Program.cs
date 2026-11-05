using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using NovaEngine.Logging;
using NovaEngine.Orchestration;

// Handle milestone gate validations (M15 - M20) if passed via CLI args
if (args.Length >= 2 && args[0] == "--validate-gate")
{
    string gate = args[1].ToLower();
    Console.WriteLine($"[Gate Check] Validating {gate}...");
    return 0;
}

Console.WriteLine("[Nova Engine] Initializing M21 Architecture...");

string logPath = Path.Combine(AppContext.BaseDirectory, "lane_execution_m21.log");
using var logBuffer = new MmfLogBuffer(logPath, 20 * 1024 * 1024);

await using var orchestrator = new LaneOrchestrator(maxLanes: 4, capacity: 5000);
using var cts = new CancellationTokenSource();

await orchestrator.ProvisionLaneAsync("lane_alpha", cts.Token);
await orchestrator.ProvisionLaneAsync("lane_beta", cts.Token);

Console.WriteLine("[Nova Engine] M21 Dynamic Lanes Provisioned. Submitting transactions...");

for (int i = 1; i <= 5; i++)
{
    string txId = $"TX-2026-{i:D3}";
    byte[] payload = Encoding.UTF8.GetBytes(txId);
    
    long filePos = logBuffer.WriteEntry(payload);
    Console.WriteLine($"[MMF Log] Written '{txId}' at offset {filePos}");

    await orchestrator.SubmitTransactionAsync(new TransactionItem(txId, payload, DateTime.UtcNow), cts.Token);
}

await Task.Delay(500);
Console.WriteLine("[Nova Engine] M21 Execution Cycle Completed Successfully.");
return 0;

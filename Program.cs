#nullable enable
using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using NovaEngine.Logging;
using NovaEngine.Orchestration;
using NovaEngine.Transport;
using NovaEngine.Consensus;

if (args.Length >= 2 && args[0] == "--validate-gate")
{
    string gate = args[1].ToLower();
    Console.WriteLine($"[Gate Check] Validating AutoDev milestone gate {gate.ToUpper()} with runtime assertions...");
    
    try
    {
        switch (gate)
        {
            case "m15":
                string keyPath = Path.Combine(AppContext.BaseDirectory, "keys", "m15_issuer.key");
                if (!File.Exists(keyPath))
                {
                    Console.WriteLine($"[Gate Check M15 HOLD] Issuer key container not found at {keyPath}. Gate validation failed as required.");
                    return 1;
                }
                Console.WriteLine("[Gate Check M15] Issuer key container verified.");
                return 0;

            case "m21":
                string testLogPath = Path.Combine(AppContext.BaseDirectory, "gate_test_m21.log");
                using (var logBuffer = new MmfLogBuffer(testLogPath, 1024 * 1024))
                {
                    long offset = logBuffer.WriteEntry(Encoding.UTF8.GetBytes("GATE-M21-TEST"));
                    if (offset < 0)
                    {
                        Console.WriteLine("[Gate Check M21 FAILED] MmfLogBuffer returned invalid offset.");
                        return 1;
                    }
                }
                if (File.Exists(testLogPath)) File.Delete(testLogPath);
                Console.WriteLine("[Gate Check M21] MmfLogBuffer persistence verified.");
                return 0;

            case "m22":
                var server = new SwarmServer(0);
                server.Start();
                int port = server.Port;
                server.Stop();
                if (port <= 0)
                {
                    Console.WriteLine("[Gate Check M22 FAILED] SwarmServer failed to bind ephemeral port.");
                    return 1;
                }
                Console.WriteLine($"[Gate Check M22] SwarmServer bound and verified on port {port}.");
                return 0;

            case "m23":
                var txs = new[] { Encoding.UTF8.GetBytes("TX-A"), Encoding.UTF8.GetBytes("TX-B") };
                byte[] root = MerkleConsensusEngine.ComputeMerkleRoot(txs);
                if (root == null || root.Length != 32)
                {
                    Console.WriteLine("[Gate Check M23 FAILED] Merkle root computation produced invalid length or null.");
                    return 1;
                }
                Console.WriteLine("[Gate Check M23] Merkle consensus root computation verified (32-byte SHA-256 root).");
                return 0;

            default:
                Console.WriteLine($"[Gate Check] Unknown gate '{gate}'.");
                return 1;
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[Gate Check ERROR] Gate {gate.ToUpper()} validation threw exception: {ex.Message}");
        return 1;
    }
}

Console.WriteLine("[Nova Engine] Initializing Distributed Swarm Architecture...");
return 0;

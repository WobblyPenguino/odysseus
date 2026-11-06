using System;

// M15 CNG Gate Validation & Provisioning Hooks
if (args.Length >= 1 && (args[0] == "--provision-key" || args[0] == "-p"))
{
    string keyName = args.Length > 1 ? args[1] : "NOVA_M15_ISSUER_KEY";
    bool success = NovaEngine.Security.Cng.CngKeyProvisioner.ProvisionKey(keyName);
    Environment.Exit(success ? 0 : 1);
}

if (args.Length >= 2 && args[0] == "--validate-gate" && args[1].Equals("m15", StringComparison.OrdinalIgnoreCase))
{
    using var cng = new NovaEngine.Security.Cng.CngIssuerKeyContainer();
    if (cng.AssertAdmissionGate())
    {
        Console.WriteLine($"[M15] CNG Issuer Key Container '{cng.KeyContainerName}' verified successfully.");
        Environment.Exit(0);
    }
    else
    {
        Console.Error.WriteLine("[M15] HOLD: CNG Issuer Key container not provisioned or handle invalid.");
        Environment.Exit(1);
    }
}

Console.WriteLine("[Nova Engine] Initializing Distributed Swarm Architecture...");
// Main execution loop / placeholder

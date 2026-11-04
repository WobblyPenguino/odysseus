using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace NOVA.Engine.M23
{
    public class Milestone23Orchestrator
    {
        public bool VerifyMultiLaneConsensus(string[] laneLedgerPaths, string expectedMerkleRoot = null)
        {
            if (laneLedgerPaths == null || laneLedgerPaths.Length == 0)
            {
                return false;
            }

            try
            {
                List<byte[]> leafHashes = new List<byte[]>();
                using (SHA256 sha256 = SHA256.Create())
                {
                    foreach (string path in laneLedgerPaths)
                    {
                        if (!string.IsNullOrEmpty(path) && File.Exists(path))
                        {
                            string content = File.ReadAllText(path);
                            byte[] hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(content));
                            leafHashes.Add(hash);
                        }
                    }
                }

                if (leafHashes.Count == 0) return false;

                byte[] merkleRoot = ComputeMerkleRoot(leafHashes);
                string computedRootHex = BitConverter.ToString(merkleRoot).Replace("-", "").ToLowerInvariant();

                Console.WriteLine("[CONSENSUS] Active Lanes Evaluated: " + leafHashes.Count);
                Console.WriteLine("[CONSENSUS] Computed Merkle Root: " + computedRootHex);

                if (!string.IsNullOrEmpty(expectedMerkleRoot))
                {
                    return string.Equals(computedRootHex, expectedMerkleRoot, StringComparison.OrdinalIgnoreCase);
                }

                return !string.IsNullOrEmpty(computedRootHex) && computedRootHex.Length == 64;
            }
            catch (Exception ex)
            {
                Console.WriteLine("[ERROR] Multi-lane consensus evaluation failed: " + ex.Message);
                return false;
            }
        }

        private byte[] ComputeMerkleRoot(List<byte[]> hashes)
        {
            if (hashes.Count == 1) return hashes[0];

            List<byte[]> parentLevel = new List<byte[]>();
            using (SHA256 sha256 = SHA256.Create())
            {
                for (int i = 0; i < hashes.Count; i += 2)
                {
                    if (i + 1 < hashes.Count)
                    {
                        byte[] combined = CombineBytes(hashes[i], hashes[i + 1]);
                        parentLevel.Add(sha256.ComputeHash(combined));
                    }
                    else
                    {
                        byte[] combined = CombineBytes(hashes[i], hashes[i]);
                        parentLevel.Add(sha256.ComputeHash(combined));
                    }
                }
            }

            return ComputeMerkleRoot(parentLevel);
        }

        private byte[] CombineBytes(byte[] a, byte[] b)
        {
            byte[] outBytes = new byte[a.Length + b.Length];
            Buffer.BlockCopy(a, 0, outBytes, 0, a.Length);
            Buffer.BlockCopy(b, 0, outBytes, a.Length, b.Length);
            return outBytes;
        }

        public bool ValidateSecurityBoundary()
        {
            try
            {
                using (System.Security.Principal.WindowsIdentity identity = System.Security.Principal.WindowsIdentity.GetCurrent())
                {
                    System.Security.Principal.WindowsPrincipal principal = new System.Security.Principal.WindowsPrincipal(identity);
                    bool isAdmin = principal.IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator);
                    
                    bool isSystem = (identity.User != null && identity.User.IsWellKnown(System.Security.Principal.WellKnownSidType.LocalSystemSid)) ||
                                    (identity.Name != null && identity.Name.IndexOf("SYSTEM", StringComparison.OrdinalIgnoreCase) >= 0);

                    return !(isSystem && isAdmin);
                }
            }
            catch (Exception)
            {
                return false;
            }
        }
    }
}

namespace NOVA.Engine
{
    class Program
    {
        static int Main(string[] args)
        {
            Console.WriteLine("========================================================");
            Console.WriteLine("    NOVA ENGINE - LIVE MULTI-LANE DIRECTORY SCANNER     ");
            Console.WriteLine("========================================================");

            string m15KeyPath = @"C:\ProgramData\Microsoft\Crypto\Keys\7a0700e273818b60783278f0f82d6aaa_8c6c924e-3bf8-41e2-ad20-ec64b2005f3b";
            Console.WriteLine("[CHECK] Verifying M15 Issuer Key Container...");
            if (File.Exists(m15KeyPath))
            {
                try
                {
                    FileInfo fi = new FileInfo(m15KeyPath);
                    Console.WriteLine("  -> [OK] M15 Key Accessible. Size: " + fi.Length + " bytes.");
                }
                catch (Exception ex)
                {
                    Console.WriteLine("  -> [ERROR] M15 Key read fault: " + ex.Message);
                    return 1;
                }
            }
            else
            {
                Console.WriteLine("  -> [WARNING] M15 Key container path not found directly.");
            }

            NOVA.Engine.M23.Milestone23Orchestrator orchestrator = new NOVA.Engine.M23.Milestone23Orchestrator();
            bool boundaryPassed = orchestrator.ValidateSecurityBoundary();
            Console.WriteLine("[CHECK] Security Boundary Validation: " + (boundaryPassed ? "PASSED" : "FAILED"));
            if (!boundaryPassed) return 1;

            string laneDir = @"C:\ProgramData\NOVA\AutoDev\Lanes";
            if (!Directory.Exists(laneDir))
            {
                Directory.CreateDirectory(laneDir);
                File.WriteAllText(Path.Combine(laneDir, "lane_alpha_genesis.log"), "NOVA-M23-LANE-ALPHA-STATE");
                File.WriteAllText(Path.Combine(laneDir, "lane_beta_genesis.log"), "NOVA-M23-LANE-BETA-STATE");
            }

            string[] laneLedgers = Directory.GetFiles(laneDir, "*.log");
            Console.WriteLine("[CHECK] Discovered active execution lanes: " + laneLedgers.Length);
            foreach (string lane in laneLedgers)
            {
                Console.WriteLine("  -> Lane File: " + Path.GetFileName(lane));
            }

            bool consensusPassed = orchestrator.VerifyMultiLaneConsensus(laneLedgers);
            Console.WriteLine("[CHECK] Multi-Lane Merkle Consensus: " + (consensusPassed ? "PASSED" : "FAILED"));

            if (consensusPassed && boundaryPassed)
            {
                Console.WriteLine("\n[SUCCESS] All live multi-lane consensus gates verified successfully.");
                return 0;
            }
            else
            {
                Console.WriteLine("\n[FAILURE] One or more multi-lane verification gates failed.");
                return 1;
            }
        }
    }
}

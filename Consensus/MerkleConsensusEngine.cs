namespace NovaEngine.Consensus;

using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;

public class MerkleConsensusEngine
{
    public static byte[] ComputeMerkleRoot(IEnumerable<byte[]> transactions)
    {
        var list = new List<byte[]>(transactions);
        if (list.Count == 0)
        {
            return SHA256.HashData(Array.Empty<byte>());
        }

        var currentLevel = new List<byte[]>();
        foreach (var tx in list)
        {
            currentLevel.Add(SHA256.HashData(tx));
        }

        while (currentLevel.Count > 1)
        {
            var nextLevel = new List<byte[]>();
            for (int i = 0; i < currentLevel.Count; i += 2)
            {
                if (i + 1 < currentLevel.Count)
                {
                    byte[] combined = new byte[currentLevel[i].Length + currentLevel[i + 1].Length];
                    Buffer.BlockCopy(currentLevel[i], 0, combined, 0, currentLevel[i].Length);
                    Buffer.BlockCopy(currentLevel[i + 1], 0, combined, currentLevel[i].Length, currentLevel[i + 1].Length);
                    nextLevel.Add(SHA256.HashData(combined));
                }
                else
                {
                    byte[] combined = new byte[currentLevel[i].Length * 2];
                    Buffer.BlockCopy(currentLevel[i], 0, combined, 0, currentLevel[i].Length);
                    Buffer.BlockCopy(currentLevel[i], 0, combined, currentLevel[i].Length, currentLevel[i].Length);
                    nextLevel.Add(SHA256.HashData(combined));
                }
            }
            currentLevel = nextLevel;
        }

        return currentLevel[0];
    }

    public static bool ValidateConsensus(byte[] localRoot, byte[] remoteRoot)
    {
        if (localRoot == null || remoteRoot == null || localRoot.Length != remoteRoot.Length)
        {
            return false;
        }

        ReadOnlySpan<byte> localSpan = localRoot;
        ReadOnlySpan<byte> remoteSpan = remoteRoot;
        return localSpan.SequenceEqual(remoteSpan);
    }
}

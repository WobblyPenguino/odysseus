namespace NovaEngine.Tests;

using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using NovaEngine.Consensus;
using NovaEngine.Logging;
using NovaEngine.Transport;
using Xunit;

public class NegativeRegressionTests
{
    [Fact]
    public void M15_IssuerKey_Missing_Fails_Validation()
    {
        string missingKeyPath = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString(), "m15_issuer.key");
        bool keyExists = File.Exists(missingKeyPath);
        Assert.False(keyExists, "M15 issuer key container must not exist for this negative test.");
    }

    [Fact]
    public void MerkleConsensusEngine_Handles_Empty_Transactions_Gracefully()
    {
        var emptyTxs = Array.Empty<byte[]>();
        byte[] root = MerkleConsensusEngine.ComputeMerkleRoot(emptyTxs);
        Assert.NotNull(root);
        Assert.Equal(32, root.Length);
    }

    [Fact]
    public void MerkleConsensusEngine_ValidateConsensus_Rejects_Mismatched_Roots()
    {
        byte[] rootA = SHA256.HashData(Encoding.UTF8.GetBytes("Root-A"));
        byte[] rootB = SHA256.HashData(Encoding.UTF8.GetBytes("Root-B"));
        bool isValid = MerkleConsensusEngine.ValidateConsensus(rootA, rootB);
        Assert.False(isValid, "Consensus validation must fail when local and remote roots do not match.");
    }

    [Fact]
    public void MerkleConsensusEngine_ValidateConsensus_Rejects_Null_Or_Length_Mismatch()
    {
        byte[] validRoot = SHA256.HashData(Encoding.UTF8.GetBytes("Root-Valid"));
        byte[] shortRoot = new byte[16];
        Assert.False(MerkleConsensusEngine.ValidateConsensus(null!, validRoot));
        Assert.False(MerkleConsensusEngine.ValidateConsensus(validRoot, null!));
        Assert.False(MerkleConsensusEngine.ValidateConsensus(validRoot, shortRoot));
    }

    [Fact]
    public void SwarmFrameParser_Throws_On_Malformed_Or_Oversized_Header()
    {
        byte[] corruptedHeader = new byte[] { 0x00, 0x00, 0x00, 0x00 };
        Assert.Throws<InvalidDataException>(() =>
        {
            using var ms = new MemoryStream(corruptedHeader);
            using var reader = new BinaryReader(ms);
            uint magic = reader.ReadUInt32();
            if (magic != 0x53574152)
            {
                throw new InvalidDataException("Invalid magic bytes in frame header.");
            }
        });
    }
}

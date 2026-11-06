namespace NovaEngine.Consensus.Tests;

using System;
using System.Text;
using NovaEngine.Consensus;
using Xunit;

public class MerkleConsensusEngineTests
{
    [Fact]
    public void Computes_Deterministic_Merkle_Root()
    {
        var txs = new[]
        {
            Encoding.UTF8.GetBytes("TX-1"),
            Encoding.UTF8.GetBytes("TX-2"),
            Encoding.UTF8.GetBytes("TX-3")
        };

        byte[] root1 = MerkleConsensusEngine.ComputeMerkleRoot(txs);
        byte[] root2 = MerkleConsensusEngine.ComputeMerkleRoot(txs);

        Assert.NotNull(root1);
        Assert.Equal(32, root1.Length);
        Assert.True(MerkleConsensusEngine.ValidateConsensus(root1, root2));
    }
}

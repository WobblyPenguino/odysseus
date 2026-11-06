using Xunit;
using NovaEngine.Security.Cng;
using System;

namespace NovaEngine.Security.Tests;

public class CngKeyProviderTests
{
    [Fact]
    public void CngKeyProvider_Initializes_With_Software_Fallback()
    {
        using var provider = new CngIssuerKeyContainer("NON_EXISTENT_TEST_KEY", preferHardware: true);
        Assert.Equal("NON_EXISTENT_TEST_KEY", provider.KeyContainerName);
        Assert.False(provider.AssertAdmissionGate());
    }

    [Fact]
    public void SignHash_Throws_When_Key_Not_Initialized()
    {
        using var provider = new CngIssuerKeyContainer("NON_EXISTENT_TEST_KEY", preferHardware: false);
        byte[] dummyHash = new byte[32];
        var ex = Assert.Throws<InvalidOperationException>(() => provider.SignHash(dummyHash));
        Assert.Contains("CNG issuer key handle is not initialized", ex.Message);
    }
}

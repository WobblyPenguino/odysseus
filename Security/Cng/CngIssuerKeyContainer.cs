#nullable enable
using System;

namespace NovaEngine.Security.Cng;

public interface ICngKeyProvider : IDisposable
{
    bool IsHardwareBacked { get; }
    string KeyContainerName { get; }
    byte[] SignHash(byte[] hash);
    bool AssertAdmissionGate();
}

public class CngIssuerKeyContainer : ICngKeyProvider
{
    private readonly string _keyName;
    private string _providerName;
    private SafeNCryptProviderHandle? _providerHandle;
    private SafeNCryptKeyHandle? _keyHandle;
    private bool _disposed;

    public bool IsHardwareBacked => _providerName == NativeMethods.MS_PLATFORM_KEY_STORAGE_PROVIDER;
    public string KeyContainerName => _keyName;

    public CngIssuerKeyContainer(string keyName = "NOVA_M15_ISSUER_KEY", bool preferHardware = true)
    {
        _keyName = keyName;
        _providerName = preferHardware ? NativeMethods.MS_PLATFORM_KEY_STORAGE_PROVIDER : NativeMethods.MS_KEY_STORAGE_PROVIDER;
        InitializeProviderAndKey();
    }

    private void InitializeProviderAndKey()
    {
        int status = NativeMethods.NCryptOpenStorageProvider(out _providerHandle, _providerName, 0);
        if (status != 0 && IsHardwareBacked)
        {
            _providerName = NativeMethods.MS_KEY_STORAGE_PROVIDER;
            status = NativeMethods.NCryptOpenStorageProvider(out _providerHandle, _providerName, 0);
        }
        if (status != 0) throw new InvalidOperationException($"Failed to open CNG storage provider. Error: 0x{status:X8}");
        status = NativeMethods.NCryptOpenKey(_providerHandle!, out _keyHandle, _keyName, 0, 0);
        if (status != 0) _keyHandle = null;
    }

    public byte[] SignHash(byte[] hash)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (_keyHandle == null || _keyHandle.IsInvalid) throw new InvalidOperationException("CNG issuer key handle is not initialized.");
        var paddingInfo = new BCRYPT_PKCS1_PADDING_INFO { pszAlgId = "SHA256" };
        int status = NativeMethods.NCryptSignHash(_keyHandle, ref paddingInfo, hash, hash.Length, null, 0, out int cbResult, 0x00000002);
        if (status != 0) throw new InvalidOperationException($"Failed to size signature. Error: 0x{status:X8}");
        byte[] signature = new byte[cbResult];
        status = NativeMethods.NCryptSignHash(_keyHandle, ref paddingInfo, hash, hash.Length, signature, signature.Length, out cbResult, 0x00000002);
        if (status != 0) throw new InvalidOperationException($"Failed to sign hash. Error: 0x{status:X8}");
        return signature;
    }

    public bool AssertAdmissionGate() => _providerHandle != null && !_providerHandle.IsInvalid && _keyHandle != null && !_keyHandle.IsInvalid;

    public void Dispose()
    {
        if (!_disposed)
        {
            _keyHandle?.Dispose();
            _providerHandle?.Dispose();
            _disposed = true;
        }
    }
}


#nullable enable
using System;
using System.Runtime.InteropServices;

namespace NovaEngine.Security.Cng;

public static class CngKeyProvisioner
{
    [DllImport("ncrypt.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern int NCryptCreatePersistedKey(
        SafeNCryptProviderHandle hProvider, 
        out SafeNCryptKeyHandle phKey, 
        string pszAlgId, 
        string? pszKeyName, 
        uint dwLegacyKeySpec, 
        uint dwFlags);

    [DllImport("ncrypt.dll", CharSet = CharSet.Unicode, ExactSpelling = true)]
    private static extern int NCryptFinalizeKey(SafeNCryptKeyHandle hKey, uint dwFlags);

    public static bool ProvisionKey(string keyName = "NOVA_M15_ISSUER_KEY", bool preferHardware = true)
    {
        string providerName = preferHardware 
            ? NativeMethods.MS_PLATFORM_KEY_STORAGE_PROVIDER 
            : NativeMethods.MS_KEY_STORAGE_PROVIDER;

        int status = NativeMethods.NCryptOpenStorageProvider(out var providerHandle, providerName, 0);
        if (status != 0 && preferHardware)
        {
            Console.WriteLine($"[M15 Provision] Platform Crypto Provider unavailable (0x{status:X8}). Falling back to Software Provider.");
            providerName = NativeMethods.MS_KEY_STORAGE_PROVIDER;
            status = NativeMethods.NCryptOpenStorageProvider(out providerHandle, providerName, 0);
        }

        if (status != 0)
        {
            Console.Error.WriteLine($"[M15 Provision] Failed to open storage provider. Error: 0x{status:X8}");
            return false;
        }

        using (providerHandle)
        {
            status = NCryptCreatePersistedKey(providerHandle, out var keyHandle, "RSA", keyName, 0, 0x00000080);
            if (status != 0)
            {
                Console.Error.WriteLine($"[M15 Provision] Failed to create persisted key. Error: 0x{status:X8}");
                return false;
            }

            using (keyHandle)
            {
                status = NCryptFinalizeKey(keyHandle, 0);
                if (status != 0)
                {
                    Console.Error.WriteLine($"[M15 Provision] Failed to finalize key. Error: 0x{status:X8}");
                    return false;
                }
            }
        }

        Console.WriteLine($"[M15 Provision] Successfully provisioned key '{keyName}' in '{providerName}'.");
        return true;
    }
}

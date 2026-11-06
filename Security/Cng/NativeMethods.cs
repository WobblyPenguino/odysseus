using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace NovaEngine.Security.Cng;

public sealed class SafeNCryptProviderHandle : SafeHandleZeroOrMinusOneIsInvalid
{
    public SafeNCryptProviderHandle() : base(true) { }
    [DllImport("ncrypt.dll", ExactSpelling = true)]
    private static extern int NCryptFreeObject(IntPtr hObject);
    protected override bool ReleaseHandle() => NCryptFreeObject(handle) == 0;
}

public sealed class SafeNCryptKeyHandle : SafeHandleZeroOrMinusOneIsInvalid
{
    public SafeNCryptKeyHandle() : base(true) { }
    [DllImport("ncrypt.dll", ExactSpelling = true)]
    private static extern int NCryptFreeObject(IntPtr hObject);
    protected override bool ReleaseHandle() => NCryptFreeObject(handle) == 0;
}

[StructLayout(LayoutKind.Sequential)]
public struct BCRYPT_PKCS1_PADDING_INFO
{
    [MarshalAs(UnmanagedType.LPWStr)]
    public string pszAlgId;
}

internal static class NativeMethods
{
    private const string NCRYPT_LIB = "ncrypt.dll";
    public const string MS_KEY_STORAGE_PROVIDER = "Microsoft Software Key Storage Provider";
    public const string MS_PLATFORM_KEY_STORAGE_PROVIDER = "Microsoft Platform Crypto Provider";

    [DllImport(NCRYPT_LIB, CharSet = CharSet.Unicode, ExactSpelling = true)]
    public static extern int NCryptOpenStorageProvider(out SafeNCryptProviderHandle phProvider, string pszProviderName, uint dwFlags);

    [DllImport(NCRYPT_LIB, CharSet = CharSet.Unicode, ExactSpelling = true)]
    public static extern int NCryptOpenKey(SafeNCryptProviderHandle hProvider, out SafeNCryptKeyHandle phKey, string pszKeyName, uint dwLegacyKeySpec, uint dwFlags);

    [DllImport(NCRYPT_LIB, CharSet = CharSet.Unicode, ExactSpelling = true)]
    public static extern int NCryptSignHash(SafeNCryptKeyHandle hKey, ref BCRYPT_PKCS1_PADDING_INFO pPaddingInfo, byte[] pbHashValue, int cbHashValue, byte[] pbSignature, int cbSignature, out int pcbResult, uint dwFlags);
}

using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using NovaEngine.Logging;
using Xunit;

public class MmfLogBufferTests : IDisposable
{
    private readonly string _testFilePath = Path.Combine(Path.GetTempPath(), "test_nova_lane.log");

    public MmfLogBufferTests()
    {
        if (File.Exists(_testFilePath)) File.Delete(_testFilePath);
    }

    [Fact]
    public void Can_Write_And_Persist_Single_Entry()
    {
        using var buffer = new MmfLogBuffer(_testFilePath, 1024 * 1024);
        byte[] payload = Encoding.UTF8.GetBytes("Genesis-Block-Hash-M21");

        long position = buffer.WriteEntry(payload);

        Assert.True(position >= sizeof(long));
        Assert.True(File.Exists(_testFilePath));
    }

    [Fact]
    public async Task Can_Handle_Concurrent_High_Throughput_Writes()
    {
        using var buffer = new MmfLogBuffer(_testFilePath, 50 * 1024 * 1024);
        int taskCount = 10;
        int iterationsPerTask = 1000;

        var tasks = new Task[taskCount];
        for (int i = 0; i < taskCount; i++)
        {
            int taskId = i;
            tasks[i] = Task.Run(() =>
            {
                for (int j = 0; j < iterationsPerTask; j++)
                {
                    byte[] data = Encoding.UTF8.GetBytes($"Lane-{taskId}-Tx-{j}");
                    buffer.WriteEntry(data);
                }
            });
        }

        await Task.WhenAll(tasks);

        var fileInfo = new FileInfo(_testFilePath);
        Assert.True(fileInfo.Length > 0);
    }

    public void Dispose()
    {
        if (File.Exists(_testFilePath))
        {
            try { File.Delete(_testFilePath); } catch {}
        }
    }
}

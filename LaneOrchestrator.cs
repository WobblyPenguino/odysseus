using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;

namespace NovaEngine.Orchestration
{
    public class LaneOrchestrator : IAsyncDisposable
    {
        private readonly ConcurrentDictionary<string, CancellationTokenSource> _activeLanes = new();
        private readonly Channel<TransactionItem> _transactionPipeline;
        private readonly int _maxLanes;
        private int _currentLaneCount;

        public LaneOrchestrator(int maxLanes = 8, int capacity = 10000)
        {
            _maxLanes = maxLanes;
            
            var options = new BoundedChannelOptions(capacity)
            {
                FullMode = BoundedChannelFullMode.Wait
            };
            _transactionPipeline = Channel.CreateBounded<TransactionItem>(options);
        }

        public async Task<bool> ProvisionLaneAsync(string laneId, CancellationToken cancellationToken)
        {
            if (_activeLanes.Count >= _maxLanes)
            {
                return false;
            }

            var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            if (_activeLanes.TryAdd(laneId, cts))
            {
                Interlocked.Increment(ref _currentLaneCount);
                _ = Task.Run(() => ExecuteLaneAsync(laneId, cts.Token), cts.Token);
                return await Task.FromResult(true);
            }

            return false;
        }

        public async Task DeprovisionLaneAsync(string laneId)
        {
            if (_activeLanes.TryRemove(laneId, out var cts))
            {
                cts.Cancel();
                cts.Dispose();
                Interlocked.Decrement(ref _currentLaneCount);
                await Task.CompletedTask;
            }
        }

        public async ValueTask SubmitTransactionAsync(TransactionItem item, CancellationToken cancellationToken)
        {
            await _transactionPipeline.Writer.WriteAsync(item, cancellationToken);
        }

        private async Task ExecuteLaneAsync(string laneId, CancellationToken cancellationToken)
        {
            try
            {
                while (!cancellationToken.IsCancellationRequested)
                {
                    while (_transactionPipeline.Reader.TryRead(out var item))
                    {
                        ProcessItem(laneId, item);
                    }

                    await Task.Delay(10, cancellationToken);
                }
            }
            catch (OperationCanceledException) {}
        }

        private void ProcessItem(string laneId, TransactionItem item)
        {
            Console.WriteLine($"[Lane {laneId}] Processed transaction {item.Id}");
        }

        public async ValueTask DisposeAsync()
        {
            _transactionPipeline.Writer.Complete();
            foreach (var kvp in _activeLanes)
            {
                kvp.Value.Cancel();
                kvp.Value.Dispose();
            }
            _activeLanes.Clear();
            await Task.CompletedTask;
        }
    }

    public record TransactionItem(string Id, byte[] Payload, DateTime Timestamp);
}

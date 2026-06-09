import threading
import time
from winlocalassistant.performance_tuning import apply_startup_performance_environment

apply_startup_performance_environment()

from winlocalassistant.main import main

# NOVA_THINKING_TIMER_PATCH
def _nova_run_with_thinking_timer(fn, *args, wait_sec=5.0, **kwargs):
    """Run a blocking Nova call and show elapsed thinking time after a short wait."""
    started = time.perf_counter()
    done = threading.Event()

    def _ticker():
        shown = False
        while not done.wait(0.25):
            elapsed = time.perf_counter() - started
            if elapsed >= wait_sec and not shown:
                print(f"\nNova is thinking... {elapsed:.1f}s elapsed", flush=True)
                shown = True

    thread = threading.Thread(target=_ticker, daemon=True)
    thread.start()
    try:
        return fn(*args, **kwargs)
    finally:
        done.set()
        elapsed = time.perf_counter() - started
        if elapsed >= wait_sec:
            print(f"\nThinking time: {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()

# NOVA_THINKING_TIMER_PATCH_NOTE:
# Timer helper installed. If app.py uses a different dispatch call, wrap that call as:
# response = _nova_run_with_thinking_timer(core.handle_command, user_text)

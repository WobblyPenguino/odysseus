<#
Nova desktop voice launcher helper.

Purpose:
- Browser SpeechRecognition can only listen while the Nova browser page is open and mic permission is allowed.
- This Windows helper runs outside the browser and listens for a tiny grammar such as
  "hey nova", "nova start", "launch nova", or "open nova".
- When heard, it launches start_windows_assistant.bat in Browser UI mode by setting NOVA_START_CHOICE=2.

Notes:
- Uses Windows System.Speech when available. Run from Windows PowerShell.
- Keep this in your Startup folder if you want it available after logging in.
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $root 'start_windows_assistant.bat'
$url = 'http://127.0.0.1:8766'

function Say-Nova([string]$Text) {
    try {
        $voice = New-Object -ComObject SAPI.SpVoice
        $null = $voice.Speak($Text, 1)
    } catch {
        Write-Host $Text
    }
}

function Start-NovaGui {
    if (!(Test-Path $bat)) {
        Say-Nova "Nova launcher could not find the Nova start file."
        return
    }
    Say-Nova "Nova is starting. I will open the browser interface."
    $env:NOVA_START_CHOICE = '2'
    Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', 'set NOVA_START_CHOICE=2&&', ('"' + $bat + '"')) -WorkingDirectory $root -WindowStyle Normal
    Start-Sleep -Seconds 3
    try { Start-Process $url } catch {}
}

try {
    Add-Type -AssemblyName System.Speech
    $recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
    $choices = New-Object System.Speech.Recognition.Choices
    @('hey nova','hay nova','okay nova','ok nova','nova start','start nova','launch nova','open nova','wake nova') | ForEach-Object { [void]$choices.Add($_) }
    $grammarBuilder = New-Object System.Speech.Recognition.GrammarBuilder
    $grammarBuilder.Culture = $recognizer.RecognizerInfo.Culture
    [void]$grammarBuilder.Append($choices)
    $grammar = New-Object System.Speech.Recognition.Grammar($grammarBuilder)
    $recognizer.LoadGrammar($grammar)
    $recognizer.SetInputToDefaultAudioDevice()
    Register-ObjectEvent -InputObject $recognizer -EventName SpeechRecognized -Action {
        $text = $EventArgs.Result.Text
        $confidence = $EventArgs.Result.Confidence
        if ($confidence -ge 0.45) {
            Write-Host ("Heard {0} confidence {1:N2}; launching Nova" -f $text, $confidence)
            Start-NovaGui
        } else {
            Write-Host ("Ignored low-confidence phrase {0} confidence {1:N2}" -f $text, $confidence)
        }
    } | Out-Null
    Say-Nova "Nova desktop listener is ready. Say hey nova, start nova, or launch nova."
    Write-Host "Nova desktop voice listener running. Press Ctrl+C to stop."
    $recognizer.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)
    while ($true) { Start-Sleep -Seconds 1 }
} catch {
    Write-Host "Desktop voice listener failed: $($_.Exception.Message)"
    Write-Host "You can still launch Nova normally with start_windows_assistant.bat."
    Say-Nova "Nova desktop listener could not start. Open Nova normally."
}

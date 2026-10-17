# Capture visible text from all Loginom windows/dialogs.
# Prefer Win32 titles + UI Automation text.
# Output blocks separated by --- .

$ErrorActionPreference = 'SilentlyContinue'

$pids = @(Get-Process loginom -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
if ($pids.Count -eq 0) { exit 0 }

Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class LoginomWinEnum {
  public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lp);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr hWnd, EnumProc cb, IntPtr lp);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  public static List<string> TitlesForPids(HashSet<uint> pids) {
    var found = new List<string>();
    EnumWindows((h, lp) => {
      uint pid; GetWindowThreadProcessId(h, out pid);
      if (!pids.Contains(pid) || !IsWindowVisible(h)) return true;
      int len = GetWindowTextLength(h);
      if (len <= 0) return true;
      var sb = new StringBuilder(len + 1);
      GetWindowText(h, sb, sb.Capacity);
      var t = sb.ToString().Trim();
      if (t.Length > 0) found.Add("WINTITLE: " + t);
      EnumChildWindows(h, (ch, lp2) => {
        int cl = GetWindowTextLength(ch);
        if (cl <= 0) return true;
        var csb = new StringBuilder(cl + 1);
        GetWindowText(ch, csb, csb.Capacity);
        var ct = csb.ToString().Trim();
        if (ct.Length > 0) found.Add(ct);
        return true;
      }, IntPtr.Zero);
      found.Add("---");
      return true;
    }, IntPtr.Zero);
    return found;
  }
}
"@ | Out-Null

$pidSet = New-Object 'System.Collections.Generic.HashSet[uint]'
foreach ($p in $pids) { [void]$pidSet.Add([uint]$p) }
[LoginomWinEnum]::TitlesForPids($pidSet) | ForEach-Object { Write-Output $_ }

try {
    Add-Type -AssemblyName UIAutomationClient | Out-Null
    Add-Type -AssemblyName UIAutomationTypes | Out-Null
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $winCond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Window
    )
    $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $winCond)
    foreach ($w in $windows) {
        $pid = 0
        try { $pid = $w.Current.ProcessId } catch { continue }
        if ($pids -notcontains $pid) { continue }
        $title = ""
        try { $title = $w.Current.Name } catch {}
        Write-Output ("UIA_WINDOW: " + $title)
        $texts = New-Object System.Collections.Generic.List[string]
        try {
            $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
            $stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
            $stack.Push($w)
            $n = 0
            while ($stack.Count -gt 0 -and $n -lt 500) {
                $el = $stack.Pop()
                $n++
                try {
                    $ct = $el.Current.ControlType
                    $nm = $el.Current.Name
                    if (-not [string]::IsNullOrWhiteSpace($nm)) {
                        if ($ct -eq [System.Windows.Automation.ControlType]::Text -or
                            $ct -eq [System.Windows.Automation.ControlType]::Document -or
                            $ct -eq [System.Windows.Automation.ControlType]::Edit -or
                            $ct -eq [System.Windows.Automation.ControlType]::Hyperlink -or
                            $ct -eq [System.Windows.Automation.ControlType]::ListItem -or
                            $ct -eq [System.Windows.Automation.ControlType]::Custom -or
                            $ct -eq [System.Windows.Automation.ControlType]::Pane) {
                            if (-not $texts.Contains($nm)) { [void]$texts.Add($nm) }
                        }
                    }
                    $child = $walker.GetFirstChild($el)
                    while ($null -ne $child) {
                        $stack.Push($child)
                        $child = $walker.GetNextSibling($child)
                    }
                } catch { continue }
            }
        } catch {}
        foreach ($t in $texts) { Write-Output $t }
        Write-Output "---"
    }
} catch {
    Write-Output ("UIA_ERROR: " + $_.Exception.Message)
}

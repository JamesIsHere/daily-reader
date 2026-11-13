# Fire one Windows toast from a prebuilt XML payload file (UTF-8).
# Called by cycle.py; keep this file ASCII-only for PS 5.1.
param([Parameter(Mandatory=$true)][string]$XmlPath)

$null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml([System.IO.File]::ReadAllText($XmlPath))
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml

# PowerShell's registered AppUserModelID -- toasts display as "Windows PowerShell".
# Good enough for v1; the notification channel is an iterate-over-time question.
$appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)

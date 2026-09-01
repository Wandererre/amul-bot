Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "python bot.py", 0, False
MsgBox "Amul Stock Tracker is now running silently in the background!" & vbCrLf & "To stop it anytime, run stop_background.bat", 64, "Amul Stock Bot"

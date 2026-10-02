-- Recalculate a model copy in Excel and save it. Excel's sandbox can't open /private/tmp: copy the file to ~/Downloads first
-- (e.g. ~/Downloads/_recalc_vNN.xlsx), edit the name below, run: osascript recalc.applescript
-- Never touch other open workbooks (Alex keeps the model open from SharePoint); close only this one, by exact name.
with timeout of 1800 seconds
tell application "Microsoft Excel"
	open (POSIX file "/Users/suprunov/Downloads/_recalc_v16.xlsx")
end tell
repeat 120 times
	tell application "Microsoft Excel" to set nms to name of workbooks
	if nms contains "_recalc_v16.xlsx" then exit repeat
	delay 2
end repeat
tell application "Microsoft Excel"
	set wb to workbook "_recalc_v16.xlsx"
	calculate full
	save wb
	close wb saving no
end tell
end timeout
return "ok"

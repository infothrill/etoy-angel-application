-- volumeExists checks if the given disk exists
on volumeExists(diskname)
	tell application "Finder"
		if exists disk diskname then
			return true
		else
			return false
		end if
	end tell
end volumeExists

-- showVolume opens a Finder window with the given volume
on showVolume(diskname)
	tell application "Finder"
		if exists disk diskname then
			reveal disk diskname
			select disk diskname
			activate
			--make new Finder window to disk diskname
		else
			display dialog "Could not open disk '" & diskname & "' in a Finder window, disk does not exist"
		end if
	end tell
end showVolume

-- mountVolume attempts to mount the given volume
on mountVolume(volspec)
	tell application "Finder"
		try
			mount volume volspec
		on error
			display dialog "There was an error mounting the repository." & return & return & Â
				"Try restarting Angel-App or wait some seconds and try again." buttons {"Okay"} default button 1
		end try
	end tell
end mountVolume

-- MAIN
on run argv
	set hostname to item 1 of argv
	set portnumber to item 2 of argv
	--set hostname to "localhost"
	--set portnumber to "6222"
	if not volumeExists(hostname) then
		mountVolume("http://" & hostname & ":" & portnumber)
	end if
	if volumeExists(hostname) then
		showVolume(hostname)
	end if
end run

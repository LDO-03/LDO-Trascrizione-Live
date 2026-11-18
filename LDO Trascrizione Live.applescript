property titolo : "LDO Trascrizione Live"

on run
	try
		set r to display dialog "Titolo della conferenza o dell'intervista:" with title titolo default answer "" buttons {"Annulla", "Avanti"} default button "Avanti"
	on error
		return
	end try
	set nomeConf to text returned of r
	if nomeConf is "" then set nomeConf to "Conferenza"

	try
		set r2 to display dialog "Autorizzi l'ascolto del microfono e la trascrizione di questa conferenza?" & return & return & "Assicurati che relatori e organizzatori siano d'accordo." with title titolo buttons {"No", "Autorizzo"} default button "Autorizzo" with icon caution
	on error
		return
	end try
	if button returned of r2 is not "Autorizzo" then return

	set shPath to (POSIX path of (path to me)) & "Contents/Resources/avvia.sh"
	set cmd to "/bin/bash " & quoted form of shPath & " " & quoted form of nomeConf
	tell application "Terminal"
		activate
		set tabNuova to do script cmd
		set background color of tabNuova to {0, 0, 0}
		set normal text color of tabNuova to {0, 65535, 0}
		set cursor color of tabNuova to {0, 65535, 0}
		set font name of tabNuova to "Menlo"
		set font size of tabNuova to 16
	end tell
end run

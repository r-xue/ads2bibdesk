
# https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/UsetheSystem-WideScriptMenu.html
set savedClipboard to the clipboard
do shell script ("ads2bibdesk -d " & savedClipboard)

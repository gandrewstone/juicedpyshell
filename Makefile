VERSION = 0.7

default: pyshell_$(VERSION).xpi

components/pyIShell.xpt: components/pyIShell.idl
	/opt/komodo/Komodo-IDE-4.2.0/lib/sdk/bin/xpidl -I /opt/komodo/Komodo-IDE-4.2.0/lib/sdk/idl -I components -o components/pyIShell -m typelib components/pyIShell.idl

pyshell_$(VERSION).xpi: components/* content/* locale/*/* install.rdf chrome.manifest LICENSE.txt
	zip pyshell.jar -r content locale
	zip pyshell_$(VERSION).xpi LICENSE.txt install.rdf chrome.manifest pyshell.jar -r components
	rm pyshell.jar


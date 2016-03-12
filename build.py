import json
import py_compile
import zipfile
import os
f=json.loads(open("build.json","r").read())
with zipfile.ZipFile('build/StatsInBattle_v{version}.zip'.format(version=f['Version']), 'w', zipfile.ZIP_DEFLATED) as myzip:
    for file in f["files"]:
        file=file.format(VersionWOT=f['VersionWOT'])
        if file[len(file)-1]=="*":
            for top, dirs, files in os.walk(file.replace("*","")):
                for nm in files:
                    if nm != "Thumbs.db":
                        myzip.write(os.path.join(top, nm))
        elif file[len(file)-3:]==".py":
            py_compile.compile(file)
            myzip.write(file+"c")
            os.remove(file+"c")
        else:
            myzip.write(file)


import json
import py_compile
import zipfile
import os

cfg = json.load(open('build.json', 'r'))

with zipfile.ZipFile('build\\StatsInBattle_v{version}.zip'.format(version=cfg['Version']), 'w', zipfile.ZIP_DEFLATED) as myzip:
    for file in cfg['files']:
        file = file.format(VersionWOT=cfg['VersionWOT'])
        if file[-1] == '*':
            for top, dirs, files in os.walk(file.replace('*', '')):
                for nm in files:
                    if nm != 'Thumbs.db':
                        myzip.write(os.path.join(top, nm))
        elif file[-3:] == '.py':
            py_compile.compile(file)
            myzip.write(file+'c')
            os.remove(file+'c')
        else:
            myzip.write(file)

# -*- mode: python -*-
a = Analysis(['ltmodbus_logger.py'],
             pathex=[],
             hiddenimports=[],
             hookspath=None)

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'ltmodbus_logger.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=True)

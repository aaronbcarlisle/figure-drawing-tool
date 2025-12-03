# -*- mode: python -*-

block_cipher = None

a = Analysis(['figure_drawing_tool.py'],
             pathex=['.'],
             binaries=None,
             datas=[
                 ('start_image.jpg', '.'),
                 ('dark.qss', '.'),
             ],
             hiddenimports=[
                 'PySide6.QtCore',
                 'PySide6.QtGui',
                 'PySide6.QtWidgets',
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='figure_drawing_tool',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='figure_drawing_tool_icon.ico')

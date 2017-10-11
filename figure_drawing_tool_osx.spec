# -*- mode: python -*-

block_cipher = None


a = Analysis(['figure_drawing_tool.py'],
             pathex=['/figure_drawing_tool'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)


a.datas += [ ('start_image.jpg', 'start_image.jpg', 'DATA')]
a.datas += [ ('dark.qss', 'dark.qss', 'DATA')]

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
          console=False , icon='figure_drawing_tool_icon.icns')
app = BUNDLE(exe,
             name='figure_drawing_tool.app',
             icon='figure_drawing_tool_icon.icns',
             bundle_identifier=None)

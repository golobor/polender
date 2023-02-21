# polender

Useful CLI commands:
- run blender in MacOS CLI:
  ```
  /Applications/Blender.app/Contents/MacOS/Blender
  ```
- instal pip packages:
  ```
  /Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "__import__('pip._internal')._internal.main(['install', 'IPython'])"
  ```
- run blender with IPython
  ```
  /Applications/Blender.app/Contents/MacOS/Blender --python-expr '__import__("threading").Timer(0, __import__("IPython").embed).start()'
  ```

Useful blender python commands:
- use opened scripts as modules in the Python console:
  ```
  mymod = bpy.data.texts[0].as_module()
  ```

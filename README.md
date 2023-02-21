# polender

Useful commands:
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

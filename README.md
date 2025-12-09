# Figure Drawing Tool
<img width="526" height="913" alt="image" src="https://github.com/user-attachments/assets/17b5c643-4649-474f-86b8-f8e96b351d62" />

## Using the Spec Files
I use [pyinstaller](https://pyinstaller.org/en/stable/) to compile the apps. Unfortunately, in order to compile per OS you actually need to be on that os (a Virtual Box works just fine).

### With the spec files all you need to do is run:

```codeowners
pyinstaller figure_drawing_tool_win.spec
```
OR

```codeowners
pyinstaller figure_drawing_tool_osx.spec
```

This'll build a build environment and compile the tool into an executable or an app. The resulted file is in the dist directory.

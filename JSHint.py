import sublime, sublime_plugin
import os, re

try:
  import commands
except ImportError:
  import subprocess

PLUGIN_FOLDER = os.path.dirname(os.path.realpath(__file__))

class JshintCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    filePath = self.view.file_name()

    # Make sure we're only linting javascript files.
    if filePath != None and not re.search(r'\.jsm?$', filePath):
      return

    packageName = PLUGIN_FOLDER.replace(sublime.packages_path(), "")
    scriptPath = PLUGIN_FOLDER + "/scripts/run.js"
    setings = " && ".join([
      # To add persistent options that are used everywhere, edit the .jshintrc
      # file inside the scripts folder. But you can als add some options here
      # if you like. For example:
      # "browser: true",
      # "esnext: true",
      # "moz: true"
    ])

    # Get the current text in the buffer.
    bufferText = self.view.substr(sublime.Region(0, self.view.size()))

    # ...and save it in a temporary file. This allows for scratch buffers
    # and dirty files to be linted as well.
    tempName = ".__temp__"
    tempPath = PLUGIN_FOLDER + '/' + tempName
    f = open(tempPath, 'w')
    f.write(bufferText)
    f.close()

    node = "node" if self.exists_in_path("node") else "/usr/local/bin/node"
    cmd = [node, scriptPath, tempPath, filePath or "?", setings]

    output = ""
    try:
      # Sublime Text 2.
      if sublime.platform() != "windows":
        # Handle Linux and OS X in Python 2.
        run = '"' + '" "'.join(cmd) + '"'
        output = commands.getoutput(run)
      else:
        # Handle Windows in Python 2.
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    except:
      # Sublime Text 3, Python 3.
      run = '"' + '" "'.join(cmd) + '"'
      output = subprocess.check_output(run, stderr=subprocess.STDOUT, shell=True)

    # We're done with linting, remove the temporary file and rebuild the
    # regions shown in the current view.
    os.remove(tempPath)
    self.view.erase_regions("jshint_errors");

    if len(output) > 0:
      regions = []
      menuitems = []

      # For each line of jshint output (errors, warnings etc.) add a region
      # in the view and a menuitem in a quick panel.
      for line in output.decode().splitlines():
        try:
          lineNo, columnNo, description = line.split(" :: ")
          point = self.view.text_point(int(lineNo) - 1, int(columnNo))
          word = self.view.word(point)
          menuitems.append(lineNo + ":" + columnNo + " " + description)
          regions.append(word)
        except:
          pass

      if int(sublime.version()) >= 3000:
        icon = "Packages/" + packageName + "/warning.png"
        self.view.add_regions("jshint_errors", regions, "keyword", icon,
          sublime.DRAW_EMPTY |
          sublime.DRAW_NO_FILL |
          sublime.DRAW_NO_OUTLINE |
          sublime.DRAW_SQUIGGLY_UNDERLINE)
      else:
        icon = ".." + packageName + "/warning"
        self.view.add_regions("jshint_errors", regions, "keyword", icon,
          sublime.DRAW_EMPTY |
          sublime.DRAW_OUTLINED |
          sublime.HIDE_ON_MINIMAP)

      sublime.active_window().show_quick_panel(menuitems, self.on_chosen)

  def on_chosen(self, index):
    if index == -1:
      return

    # Focus the user requested region from the quick panel.
    region = self.view.get_regions("jshint_errors")[index]
    selection = self.view.sel()
    selection.clear()
    selection.add(region)
    self.view.show(region)

  def exists_in_path(self, cmd):
    # Can't search the path if a directory is specified.
    assert not os.path.dirname(cmd)
    path = os.environ.get("PATH", "").split(os.pathsep)
    extensions = os.environ.get("PATHEXT", "").split(os.pathsep)

    # For each directory in PATH, check if it contains the specified binary.
    for directory in path:
      base = os.path.join(directory, cmd)
      options = [base] + [(base + ext) for ext in extensions]
      for filename in options:
        if os.path.exists(filename):
          return True

    return False

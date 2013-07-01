import commands
import sublime, sublime_plugin

class JshintCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    scriptPath = sublime.packages_path() + "/Sublime-JSHint/scripts/run.js"
    filePath = self.view.file_name()
    setings = ' && '.join([
      "browser: true",
      "node: true",
      "esnext: true",
      "moz: true",
      "globalstrict: true",
      "trailing: true",
      "undef: true",
      "unused: true",
      "smarttabs: true"
    ])

    cmd = ["/usr/local/bin/node", scriptPath, filePath, setings]
    output = commands.getoutput('"' + '" "'.join(cmd) + '"')

    self.view.erase_regions("jshint_errors");

    if len(output) > 0:
      regions = []
      menuitems = []

      for line in output.splitlines():
        try:
          data = line.split(":")
          line = int(data[1]) - 1
          column = int(data[2])
          point = self.view.text_point(line, column)
          word = self.view.word(point)
          menuitems.append(data[1] + ":" + data[2] + " " + data[3])
          regions.append(word)
        except:
          pass

      self.view.add_regions("jshint_errors", regions, " ", "cross")
      sublime.active_window().show_quick_panel(menuitems, self.on_chosen)
      print output

  def on_chosen(self, index):
    if index == -1:
      return

    region = self.view.get_regions("jshint_errors")[index]
    selection = self.view.sel()
    selection.clear()
    selection.add(region)
    self.view.show(region)

import sublime
import sublime_plugin
import time
import subprocess

AUTHOR = ""
EMAIL = ""


def make_comment(depth=1):
    """
    Returns a string using the values from `config()` for a comment of depth
    `depth`.
    """
    depth = max(depth, 1)
    header = '#' + '*' * depth
    body = '#' + '-' * depth

    proc = subprocess.Popen(
        'git config user.name', shell=True, stdout=subprocess.PIPE)
    AUTHOR, error = proc.communicate()
    proc = subprocess.Popen(
        'git config user.email', shell=True, stdout=subprocess.PIPE)
    EMAIL, error = proc.communicate()
    fields = {'author': AUTHOR[:-1].decode(
        "utf-8"), 'email': EMAIL[:-1].decode("utf-8")}
    fields['date'] = time.strftime('%Y-%m-%dT%T%z')

    lines = [header]
    for field_name in ['author', 'email', 'date']:
        field_value = fields.get(field_name, 'Unknown')
        lines.append('%s %s: %s' % (header, field_name, field_value))
    lines.extend([header, body + ' ', body])
    return lines


class ShowLocalSourceCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        row, col = self.view.rowcol(self.view.sel()[0].begin())
        file_name = self.view.file_name()
        cmd = 'diffscuss find-local -i %s %s' % (file_name, row)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output, error = proc.communicate()
        file_name, line = output.decode('utf8').split(" ")
        self.view.window().open_file("%s:%s" %
                        (file_name, line), sublime.ENCODED_POSITION)


class MakeCommentCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        row = self.view.line(self.view.sel()[0].begin()).a
        comment = '\n'.join(make_comment()).strip()
        self.view.insert(edit, row, comment + "\n")


class FindNextCommentCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        region = self.view.find('#\*', self.view.sel()[0].end())
        region = self.view.find('#-', region.end())
        self.view.show(region)
        self.view.sel().clear()
        self.view.sel().add(region)


class MailboxDoneCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        file_name = self.view.file_name()
        cmd = 'diffscuss mailbox done -p %s' % (file_name)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output, error = proc.communicate()
        window = sublime.active_window()
        window.show_quick_panel(
            ["File deleted"], None, sublime.MONOSPACE_FONT)


class MailboxPostCommand(sublime_plugin.TextCommand):

    def _on_done(self, name):
        file_name = self.view.file_name()
        cmd = 'diffscuss mailbox post -p %s %s' % (file_name, name)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output, error = proc.communicate()
        window = sublime.active_window()
        window.show_quick_panel(
            ["File posted to %s" % name], None, sublime.MONOSPACE_FONT)

    def run(self, edit):
        sublime.active_window().show_input_panel(
            "Post to who?", 'name', self._on_done, None, None)


class DiffscussGenerateCommand(sublime_plugin.TextCommand):

    def _on_done_commits(self, commits):
        self.commits = commits
        sublime.active_window().show_input_panel(
            "review file name", 'review_name', self._on_done_filename, None, None)

    def _on_done_filename(self, file_name):
        settings = sublime.load_settings('Diffscuss.sublime-settings')
        file_dir = "%s/codereview/reviews/%s.cr" % (settings.get('project_folder'), file_name)
        cmd = 'diffscuss generate %s >> %s' % (
            self.commits, file_dir)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output, error = proc.communicate()
        self.view.window().open_file(file_dir)

    def run(self, edit):
        sublime.active_window().show_input_panel(
            "diff message", 'HEAD^..HEAD [-- file_to_review]', self._on_done_commits, None, None)

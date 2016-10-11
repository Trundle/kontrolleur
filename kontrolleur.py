import sys
from itertools import islice

import attr
from curtsies import CursorAwareWindow, Input, FSArray
from curtsies.fmtfuncs import dark, invert, magenta, red


@attr.s
class Position:
    row = attr.ib()
    column = attr.ib()

    def __getitem__(self, key):
        return attr.astuple(self)[key]


class Prompt:
    KEY_TRANSLATIONS = {
        "<SPACE>": " "
    }

    def __init__(self, window, input_generator, finder):
        self._window = window
        self._input = input_generator
        self._finder = finder
        self.current_match = None
        self._search_text = ""
        self._output = FSArray(2, window.width)
        self._prompt_start_line = 1
        self._init_prompt()

    def run(self):
        self.redraw()
        for event in self._input:
            if event in {"<ESC>", "<Ctrl-g>"}:
                self.current_match = None
                break
            elif event == "<BACKSPACE>":
                self._delete_last_char()
            elif (isinstance(event, str)
                  and not event.startswith("<") or event in self.KEY_TRANSLATIONS):
                self._add_char(self.KEY_TRANSLATIONS.get(event, event))
            elif event == "<Ctrl-r>":
                self._update_with_next_match()
            else:
                break
            self.redraw()
        return self.current_match

    def redraw(self):
        self._window.render_to_terminal(self._output, self._cursor_pos)

    def _init_prompt(self):
        prompt_msg = dark("bck-i-search: ")
        self._output[0, 0:prompt_msg.width] = [prompt_msg]
        self._cursor_pos = Position(row=0, column=prompt_msg.width)

    def _add_char(self, char):
        self._search_text += char
        current_index = self._cursor_pos.column
        self._output[0, current_index] = char
        self._cursor_pos.column += 1
        self._finder.reset_search_text(self._search_text)
        self._update_with_next_match()

    def _delete_last_char(self):
        if self._search_text:
            self._search_text = self._search_text[:-1]
            self._cursor_pos.column -= 1
            self._output[0, self._cursor_pos.column] = " "
            self._finder.reset_search_text(self._search_text)
            self._update_with_next_match()

    def _update_with_next_match(self):
        entry = self._finder.next()
        if entry is not None:
            lines = list(wrap_lines(entry.splitlines(), self._window.width))
            (term_height, _) = self._window.get_term_hw()
            if len(lines) + 1 > term_height:
                lines = lines[:term_height - 1]
                lines[-1] = "…"
            if len(lines) + 1 != self._output.shape[0]:
                self._resize_output(len(lines) + 1)
            for (lineno, line) in enumerate(lines, 1):
                line = self._highlight_match(line)
                self._output[lineno, 0:] = [line.ljust(self._window.width)]
            color = lambda x: x
        else:
            color = red
        end_column = self._cursor_pos.column
        start_column = end_column - len(self._search_text)
        self._output[0, start_column:end_column] = [color(self._search_text)]
        self.current_match = entry

    def _resize_output(self, number_of_rows):
        old_output = self._output
        self._output = FSArray(number_of_rows, self._window.width)
        for (lineno, line) in enumerate(islice(old_output, number_of_rows)):
            self._output[lineno] = line

    def _highlight_match(self, line):
        start_index = line.find(self._search_text)
        if start_index >= 0:
            return (
                line[:start_index]
                + invert(magenta(self._search_text))
                + line[start_index + len(self._search_text):])
        return line


def wrap_lines(lines, max_length):
    for line in lines:
        while len(line) > max_length:
            yield line[:max_length]
            line = line[max_length:]
        yield line


class SearchStrategy:
    def __init__(self, history, *, search_text=""):
        self.history = history
        self.search_text = search_text
        self._reset_iter()

    def next(self):
        for entry in self._iter:
            if self.search_text in entry:
                return entry

    def reset_search_text(self, new_search_text):
        self.search_text = new_search_text
        self._reset_iter()

    def _reset_iter(self):
        self._iter = iter(self.history)


def main():
    entries = list(sys.stdin)
    finder = SearchStrategy(entries)
    with open("/dev/tty", "r") as tty_in, \
         CursorAwareWindow(in_stream=tty_in, hide_cursor=False) as window, \
         Input(in_stream=tty_in) as input_generator:
        prompt = Prompt(window, input_generator, finder)
        match = prompt.run()
    if match is not None:
        print(match)


if __name__ == "__main__":
    main()
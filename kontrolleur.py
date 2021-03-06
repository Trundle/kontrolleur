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


def _identity(x):
    return x


class Prompt:
    KEY_TRANSLATIONS = {
        "<SPACE>": " "
    }
    CURSOR_OFFSETS = {
        "<LEFT>": lambda offset: offset - 1,
        "<RIGHT>": lambda offset: offset + 1,
        "<HOME>": lambda _: 0,
        # Simply a large enough number. fish then makes sure the cursor is
        # placed at the end
        "<END>": lambda _: 2 ** 16,
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
        execute = False
        cursor_offset_modifier = _identity
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
            elif event in {"<Ctrl-j>", "<Ctrl-m>"}:
                execute = True
                break
            else:
                cursor_offset_modifier = self.CURSOR_OFFSETS.get(event, _identity)
                break
            self.redraw()
        if self.current_match:
            cursor_pos = cursor_offset_modifier(self._finder.index(self.current_match))
        else:
            cursor_pos = 0
        return (self.current_match, execute, cursor_pos)

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
                line = self._finder.highlight_match(line)
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


def wrap_lines(lines, max_length):
    for line in lines:
        while len(line) > max_length:
            yield line[:max_length]
            line = line[max_length:]
        yield line


class SearchStrategy:
    def __init__(self, history, *, search_text=""):
        self.history = history
        self.reset_search_text(search_text)

    def next(self):
        for entry in self._iter:
            if self.search_text in entry.lower():
                return entry

    def reset_search_text(self, new_search_text):
        self.search_text = new_search_text.lower()
        self._reset_iter()

    def index(self, match):
        """Returns the start index of the current search text in `match`.
        """
        return match.lower().find(self.search_text)

    def highlight_match(self, match):
        start_index = match.lower().find(self.search_text)
        if start_index >= 0:
            end_index = start_index + len(self.search_text)
            return (
                match[:start_index]
                + invert(magenta(match[start_index:end_index]))
                + match[end_index:])
        return match

    def _reset_iter(self):
        self._iter = iter(self.history)


class _ReusableIter:
    """An iterable that yields all elements from the given iterable and also
    memorizes them. Requesting a new iterator returns an iterator that yields
    all elements again.

    """
    def __init__(self, iterable):
        self._iter = iterable
        self._entries = []

    def __iter__(self):
        for item in self._entries:
            yield item
        for item in self._iter:
            self._entries.append(item)
            yield item


def parse_entries(lines_iter):
    lines = []
    for line in lines_iter:
        while line:
            (command_part, sep, line) = line.partition("\x00")
            lines.append(command_part)
            if sep == "\x00":
                yield "".join(lines)
                lines = []


def main():
    entries = _ReusableIter(parse_entries(sys.stdin))
    finder = SearchStrategy(entries)
    with open("/dev/tty", "r") as tty_in, \
         open("/dev/tty", "w") as tty_out, \
         Input(in_stream=tty_in) as input_generator, \
         CursorAwareWindow(in_stream=tty_in,
                           out_stream=tty_out,
                           hide_cursor=False,
                           extra_bytes_callback=input_generator.unget_bytes) as window:
        prompt = Prompt(window, input_generator, finder)
        try:
            (match, execute, cursor_pos) = prompt.run()
        except KeyboardInterrupt:
            match = None
    if match is not None:
        print(execute)
        print(cursor_pos)
        print(match, end="\0")


if __name__ == "__main__":
    main()

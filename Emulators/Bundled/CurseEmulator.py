from Emulators.OhNoAnotherBunchOfBrainFckEmulators4Python import ONABOBFE4P_emulation_base
from time import sleep
import curses
import os
from threading import Thread
from time import sleep, time
from queue import Queue, Empty

curse_screen = """OUTPUT: //////////////////////////////////////////////////////////////////////
/                                                                            /
/                                                                            /
//////////////////////////////////////////////////////////////////////////////
INPUT:
Data              
|     |     |     |     |     |     |     |     |     |     |     |     |     |
|     |     |     |     |     |     |     |     |     |     |     |     |     |

Program
|     |     |     |     |     |     |     |     |     |     |     |     |     |
                                                                             """

if os.getenv("PRINT_BLANK_DATA_TO_ENSURE_ENLARGED_TERMINAL_IN_IDE", default=False):
    for _ in range(15): print(" " * 80); sleep(0.00001);


class Queues:
    def __init__(self):
        self.input = None
        self.shutdown = None
        self.output = None


queues = Queues()


def start_curse_queues():
    global queues

    queues.input = Queue()
    queues.shutdown = Queue()
    queues.output = Queue()


def start_curse_engine():
    global queues

    stdscr = curses.initscr()
    curses.noecho()
    curses.curs_set(0)
    stdscr.keypad(True)

    outputwin = stdscr.subwin(12, 80, 0, 0)
    inputwin = stdscr.subwin(2, 80, 12, 0)

    def outputThreadFunc():
        t = time()
        for e, line in enumerate(curse_screen.split("\n")):
            outputwin.addstr(e, 0, line)
        outputwin.move(0, 0)
        while queues.shutdown.empty():
            try:
                if not queues.output.empty():
                    y, x, inp = queues.output.get()
                    if (y, x) != (8, 79):
                        outputwin.addstr(y, x, inp)
            except Empty:
                pass
            if time() - t > 0.05:
                t = time()
                outputwin.refresh()

    def inputThreadFunc():
        inputwin.addstr("-" * 80)
        inputwin.addstr("")
        inputwin.timeout(200)
        while queues.shutdown.empty():
            input_char = inputwin.getch()
            if input_char != -1:
                queues.input.put(input_char)

    outputThread = Thread(target=outputThreadFunc)
    inputThread = Thread(target=inputThreadFunc)
    outputThread.start()
    inputThread.start()

class ONABOBFE4P_emulation_using_curse(ONABOBFE4P_emulation_base):
    def __init__(self, program, initial_data=None):

        start_curse_queues()

        self.input_queue = queues.input
        self.output_queue = queues.output
        self.shutdown_queue = queues.shutdown
        self.x = 0
        self.y = 1
        self.move_change = True
        self.value_change = True

        def print_curse(c):
            self.x += 1
            if self.x == 77:
                self.x = 1
                self.y+= 1
                if self.y == 3:
                    self.y = 1
            self.output_queue.put((self.y, self.x, c))

        def input_curse():
            input_char = None
            while input_char is None:
                if not self.input_queue.empty():
                    input_char = chr(self.input_queue.get())
            self.output_queue.put((4, 6, input_char))
            return [input_char]

        def update_curse_screen(self, when, error):
            if when == "END_STEP":

                self.output_queue.put((9, 9, str(self.program_pointer - 1)))
                for e, x in enumerate(range(1, 78, 6)):
                    if self.program_pointer + e < len(self.program):
                        self.output_queue.put((10, x, self.program[self.program_pointer + e] + "  "))
                    else:
                        self.output_queue.put((10, x, "END"))


                if self.move_change:
                    self.output_queue.put((5, 5, str(self.data_pointer)))
                    for e,x in enumerate(range(1,78,6)):
                        if self.data_pointer + e < self.max_data:
                            val = self.data[self.data_pointer+e]
                            if 32 <= val and 126 >= val:
                                self.output_queue.put((6 ,  x,  "'" +chr(val) + "'"))
                            else:
                                self.output_queue.put((6 ,  x,  "   "))
                            self.output_queue.put((7, x, str(val) + "  "))
                        else:
                            self.output_queue.put((6, x, "     "))
                            self.output_queue.put((7, x, "     "))

                elif self.value_change:
                    val = self.data[self.data_pointer]
                    if 32 <= val and 126 >= val:
                        self.output_queue.put((6, 1, "'" + chr(val) + "'"))
                    else:
                        self.output_queue.put((6, 1, "   "))
                    self.output_queue.put((7 , 1, str(val) + "  "))

            if when in [">","<","-","+","[","]",".",",","END_STEP"]:
                self.move_change =  when in [">","<","[","]"]
                self.value_change = when in ["+", "-", ","]

            return True, False

        def finish_curse_when_program_done(self, when, error):
            if when == "DONE":
                sleep(4)
                self.shutdown_queue.put(1)
            return True, False

        super().__init__(" " + program, initial_data, max_data=30000,
                         hooks=[update_curse_screen, finish_curse_when_program_done],
                         io_output=print_curse, io_input=input_curse,
                         max_cell_value=2 ** 8, use_negatives=False,
                         allow_pointer_overflow=False, allow_pointer_underflow=False,
                         allow_data_overflow=False, allow_data_underflow=False)

    def run(self):
        try:
            start_curse_engine()
            super()._run_with_step(self._step)
        except Exception as e:
            self.shutdown_queue.put(1)
            raise e

    def _step(self):
        sleep(0.1)
        return super()._step()

if __name__ == "__main__":
    hello_world = "s>++++++++[<+++++++++>-]<.>++++[<+++++++>-]<+.+++++++..+++.>>++++++[<+++++++>-]<++.------------.>++++++[<+++++++++>-]<+.<.+++.------.--------.>>>++++[<++++++++>-]<+."
    ONABOBFE4P_emulation_using_curse(hello_world, None).run()
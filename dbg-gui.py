import dearpygui.dearpygui as dpg
from cpu import CPU
from run import load_program

class DebugGUI:
    def __init__(self):
        self.debug_window = None
        self.cpu = CPU()

    def create_memory_dump(self, start, stop):
        with dpg.child_window(label="Memory Dump", width=380, height=200, parent=self.debug_window) as self.memory_dump:
            for i in range(start, stop, 16):
                chunk = self.cpu.mem[i:i+16]
                dpg.add_text(f"{i:04X}: " + " ".join(f"{b:02X}" for b in chunk) + " " + "".join([chr(b) if 32 <= b <= 126 else '.' for b in chunk]))
    
    def create_register_display(self):
        with dpg.child_window(label="Registers", width=380, height=100, parent=self.debug_window) as self.register_display:
            for i in range(16):
                if i == 14:
                    dpg.add_text(f"R{i} (SP): {self.cpu.reg[i]:04X}")
                elif i == 15:
                    dpg.add_text(f"R{i} (PC): {self.cpu.reg[i]:04X}")
                elif i == 0:
                    dpg.add_text(f"R{i} (Zero): {self.cpu.reg[i]:04X}")
                else:
                    dpg.add_text(f"R{i:2}: {self.cpu.reg[i]:04X}")
            dpg.add_text(f"FLAG: {self.cpu.flag:016b}")

    def create_disassembly_view(self):
        with dpg.child_window(label="Disassembly", width=380, height=200, parent=self.debug_window) as self.disassembly_view:
            # logic to disassemble instructions and display them
            pass

    def write_memory(self):
        # logic to write memory based on user input
        pass

    def execute_from_address(self):
        # logic to execute from a specific address based on user input
        pass

    def load_program_from_file(self):
        # logic to load a program from a file based on user input
        pass

    def create_debug_window(self):
        with dpg.window(label="Debugger", width=400, height=300) as self.debug_window:
            # buttons and input fields for commands
            # status display area, memory dump area, control buttons, disassembly view for inner window
            # +----------+----------+
            # |  Control |  Memory  |
            # +----------+----------+
            # | Registers|  Disasm  |
            # +----------+----------+
            with dpg.group(horizontal=True):
                # control buttons
                dpg.add_button(label="Write Memory", callback=self.write_memory)
                dpg.add_button(label="Execute", callback=self.execute_from_address)
                dpg.add_button(label="Load Program", callback=self.load_program_from_file)
            # display area for registers and memory
            self.create_memory_dump(0x0000, 0x00FF)
            self.create_register_display()
            self.create_disassembly_view()
        

if __name__ == "__main__":
    dpg.create_context()
    debug_gui = DebugGUI()
    debug_gui.create_debug_window()
    dpg.create_viewport(title='SRC16 Debugger', width=600, height=400)
    dpg.set_primary_window(debug_gui.debug_window, True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()

import tkinter as tk
warn_level = 1

def matrix_builder(columns,rows, default=0):
    return [[default for _ in range(rows)] for _ in range(columns)]

class Xerox:
    class DocuColor():
        """matrix 15 x 8
        (value) c1/r8 c2 c3 c4 c5 c6 c7 c8 c9 c10 c11 c12 c13 c14 c15
           64    r7   dot dot dot dot ..
           32    r6    ...
           16    r5
            8    r4     
            4    r3
            2    r2
            1    r1    ...
        the labels rx and cx are also dots. c1/r8 is only one dot
         c1 = Parity; c2 = Minute; c3=Unused; c4=Unused; c5 = Hour; etc..
         r8 = parity; note: parity of rows (c1) override the parity of column (ie: the dot at c1/r8 tells us the parity of the rows (the dots at r1,r2,r3,r4,r5,r6,r7) , not the parity of the columns)
        dots are reads from down to up
                                           / \ <-- this is supposed to be an arrow from down to up
                                            |
                                            |
        """
        MATRIX_COLUMNS_NUMBER = 15
        MATRIX_ROWS_NUMBER = 8
        COLUMNS_LABELS = ["row parity", "minute", "unused1", "unused2", "hour", "day", "month", "year", "unused3", "separator", "serial_b4", "serial_b3", "serial_b2", "serial_b1", "unknown"]
        ROWS_LABELS = range(MATRIX_ROWS_NUMBER, 0, -1)
        def __init__(self):
            self.matrix = matrix_builder(self.MATRIX_COLUMNS_NUMBER, self.MATRIX_ROWS_NUMBER)
            return
        def update(self, column:str, row:str, value=1) -> None:
            if value not in [0,1]:
                raise ValueError(f"Invalid value {value} while updating. The Xerox docusign only accept 0 or 1 (0= empty; 1=filled)")
            self.matrix[column][row] = value
            return
        def load(self, matrix:list) -> None:
            if len(matrix) != self.MATRIX_COLUMNS_NUMBER:
                raise ValueError("The loaded matrix has too many columns for a Xerox docusign")
            for row in matrix:
                if len(row) != self.MATRIX_ROWS_NUMBER:
                    raise ValueError("The loaded matrix has too many rows for a Xerox docusign")
            self.matrix = matrix
            return
        def getDate(self) -> str:
            return f"{self.getTime()} {self.getDay():02d}-{self.getMonth():02d}-{self.getYear():02d}"
        def getTime(self) -> str:
            return f"{self.getHour():02d}:{self.getMinute():02d}"
        def getDay(self) -> int:
            return self.read_column(5)
        def getMonth(self) -> int:
            return self.read_column(6)
        def getYear(self) -> int:
            return self.read_column(7)
        def getMinute(self) -> int:
            return self.read_column(1)
        def getHour(self) -> int:
            return self.read_column(4)
        def getType(self) -> str:
            """the type of document: either printed or copied -- THIS INFORMATION IS NOT CONFIRMED AND MIGHT BE WRONG"""
            #if the column 10 is filled then it is a copy - if it is empty then the document is a print
            #note: I'm not sure how the dots magically dissapear from a print to a copy - I don't own printers or copiers to test
            return "printed(?)" if self.read_column(9) > 0 else "copied(?)"
        def getSerial(self) -> str:
            return f"{self.read_column(13):02d}{self.read_column(12):02d}{self.read_column(11):02d}{self.read_column(10):02d}"
        def read_column(self, col:int) -> int:
            #top row is parity row -> we do not read it; Note that the first column is also the parity column but there are no impact on decoding from reading it
            return sum(self.matrix[col][i] * 2**i for i in range(self.MATRIX_ROWS_NUMBER - 1))
        def read_allcolums(self) -> dict:
            return dict(zip(self.COLUMNS_LABELS, [self.read_column(col) for col in range(self.MATRIX_COLUMNS_NUMBER)]))
        def integrity_check(self) -> str:
            integrity_status = ""
            #parity
            parity_result = self.parity_check()
            if sum(parity_result['columns']) + sum(parity_result['rows']) > 0:
                failed_columns = [i+1 for i,v in enumerate(parity_result['columns']) if v]
                failed_rows = [i+1 for i,v in enumerate(parity_result['rows']) if v]
                integrity_status += f"Warning:\n{sum(parity_result['columns'])} columns parity errors: {failed_columns}\n{sum(parity_result['rows'])} rows parity errors: {failed_rows}\n"
            #separator
            if self.separator_check():
                integrity_status += "Warning: separator is malformed.\n"
            #coherence
            coherence = self.coherence_check()
            return integrity_status + coherence
        def coherence_check(self) -> str:
            """check that the value in the columns are not impossible. Exemple: a 13th month"""
            message = ""
            minute = self.getMinute()
            hour = self.getHour()
            day = self.getDay()
            month = self.getMonth()
            year = self.getYear()
            if minute > 59: message += f"impossible number of minutes, got {minute}\n"
            if hour > 23: message += f"impossible number of hours, got {hour}\n"
            if day > 31: message += f"impossible number of days, got {day}\n"
            if month > 31: message += f"impossible number of months, got {month}\n"
            if (day == 31 and month in [1, 3, 5, 7, 8, 10, 12]) or (month == 2 and day > 29): message += "impossible number of days for the month\n"
            if month == 2 and day > 28 and year % 4 != 0: message += "29+ days in february in a non-leap year\n"
            return message
        def separator_check(self) -> bool:
            """check if the separator is malformed. Returns True if the separator is wrong."""
            if self.matrix[9][7] == 0:
                if self.read_column(9) != 127:
                    return True
            else:
                if self.read_column(9) != 0:
                    return True
            return False
        def parity_check(self) -> dict:
            """check the integrity of the code. returns true for columns or rows with a parity mismatch"""
            failed = {'columns': [False,]*self.MATRIX_COLUMNS_NUMBER, 'rows': [False,]*self.MATRIX_ROWS_NUMBER}
            # row parity
            for i, col in enumerate(self.matrix):
                if sum(col[j] for j in range(self.MATRIX_ROWS_NUMBER - 1)) % 2 == col[self.MATRIX_ROWS_NUMBER - 1]:
                    failed['columns'][i] = True
                    if warn_level > 0: print(f"Warning: column {i+1} failed parity check.")
            # column parity; we ignore top row
            for row in range(self.MATRIX_ROWS_NUMBER - 1):
                if sum(col[row] for col in self.matrix[1:]) % 2 == self.matrix[0][row]:
                    failed['rows'][row] = True
                    if warn_level > 0: print(f"Warning: row {row+1} failed parity check.")
            return failed
        
        def get_infos(self) -> dict:
            """returns all relevant informations"""
            return {'date':self.getDate(), 'serial':self.getSerial(), 'type':self.getType(), 'unknown':self.read_column(14)}
    class DocuColor_flipped(DocuColor):
        """
        A flipped version of the DocuColor. Sometimes the DocuColor pattern is flipped 90° on the left.
        __Does it depends on the firmware?__
        
                (unknown) c8/r15   c7   c6   c5   c4   c3  c2  c1
                (serial)    r14      dot   dot   dot <---
                (serial)    r13     <--
                (serial)    r12     <--
                (serial)    r11
                (separator) r10
                (unused)    r9
                (year)      r8
                (month)     r7
                (day)       r6
                (hour)      r5
                (unused)    r4
                (unused)    r3
                (minute)    r2
                (parity)    r1           <-- parity dots -->
        the labels rx and cx are also dots. c8/r15 is only one dot
        c8 is a parity column; 
        note: difference in the flipped version is the dot at c8/r15 still prioritize the parity of the rows and is not affected by the flip.
        it shows that this version is different and not just a 90° flip of the pattern (even if it's mostly what it is about)
         if the pattern was printed on a landscape paper instead of portrait, we could still tell the difference between the two because of this slight difference.
        """
        MATRIX_COLUMNS_NUMBER = 8
        MATRIX_ROWS_NUMBER = 15
        COLUMNS_LABELS = range(MATRIX_COLUMNS_NUMBER, 0, -1)
        ROWS_LABELS = ['unknown', 'serial_b1', 'serial_b2', 'serial_b3', 'serial_b4', 'separator', 'unused3', 'year', 'month', 'day', 'hour', 'unused2', 'unused1', 'minute', 'row parity']
        def read_column(self, row) -> int:
            #read row but I don't want to rename as I'm overwriting the method
            return sum(self.matrix[i - 1][row] * 2**(self.MATRIX_COLUMNS_NUMBER - i) for i in range(self.MATRIX_COLUMNS_NUMBER, 1, -1))
        def parity_check(self) -> dict:
            """check the integrity of the code. returns true for columns or rows with a parity mismatch"""
            failed = {'columns': [False,]*self.MATRIX_COLUMNS_NUMBER, 'rows': [False,]*self.MATRIX_ROWS_NUMBER}
            # row parity
            for i, col in enumerate(self.matrix):
                if sum(col[j] for j in range(self.MATRIX_ROWS_NUMBER - 1)) % 2 == col[self.MATRIX_ROWS_NUMBER - 1]:
                    failed['columns'][i] = True
                    if warn_level > 0: print(f"Warning: column {i+1} failed parity check.")
            # column parity; we ignore top row
            for row in range(self.MATRIX_ROWS_NUMBER - 1):
                if sum(col[row] for col in self.matrix[1:]) % 2 == self.matrix[0][row]:
                    failed['rows'][row] = True
                    if warn_level > 0: print(f"Warning: row {row+1} failed parity check.")
            return failed
        def separator_check(self) -> bool:
            """check if the separator is malformed. Returns True if the separator is wrong."""
            if self.matrix[0][9] == 0:
                if self.read_column(9) != 127:
                    return True
            else:
                if self.read_column(9) != 0:
                    return True
            return False
    class Phaser(DocuColor):
        """similar to DocuColor but columns 3 and 4 are being used.
        Unknown what for.    Dataset size: 2
                            Current value range for column 3: 0-6
                            Current value range for column 4: 0-1
                                        (columns start at index 1)
                            need more data.
        """
        COLUMNS_LABELS = ["row parity", "minute", "unknown1", "unknown2", "hour", "day", "month", "year", "unused", "separator", "serial_b4", "serial_b3", "serial_b2", "serial_b1", "unknown3"]
        def get_infos(self) -> dict:
            """returns all relevant informations"""
            return {'date':self.getDate(), 'serial':self.getSerial(), 'unknowns':(self.read_column(2), self.read_column(3), self.read_column(14))}
    Default = DocuColor #default for Xerox
    WorkCentre = Phaser #same as Phaser

class Dell:
    class ColorLaser(Xerox.DocuColor_flipped):
        """similar to the flipped version of the DocuColor except the rows 3 and 4 are being used.
        Unknown what for.
        """ 
        ROWS_LABELS = ['unknown3', 'serial_b1', 'serial_b2', 'serial_b3', 'serial_b4', 'separator', 'unused', 'year', 'month', 'day', 'hour', 'unknown2', 'unknown1', 'minute', 'row parity']
        def get_infos(self) -> dict:
            """returns all relevant informations"""
            return {'date':self.getDate(), 'serial':self.getSerial(), 'unknowns':(self.read_column(2), self.read_column(3), self.read_column(14))}
class Epson:
    Aculaser_c4000 = Dell.ColorLaser #same as the Dell ColorLaser
    Aculaser_c3000 = Dell.ColorLaser #same as the Dell ColorLaser
    #Aculaser_c1xxx-2xxx are very different
    

class gui:
    app = tk.Tk()
    
    def __init__(self):
        self.app.title("Machine Identification Code - Decoder")
        self.grid = tk.Frame(self.app)
        self.grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        control_frame = tk.Frame(self.app, padx=10, pady=10)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y) 
        
        #printer selection options
        self.menu = {
            "DocuColor": Xerox.DocuColor(),
            "DocuColor (flipped)": Xerox.DocuColor_flipped(),
            "Phaser": Xerox.Phaser(),
            "ColorLaser": Dell.ColorLaser(),
            "Aculaser C4000": Epson.Aculaser_c4000(),
            "Aculaser C3000": Epson.Aculaser_c4000(),
        }
        self.var = tk.StringVar(value="DocuColor")
        menubutton = tk.Menubutton(control_frame, textvariable=self.var, indicatoron=True,
                                   borderwidth=1, relief="raised", width=0, takefocus=True)
        main_menu = tk.Menu(menubutton, tearoff=False)
        menubutton.configure(menu=main_menu)
        for item in (("Xerox", "DocuColor", "DocuColor (flipped)", "Phaser"),
                     ("Dell", "ColorLaser"),
                     ("Epson", "Aculaser C4000", "Aculaser C3000")
                     ):
            menu = tk.Menu(main_menu, tearoff=False)
            main_menu.add_cascade(label=item[0], menu=menu)
            for value in item[1:]:
                menu.add_radiobutton(label=value, variable=self.var, value=value, command=self.on_grid_size_change)
        
        #(keyboard navigation) open the menu - current solution is to trick a mouse click event when pressing spacebar while focusing on the menu
        menubutton.bind('<space>', menubutton.event_generate('<Button-1>'))
        menubutton.pack(side="top", padx=20, pady=20)
        
        #result label
        self.label_result = tk.Label(control_frame, text="---")
        self.label_result.pack(side="bottom", pady=10)
        #warnings
        self.label_parity = tk.Label(control_frame, text="---")
        self.label_parity.pack(side="bottom", pady=0)
        
        
        update_button = tk.Button(control_frame, text="Decode!", command=self.update_label)
        update_button.pack(side="bottom", pady=10)
        
        self.grid_builder(self.grid, self.menu[self.var.get()].MATRIX_ROWS_NUMBER + 1, self.menu[self.var.get()].MATRIX_COLUMNS_NUMBER + 1)
    def run(self):
        self.app.mainloop()
    
    def update_label(self):
        self.label_result.config(text=f"{self.menu[self.var.get()].get_infos()}")
        self.label_parity.config(text=self.menu[self.var.get()].integrity_check())
        
    def update_matrix(self, col, row, value):
        printer = self.menu[self.var.get()]
        printer.update(col - 1, printer.MATRIX_ROWS_NUMBER - row, value)

    class button:
        def __init__(self, parent, row, col, parentclass):
            self.canvas = tk.Canvas(parent, width=50, height=50)
            self.canvas.grid(row=row, column=col, padx=5, pady=5)
            self.is_toggled = False
            self.circle = self.canvas.create_oval(5, 5, 45, 45, fill="gray")
            #(keyboard navigation) tabulation nav
            self.canvas.bind("<Tab>", self.canvas.tk_focusNext().focus)
            self.canvas.unbind("<Tab>") #somehow needed; tkinter are you good?
            self.canvas.bind("<Shift-Tab>", self.canvas.tk_focusPrev().focus)
            self.canvas.bind("<space>", self.toggle)
            #(mouse) mouse click
            self.canvas.bind("<Button-1>", self.toggle)
            
            self.pos = (col, row)
            self.parentclass = parentclass
            
        def toggle(self, event):
            self.is_toggled = not self.is_toggled
            if self.is_toggled:
                new_color = "yellow"
                self.parentclass.update_matrix(*self.pos, 1)
            else:
                new_color = "gray"
                self.parentclass.update_matrix(*self.pos, 0)
            self.canvas.itemconfig(self.circle, fill=new_color)
            
            
    def grid_builder(self, parent, rows, cols):
        # Clear existing grid
        for widget in parent.winfo_children():
            #widget.canvas.delete("all")
            widget.destroy()
        
        # new grid
        for row in range(rows):
            for col in range(cols):
                if row == 0 and col == 0:
                    label = tk.Label(parent, text="", borderwidth=1, relief="solid")
                    label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                elif row == 0:
                    label = tk.Label(parent, text=f"{self.menu[self.var.get()].COLUMNS_LABELS[col - 1]}", borderwidth=0, relief="solid")
                    label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                elif col == 0:
                    label = tk.Label(parent, text=f"{self.menu[self.var.get()].ROWS_LABELS[row - 1]}", borderwidth=0, relief="solid")
                    label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                else:
                    self.button(parent, row, col, self)
    
        for col in range(cols):
            parent.grid_columnconfigure(col, weight=1)
        for row in range(rows):
            parent.grid_rowconfigure(row, weight=1)
            
    def on_grid_size_change(self):
        cols, rows = self.menu[self.var.get()].MATRIX_COLUMNS_NUMBER + 1, self.menu[self.var.get()].MATRIX_ROWS_NUMBER + 1
        self.grid_builder(self.grid, rows, cols)

# code
if __name__ == "__main__":
    app = gui()
    app.run()
    
    

    
    
    

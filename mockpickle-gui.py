#!/bin/python

import mockpickle
import pickle
import tkinter as tk
import os.path
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.simpledialog import askstring
from tkinter.messagebox import showerror


class Data():

    confFilename = "mpg.state"

    def __init__(self):
        self.fileIn = ""
        self.fileOut = ""
        self.unload()

    def unload(self):
        self.mp = "(No file loaded...)"

    def load(self):
        if self.fileIn == "":
            return
        with open(self.fileIn, "rb") as f:
            self.mp = mockpickle.loads(f.read())

    def save(self):
        if self.fileOut == "":
            return
        with open(self.fileOut, "wb") as f:
            f.write(mockpickle.dumps(self.mp))


class MPGui(tk.Frame):

    def __init__(self, master=None, data=None):
        tk.Frame.__init__(self, master)

        self.data = data or Data()
        self.data.load()

        self.pack(expand=True, fill=tk.BOTH)
        self.createWidgets()

        self.setters = {}
        self.backbinds = {}
        self.reload()

    def createWidgets(self):
        menubar = tk.Menu(self)
        buttons = [
                ("Load...", self.load),
                ("Store...", self.save),
                ("Exit", self.shutdown),
        ]

        for label, cmd in buttons:
            menubar.add_command(label=label, command=cmd)

        self.master.config(menu=menubar)

        tree = ttk.Treeview(self)
        self.tree = tree
        tree['columns'] = ('type', 'value')
        tree.heading('type', text='Type')
        tree.heading('value', text='Value')
        tree.bind("<Double-1>", self.OnDoubleClick)
        tree.bind("<<TreeviewOpen>>", self.onTreeOpen)

        tree.pack(expand=True, fill=tk.BOTH)

    def OnDoubleClick(self, event):
        item = self.tree.identify('item', event.x, event.y)
        if item not in self.setters:
            return False
        newval = askstring("Change value", "Enter new value...")
        if not self.updateItem(item, newval):
            showerror("Error", "Mismatching type!")

    def onTreeOpen(self, event):
        item = self.tree.focus()
        self.expand(item)

    def load(self):
        self.data.fileIn = askopenfilename()
        self.data.load()
        self.reload()

    def save(self):
        self.data.fileOut = asksaveasfilename()
        self.data.save()

    def reload(self):
        self.addItem(self.data.mp)

    def addItem(self, obj, parent='', name='', setter=None):
        primitive = (int, bool, str, float, type(None), bytes)

        t = type(obj)

        if not isinstance(obj, primitive):
            # non-primitive types are searched recursively
            typename = t.__name__
            me = self.tree.insert(parent, 'end', text=name,
                                  values=(typename, ''))
            self.backbinds[me] = obj
            # only insert placeholder, load when user expands entry
            self.tree.insert(me, 'end', text="(Loading...)")

        else:
            me = self.tree.insert(parent, 'end', text=name,
                                  values=(t.__name__, obj))
            # only primitives get a setter
            if setter is not None:
                self.setters[me] = setter
            return

    def expand(self, item):
        # ignore if item has already been expanded
        children = self.tree.get_children(item)
        if len(children) != 1:
            return

        # remove placeholder
        self.tree.delete(children[0])

        obj = self.backbinds[item]
        t = type(obj)

        its = {
                dict: lambda: obj.items(),
                tuple: lambda: enumerate(obj),
                list: lambda: enumerate(obj),
                set: lambda: [(a, a) for a in obj]
        }
        it = None
        for k, v in its.items():
            if issubclass(t, k):
                it = v()
                break

        if it is None:
            # Fallback for general objects
            it = obj.__dict__.items()

        for key, value in it:
            setter = (obj, key)  # unused when subobj is not primitive
            if issubclass(t, set):
                setter = None
            self.addItem(value, parent=item, name=key, setter=setter)
        return

    def updateItem(self, item, value):
        owner, key = self.setters[item]
        t = type(owner[key])
        # print("%s: %s => %s" % (item, owner[key], value))
        # Fail when types don't match
        try:
            value = t(value)
        except (TypeError, ValueError):
            return False  # types not compatible

        owner[key] = value
        self.tree.item(item, values=(t.__name__, value))
        return True

    def shutdown(self):
        self.data.unload()
        with open(Data.confFilename, "wb") as f:
            f.write(pickle.dumps(self.data))
        self.quit()


if __name__ == "__main__":
    data = None
    if os.path.isfile(Data.confFilename):
        with open(Data.confFilename, "rb") as f:
            data = pickle.loads(f.read())

    mpg = MPGui(data=data)
    mpg.master.title('MockPickle GUI')
    mpg.mainloop()

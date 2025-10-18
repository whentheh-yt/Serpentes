"""
[NOTE]
For this mod (and any other mod) to work,
it needs to be in the same directory as
serpentes.py.

If you want to submit your own custom mods, 
please contact the owner of this respository
at whentheh.yt@gmail.com.
"""

# Example: Run game with 2 windows
import tkinter as tk
import serpentes

# ---- CONFIGURATION ----
NUM_WINDOWS_MOD = 2 
# -----------------------

serpentes.NUM_WINDOWS = NUM_WINDOWS_MOD
serpentes.cfg["game"]["num_windows"] = NUM_WINDOWS_MOD

from serpentes import Serpentes

def main():
    root = tk.Tk()
    game = Serpentes(root)
    root.mainloop()

if __name__ == "__main__":
    main()

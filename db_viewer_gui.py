
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

class DbViewerApp:
    def __init__(self, root, db_path):
        self.root = root
        self.db_path = db_path
        self.root.title(f"Database Viewer - {os.path.basename(db_path)}")
        self.root.geometry("1200x700")

        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Create file menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh", command=self.load_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Create info menu
        info_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Info", menu=info_menu)
        info_menu.add_command(label="Database Info", command=self.show_db_info)

        # Create filter frame
        self.filter_frame = ttk.LabelFrame(self.root, text="Filter Options")
        self.filter_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Label(self.filter_frame, text="Search:").grid(row=0, column=0, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.filter_frame, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        self.search_var.trace('w', self.filter_data)
        
        ttk.Button(self.filter_frame, text="Clear Filter", command=self.clear_filter).grid(row=0, column=2, padx=5, pady=5)
        
        # Create treeview frame
        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(self.tree_frame, 
                                 yscrollcommand=self.tree_scroll_y.set,
                                 xscrollcommand=self.tree_scroll_x.set,
                                 show='headings')
        self.tree.pack(fill="both", expand=True)

        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.load_data()

    def load_data(self):
        if not os.path.exists(self.db_path):
            self.show_error(f"Error: Database file not found at\n{self.db_path}")
            return
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Use the staging_attendance table directly
            table_name = "staging_attendance"
            self.root.title(f"Database Viewer - {os.path.basename(self.db_path)} [{table_name}]")

            # Get specific data from the table
            cursor.execute(f"SELECT employee_name, date, status, raw_charge_job FROM {table_name}")
            
            # Define specific column names
            columns = ["Employee Name", "Date", "Status", "Raw Charge Job"]
            self.tree["columns"] = columns
            
            # Set column headings and widths
            self.tree.heading("Employee Name", text="Employee Name", anchor='w')
            self.tree.column("Employee Name", anchor="w", width=200)
            
            self.tree.heading("Date", text="Date", anchor='w')
            self.tree.column("Date", anchor="w", width=100)
            
            self.tree.heading("Status", text="Status", anchor='w')
            self.tree.column("Status", anchor="w", width=100)
            
            self.tree.heading("Raw Charge Job", text="Raw Charge Job", anchor='w')
            self.tree.column("Raw Charge Job", anchor="w", width=700)

            # Clear existing data
            for i in self.tree.get_children():
                self.tree.delete(i)

            # Add new data
            rows = cursor.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
            
            # Update status
            self.status_var.set(f"Loaded {len(rows)} records from {table_name}")

        except sqlite3.Error as e:
            self.show_error(f"Database Error: {e}")
        except Exception as e:
            self.show_error(f"An unexpected error occurred: {e}")
        finally:
            if conn:
                conn.close()

    def filter_data(self, *args):
        search_term = self.search_var.get().lower()
        if not search_term:
            return
            
        # Get current data and filter it
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            # Convert all values to strings and check if any contain the search term
            if any(str(value).lower().find(search_term) != -1 for value in values):
                # Item matches, ensure it's visible
                self.tree.reattach(item, '', 0)
            else:
                # Item doesn't match, hide it
                self.tree.detach(item)
        
        # Update status
        visible_count = len([item for item in self.tree.get_children()])
        self.status_var.set(f"Showing {visible_count} filtered records")

    def clear_filter(self):
        self.search_var.set("")
        # Reattach all detached items
        for item in self.tree.get_children():
            self.tree.reattach(item, '', 0)
        # Update status
        total_count = len([item for item in self.tree.get_children()])
        self.status_var.set(f"Loaded {total_count} records")

    def show_db_info(self):
        if not os.path.exists(self.db_path):
            messagebox.showerror("Error", f"Database file not found at\n{self.db_path}")
            return
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get database information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            info_text = f"Database Path: {self.db_path}\n"
            info_text += f"Number of Tables: {len(tables)}\n"
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                info_text += f"Table: {table_name} ({row_count} records)\n"
                
                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                info_text += "  Columns:\n"
                for col in columns:
                    info_text += f"    - {col[1]} ({col[2]})\n"
                info_text += "\n"
            
            # Show in a message box
            messagebox.showinfo("Database Information", info_text)
            
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Database Error: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            if conn:
                conn.close()

    def show_error(self, message):
        # Clear the treeview and show an error message
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.tree["columns"] = ("Error")
        self.tree.heading("Error", text="Error")
        self.tree.column("Error", width=800)
        self.tree.insert("", "end", values=(message,))
        self.status_var.set("Error loading data")


if __name__ == "__main__":
    # IMPORTANT: Use the absolute path to your database file
    DATABASE_PATH = r"D:\Gawean Rebinmas\Autofill Venus Millware\Selenium_aug_25\Selenium Auto Fill\Selenium Auto Fill\data\staging_attendance.db"
    
    root = tk.Tk()
    app = DbViewerApp(root, DATABASE_PATH)
    root.mainloop()

import random
import json
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import scrolledtext
import webbrowser

# Database Setup (SQLite)
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        learning_style TEXT NOT NULL,
        progress TEXT DEFAULT '{}'
    )
""")
conn.commit()

# Learning Style Assessment (VARK)
class VARKAssessment:
    def __init__(self, master):
        self.master = master
        master.title("Learning Style Assessment")

        self.questions = [
            "Do you prefer to learn by reading text or listening to explanations?",
            "Do you prefer to learn by watching demonstrations or doing hands-on activities?",
            "Do you prefer to learn by seeing diagrams or maps, or by hearing descriptions?",
            "Do you prefer to learn by discussing ideas with others or by working independently?",
            "Do you prefer to learn by taking notes or by drawing diagrams?",
            # Add more questions if needed.
        ]
        self.answer_choices = ["Visual (V)", "Auditory (A)", "Reading/Writing (R)", "Kinesthetic (K)"]

        self.question_label = tk.Label(master, text=self.questions[0], wraplength=400)
        self.question_label.pack(pady=10)

        self.answer_vars = [tk.StringVar(value="") for _ in range(len(self.answer_choices))]
        self.answer_buttons = [
            tk.Radiobutton(
                master,
                text=choice,
                variable=self.answer_vars[i],
                value=choice[:1],
                command=self.check_next_question,
            )
            for i, choice in enumerate(self.answer_choices)
        ]
        for button in self.answer_buttons:
            button.pack(pady=5)

        self.next_button = tk.Button(master, text="Next", command=self.check_next_question)
        self.next_button.pack(pady=10)

        self.current_question = 0
        self.answers = []

    def check_next_question(self):
        selected_answer = self.answer_vars[self.current_question].get()
        if selected_answer:
            self.answers.append(selected_answer)
            self.current_question += 1
            if self.current_question < len(self.questions):
                self.question_label.config(text=self.questions[self.current_question])
                for i, button in enumerate(self.answer_buttons):
                    button.config(variable=self.answer_vars[self.current_question])
            else:
                self.calculate_learning_style()
        else:
            messagebox.showwarning("Incomplete Answer", "Please select an answer before proceeding.")

    def calculate_learning_style(self):
        # Analyze answers and determine dominant learning style.
        visual_count = self.answers.count("V")
        auditory_count = self.answers.count("A")
        reading_count = self.answers.count("R")
        kinesthetic_count = self.answers.count("K")

        dominant_style = max(
            visual_count, auditory_count, reading_count, kinesthetic_count
        )
        if dominant_style == visual_count:
            self.learning_style = "Visual"
        elif dominant_style == auditory_count:
            self.learning_style = "Auditory"
        elif dominant_style == reading_count:
            self.learning_style = "Reading/Writing"
        else:
            self.learning_style = "Kinesthetic"

        self.master.destroy()

# User Account Management
def register_user():
    def register():
        username = username_entry.get()
        password = password_entry.get()
        confirm_password = confirm_password_entry.get()

        if not username or not password or not confirm_password:
            messagebox.showwarning("Incomplete Information", "Please fill in all fields.")
            return

        if password != confirm_password:
            messagebox.showwarning(
                "Password Mismatch", "Passwords do not match. Please try again."
            )
            return

        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, learning_style) VALUES (?, ?, ?)",
                (username, password, learning_style),
            )
            conn.commit()
            conn.close()
            messagebox.showinfo("Registration Successful", f"User {username} registered successfully.")
            register_window.destroy()
        except sqlite3.IntegrityError:
            messagebox.showwarning(
                "Username Taken", "Username already exists. Please choose a different one."
            )

    register_window = tk.Toplevel(root)
    register_window.title("Register")

    global learning_style
    assessment = VARKAssessment(tk.Toplevel(register_window))
    register_window.wait_window(assessment.master)
    learning_style = assessment.learning_style

    username_label = tk.Label(register_window, text="Username:")
    username_label.pack()
    username_entry = tk.Entry(register_window)
    username_entry.pack()

    password_label = tk.Label(register_window, text="Password:")
    password_label.pack()
    password_entry = tk.Entry(register_window, show="*")
    password_entry.pack()

    confirm_password_label = tk.Label(register_window, text="Confirm Password:")
    confirm_password_label.pack()
    confirm_password_entry = tk.Entry(register_window, show="*")
    confirm_password_entry.pack()

    register_button = tk.Button(register_window, text="Register", command=register)
    register_button.pack(pady=10)

def login_user():
    def login():
        username = username_entry.get()
        password = password_entry.get()

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            global current_user
            current_user = user
            login_window.destroy()
            show_dashboard()
        else:
            messagebox.showwarning(
                "Invalid Credentials", "Incorrect username or password."
            )

    login_window = tk.Toplevel(root)
    login_window.title("Login")

    username_label = tk.Label(login_window, text="Username:")
    username_label.pack()
    global username_entry
    username_entry = tk.Entry(login_window)
    username_entry.pack()

    password_label = tk.Label(login_window, text="Password:")
    password_label.pack()
    global password_entry
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack()

    login_button = tk.Button(login_window, text="Login", command=login)
    login_button.pack(pady=10)

# Dashboard
def show_dashboard():
    def start_learning():
        dashboard_window.destroy()
        show_learning_content()

    def view_progress():
        progress_window = tk.Toplevel(root)
        progress_window.title("Progress")

        progress_text = scrolledtext.ScrolledText(progress_window, wrap=tk.WORD)
        progress_text.pack(expand=True, fill="both")

        progress = json.loads(current_user[4])
        for topic, data in progress.items():
            if data["completed"]:
                progress_text.insert(
                    tk.END,
                    f"{topic}: Completed on {data['timestamp']}\n",
                )
            else:
                progress_text.insert(
                    tk.END, f"{topic}: Not yet completed\n"
                )

    def update_profile():
        profile_window = tk.Toplevel(root)
        profile_window.title("Update Profile")

        # Implement logic for updating learning style and password.
        # You can use a similar approach as in the registration and login functions.

    def logout():
        global current_user
        current_user = None
        dashboard_window.destroy()

    dashboard_window = tk.Toplevel(root)
    dashboard_window.title("Dashboard")

    welcome_label = tk.Label(
        dashboard_window,
        text=f"Welcome, {current_user[1]}!",
        font=("Helvetica", 16),
    )
    welcome_label.pack(pady=20)

    start_button = tk.Button(
        dashboard_window,
        text="Start Learning",
        command=start_learning,
        width=20,
    )
    start_button.pack(pady=10)

    progress_button = tk.Button(
        dashboard_window,
        text="View Progress",
        command=view_progress,
        width=20,
    )
    progress_button.pack(pady=10)

    profile_button = tk.Button(
        dashboard_window,
        text="Update Profile",
        command=update_profile,
        width=20,
    )
    profile_button.pack(pady=10)

    logout_button = tk.Button(
        dashboard_window, text="Logout", command=logout, width=20
    )
    logout_button.pack(pady=10)

# Learning Content and Progress Tracking
def show_learning_content():
    def mark_complete(topic):
        progress = json.loads(current_user[4])
        progress[topic] = {"completed": True, "timestamp": datetime.now().isoformat()}
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET progress=? WHERE id=?",
            (json.dumps(progress), current_user[0]),
        )
        conn.commit()
        conn.close()
        messagebox.showinfo("Progress Updated", f"Progress for {topic} marked as complete.")
        learning_window.destroy()
        show_dashboard()

    learning_window = tk.Toplevel(root)
    learning_window.title("Learning Content")

    # Example Topics
    topics = [
        {"title": "Program Structure: Classes and Objects", "content": []},
        {"title": "Program Structure: Decomposition", "content": []},
        {"title": "Program Structure: Inheritance and Reuse", "content": []},
        # Add more topics as needed.
    ]

    topic_frame = tk.Frame(learning_window)
    topic_frame.pack(pady=10)

    for topic_data in topics:
        topic = topic_data["title"]
        content = topic_data["content"]

        # Learning Style-Specific Content
        if current_user[3] == "Visual":
            content.append(
                "**Visual Content:**\n"
                "Here's a diagram explaining the concept:\n"
                "[Link to visual content or embed image]\n"
            )
        elif current_user[3] == "Auditory":
            content.append(
                "**Auditory Content:**\n"
                "Listen to this explanation:\n"
                "[Link to audio recording or embed audio player]\n"
            )
        elif current_user[3] == "Reading/Writing":
            content.append(
                "**Reading/Writing Content:**\n"
                "Read this text describing the concept:\n"
                "[Link to article or tutorial]\n"
            )
        elif current_user[3] == "Kinesthetic":
            content.append(
                "**Kinesthetic Activity:**\n"
                "Try this hands-on activity:\n"
                "[Link to a simulation or interactive activity]\n"
            )
        else:
            content.append("Learning style not recognized.")

        topic_button = tk.Button(
            topic_frame,
            text=topic,
            command=lambda t=topic: show_topic_content(t, content, learning_window),
        )
        topic_button.pack(pady=5)

def show_topic_content(topic, content, parent_window):
    topic_window = tk.Toplevel(parent_window)
    topic_window.title(topic)

    topic_text = scrolledtext.ScrolledText(topic_window, wrap=tk.WORD)
    topic_text.pack(expand=True, fill="both")

    for item in content:
        topic_text.insert(tk.END, item + "\n")

    # Add a button to mark the topic as complete.
    complete_button = tk.Button(topic_window, text="Mark Complete", command=lambda t=topic: mark_complete(t))
    complete_button.pack(pady=10)

# Main Application Window
root = tk.Tk()
root.title("AI Education App")

# Main Menu
main_menu = tk.Menu(root)
filemenu = tk.Menu(main_menu, tearoff=0)
filemenu.add_command(label="Register", command=register_user)
filemenu.add_command(label="Login", command=login_user)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
main_menu.add_cascade(label="User Interface", menu=filemenu)

root.config(menu=main_menu)

current_user = None

root.mainloop()
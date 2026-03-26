import tkinter as tk
from tkinter import messagebox

import pyperclip

from llm_client import LLMClient, LLMError


class ReplyAssistantApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Reply Assistant")
        self.root.geometry("760x560")

        self.client = None
        try:
            self.client = LLMClient()
        except LLMError as exc:
            messagebox.showerror("Configuration Error", str(exc))

        self._build_ui()
        self._load_clipboard()

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        header = tk.Label(
            container,
            text="Hinge Reply Assistant",
            font=("Arial", 18, "bold"),
        )
        header.pack(anchor="w")

        subheader = tk.Label(
            container,
            text="Paste or auto-load a copied message, then generate three reply options.",
            justify="left",
        )
        subheader.pack(anchor="w", pady=(4, 12))

        input_label = tk.Label(container, text="Incoming message")
        input_label.pack(anchor="w")

        self.input_box = tk.Text(container, height=8, wrap="word")
        self.input_box.pack(fill="x", pady=(4, 12))

        button_row = tk.Frame(container)
        button_row.pack(fill="x", pady=(0, 12))

        tk.Button(
            button_row,
            text="Load Clipboard",
            command=self._load_clipboard
        ).pack(side="left")

        tk.Button(
            button_row,
            text="Generate Replies",
            command=self._generate
        ).pack(side="left", padx=8)

        tk.Button(
            button_row,
            text="Clear",
            command=self._clear_all
        ).pack(side="left")

        self.status_label = tk.Label(container, text="Ready", anchor="w")
        self.status_label.pack(fill="x", pady=(0, 12))

        self.reply_frames = {}

        for key, title in [
            ("playful", "Playful"),
            ("casual", "Casual"),
            ("flirty_light", "Flirty-light"),
        ]:
            frame = tk.LabelFrame(container, text=title, padx=10, pady=10)
            frame.pack(fill="x", pady=(0, 10))

            text_box = tk.Text(frame, height=3, wrap="word")
            text_box.pack(fill="x")

            btn_row = tk.Frame(frame)
            btn_row.pack(fill="x", pady=(8, 0))

            tk.Button(
                btn_row,
                text="Copy This Reply",
                command=lambda current_key=key: self._copy_reply(current_key),
            ).pack(side="left")

            self.reply_frames[key] = text_box

    def _set_status(self, text: str) -> None:
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def _load_clipboard(self) -> None:
        try:
            content = pyperclip.paste()
        except Exception as exc:
            messagebox.showerror("Clipboard Error", f"Could not read clipboard: {exc}")
            return

        self.input_box.delete("1.0", tk.END)

        if content:
            self.input_box.insert("1.0", content)
            self._set_status("Loaded message from clipboard.")
        else:
            self._set_status("Clipboard is empty.")

    def _clear_all(self) -> None:
        self.input_box.delete("1.0", tk.END)
        for text_box in self.reply_frames.values():
            text_box.delete("1.0", tk.END)
        self._set_status("Cleared.")

    def _generate(self) -> None:
        if self.client is None:
            messagebox.showerror("Setup Error", "LLM client is not configured.")
            return

        incoming = self.input_box.get("1.0", tk.END).strip()
        if not incoming:
            messagebox.showwarning("Missing Message", "Please paste a message first.")
            return

        self._set_status("Generating replies...")

        try:
            replies = self.client.generate_replies(incoming)
        except LLMError as exc:
            messagebox.showerror("Generation Error", str(exc))
            self._set_status("Generation failed.")
            return

        for key, value in replies.items():
            text_box = self.reply_frames[key]
            text_box.delete("1.0", tk.END)
            text_box.insert("1.0", value.strip())

        self._set_status("Replies generated.")

    def _copy_reply(self, key: str) -> None:
        text_box = self.reply_frames[key]
        value = text_box.get("1.0", tk.END).strip()

        if not value:
            messagebox.showwarning("No Reply", "Nothing to copy yet.")
            return

        try:
            pyperclip.copy(value)
        except Exception as exc:
            messagebox.showerror("Clipboard Error", f"Could not copy text: {exc}")
            return

        self._set_status("Reply copied to clipboard.")


def main() -> None:
    root = tk.Tk()
    root.geometry("760x560+100+100")
    root.lift()
    root.attributes("-topmost", True)
    root.focus_force()
    root.after(2000, lambda: root.attributes("-topmost", False))
    ReplyAssistantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
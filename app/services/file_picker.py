from pathlib import Path


class FilePickerService:
    def pick_image_file(self) -> str:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            selected_file = filedialog.askopenfilename(
                title="Select cheque image",
                filetypes=[
                    ("Image Files", "*.png *.jpg *.jpeg *.bmp"),
                    ("All Files", "*.*"),
                ],
            )
            root.destroy()

            if selected_file:
                return selected_file
        except Exception:
            pass

        manual_path = input("Enter the cheque image path: ").strip().strip('"')
        if manual_path and Path(manual_path).exists():
            return manual_path

        return ""

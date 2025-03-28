import os
import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class BoundingBoxEditor:
    def __init__(self, root, img_dir, bbox_dir, cleaned_bbox_dir):
        self.root = root
        self.img_dir = img_dir
        self.bbox_dir = bbox_dir
        self.cleaned_bbox_dir = cleaned_bbox_dir
        self.img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        self.current_idx = 0
        self.bboxes = []
        self.load_image()
        
        self.canvas = tk.Canvas(root, width=self.image.shape[1], height=self.image.shape[0])
        self.canvas.pack()
        self.tk_img = ImageTk.PhotoImage(Image.fromarray(self.image))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.rectangles = []
        self.draw_bboxes()
        
        self.canvas.bind("<Button-1>", self.click_bbox)
        
        self.next_button = tk.Button(root, text="Next", command=self.next_image)
        self.next_button.pack()
    
    def load_image(self):
        img_path = os.path.join(self.img_dir, self.img_files[self.current_idx])
        bbox_path = os.path.join(self.bbox_dir, os.path.splitext(self.img_files[self.current_idx])[0] + ".txt")
        
        self.image = cv2.imread(img_path)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.bboxes = self.load_bboxes(bbox_path)
    
    def load_bboxes(self, bbox_path):
        bboxes = []
        if os.path.exists(bbox_path):
            h, w, _ = self.image.shape
            with open(bbox_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip().replace("\ufeff", "")  # Remove potential BOM
                    parts = line.split()
                    if len(parts) != 5:
                        continue
                    try:
                        _, x_center, y_center, bw, bh = map(float, parts)
                        x = int((x_center * w) - (bw * w) / 2)
                        y = int((y_center * h) - (bh * h) / 2)
                        bw = int(bw * w)
                        bh = int(bh * h)
                        bboxes.append((x, y, bw, bh))
                    except ValueError:
                        continue
        return bboxes
    
    def draw_bboxes(self):
        for bbox in self.bboxes:
            x, y, w, h = bbox
            rect = self.canvas.create_rectangle(x, y, x + w, y + h, outline="red", width=2)
            self.rectangles.append((rect, bbox))
    
    def click_bbox(self, event):
        for rect, bbox in self.rectangles:
            x, y, w, h = bbox
            if x <= event.x <= x + w and y <= event.y <= y + h:
                self.canvas.delete(rect)
                self.bboxes.remove(bbox)
                self.rectangles.remove((rect, bbox))
                break
    
    def save_cleaned_bboxes(self):
        os.makedirs(self.cleaned_bbox_dir, exist_ok=True)
        cleaned_bbox_path = os.path.join(self.cleaned_bbox_dir, os.path.splitext(self.img_files[self.current_idx])[0] + ".txt")
        h, w, _ = self.image.shape
        with open(cleaned_bbox_path, "w") as f:
            for x, y, bw, bh in self.bboxes:
                x_center = (x + bw / 2) / w
                y_center = (y + bh / 2) / h
                bw /= w
                bh /= h
                f.write(f"0 {x_center} {y_center} {bw} {bh}\n")
    
    def next_image(self):
        self.save_cleaned_bboxes()
        
        self.current_idx += 1
        if self.current_idx < len(self.img_files):
            self.canvas.delete("all")
            self.load_image()
            self.tk_img = ImageTk.PhotoImage(Image.fromarray(self.image))
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
            self.rectangles = []
            self.draw_bboxes()
        else:
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    img_dir = filedialog.askdirectory(title="Select Image Directory")
    bbox_dir = filedialog.askdirectory(title="Select Bounding Boxes Directory")
    cleaned_bbox_dir = filedialog.askdirectory(title="Select Cleaned Labels Directory")
    app = BoundingBoxEditor(root, img_dir, bbox_dir, cleaned_bbox_dir)
    root.mainloop()
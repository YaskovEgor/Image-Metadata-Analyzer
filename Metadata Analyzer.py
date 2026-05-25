import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS, GPSTAGS
import json
import os
import threading
import webbrowser

class MetadataViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор метаданных изображений")
        self.root.geometry("1200x700")
        self.root.configure(bg='#f0f0f0')
        
        self.current_image_path = None
        self.current_photo = None
        self.current_gps = None
        
        self.create_menu()
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть изображение", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Сохранить метаданные как JSON", command=self.save_metadata)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        
        self.root.bind('<Control-o>', lambda e: self.open_image())
        self.root.bind('<Control-c>', lambda e: self.copy_current_text())
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Верхняя панель
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(top_frame, text="📁 Открыть изображение", command=self.open_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="💾 Сохранить метаданные", command=self.save_metadata).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="🔄 Обновить", command=self.refresh_metadata).pack(side=tk.LEFT, padx=5)
        
        # Левая панель
        left_frame = ttk.LabelFrame(main_frame, text="Превью и основная информация", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        
        self.thumbnail_label = ttk.Label(left_frame, text="Изображение не загружено", 
                                         background='white', relief=tk.SUNKEN)
        self.thumbnail_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        info_frame = ttk.LabelFrame(left_frame, text="Основная информация", padding="5")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        info_frame.columnconfigure(0, weight=1)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=10, width=30, wrap=tk.WORD)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.progress = ttk.Progressbar(left_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Правая панель
        right_frame = ttk.LabelFrame(main_frame, text="Метаданные", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Вкладка EXIF
        self.exif_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.exif_frame, text="EXIF данные")
        self.exif_text = scrolledtext.ScrolledText(self.exif_frame, wrap=tk.WORD)
        self.exif_text.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка GPS
        self.gps_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gps_frame, text="GPS координаты")
        
        # Кнопки для GPS
        gps_button_frame = ttk.Frame(self.gps_frame)
        gps_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.map_button = ttk.Button(gps_button_frame, text="🗺️ Открыть в Яндекс.Картах", 
                                     command=self.open_in_maps, state=tk.DISABLED)
        self.map_button.pack(side=tk.LEFT, padx=5)
        
        self.copy_gps_button = ttk.Button(gps_button_frame, text="📋 Копировать GPS", 
                                          command=self.copy_gps, state=tk.DISABLED)
        self.copy_gps_button.pack(side=tk.LEFT, padx=5)
        
        self.gps_text = scrolledtext.ScrolledText(self.gps_frame, wrap=tk.WORD)
        self.gps_text.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка Все данные
        self.all_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.all_frame, text="Все данные (JSON)")
        
        all_button_frame = ttk.Frame(self.all_frame)
        all_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(all_button_frame, text="📋 Копировать всё (JSON)", 
                   command=self.copy_all_json).pack(side=tk.LEFT, padx=5)
        
        self.all_text = scrolledtext.ScrolledText(self.all_frame, wrap=tk.WORD)
        self.all_text.pack(fill=tk.BOTH, expand=True)
        
        # Статус-бар
        self.status_bar = ttk.Label(self.root, text="Готов", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.root.columnconfigure(0, weight=1)
    
    def open_in_maps(self):
        """Открывает Яндекс.Карты с координатами"""
        if self.current_gps and 'latitude' in self.current_gps and 'longitude' in self.current_gps:
            lat = self.current_gps['latitude']
            lon = self.current_gps['longitude']
            url = f"https://maps.yandex.ru/?ll={lon},{lat}&z=17&pt={lon},{lat},pm2rdm"
            webbrowser.open(url)
    
    def copy_gps(self):
        """Копирует GPS координаты в буфер обмена"""
        if self.current_gps:
            lat = self.current_gps.get('latitude', 'Н/Д')
            lon = self.current_gps.get('longitude', 'Н/Д')
            gps_text = f"{lat}, {lon}"
            self.root.clipboard_clear()
            self.root.clipboard_append(gps_text)
            self.status_bar.config(text=f"Скопировано: {gps_text}")
            messagebox.showinfo("Успех", f"GPS координаты скопированы:\n{gps_text}")
    
    def copy_all_json(self):
        """Копирует все метаданные в JSON формате"""
        if self.current_image_path:
            metadata = self.read_image_metadata(self.current_image_path)
            json_str = json.dumps(metadata, indent=2, ensure_ascii=False, default=str)
            self.root.clipboard_clear()
            self.root.clipboard_append(json_str)
            self.status_bar.config(text="Скопированы все метаданные (JSON)")
            messagebox.showinfo("Успех", "Все метаданные скопированы в буфер обмена в формате JSON")
    
    def copy_current_text(self):
        """Копирует текст из активного текстового поля"""
        current_tab = self.notebook.index(self.notebook.select())
        
        if current_tab == 0:  # EXIF
            text = self.exif_text.get(1.0, tk.END).strip()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.status_bar.config(text="Скопированы EXIF данные")
                messagebox.showinfo("Успех", "EXIF данные скопированы")
        elif current_tab == 1:  # GPS
            text = self.gps_text.get(1.0, tk.END).strip()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.status_bar.config(text="Скопированы GPS данные")
                messagebox.showinfo("Успех", "GPS данные скопированы")
        elif current_tab == 2:  # Все данные
            self.copy_all_json()
    
    def get_gps_coordinates(self, exif_data):
        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'GPSInfo':
                for gps_tag in value:
                    sub_tag_name = GPSTAGS.get(gps_tag, gps_tag)
                    gps_info[sub_tag_name] = value[gps_tag]
        
        if gps_info:
            def convert_to_degrees(value):
                d = float(value[0])
                m = float(value[1])
                s = float(value[2])
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(gps_info.get('GPSLatitude', [0,0,0]))
            lon = convert_to_degrees(gps_info.get('GPSLongitude', [0,0,0]))
            
            if gps_info.get('GPSLatitudeRef') == 'S':
                lat = -lat
            if gps_info.get('GPSLongitudeRef') == 'W':
                lon = -lon
                
            return {
                'latitude': lat,
                'longitude': lon,
                'raw': gps_info
            }
        return None
    
    def read_image_metadata(self, image_path):
        metadata = {}
        
        with Image.open(image_path) as img:
            metadata['file_info'] = {
                'file_name': os.path.basename(image_path),
                'file_path': image_path,
                'file_size': f"{os.path.getsize(image_path) / 1024:.2f} KB",
                'format': img.format,
                'format_description': img.format_description,
                'mode': img.mode,
                'width': img.width,
                'height': img.height,
                'size': f"{img.width} x {img.height}",
                'color_bands': list(img.getbands())
            }
            
            exif_data = img._getexif()
            if exif_data:
                metadata['exif'] = {}
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore')
                        except:
                            value = str(value)
                    elif isinstance(value, tuple):
                        value = list(value)
                    
                    metadata['exif'][tag_name] = value
                
                gps = self.get_gps_coordinates(exif_data)
                if gps:
                    metadata['gps'] = gps
            
            if os.path.getmtime(image_path):
                from datetime import datetime
                metadata['file_info']['last_modified'] = datetime.fromtimestamp(
                    os.path.getmtime(image_path)
                ).strftime('%Y-%m-%d %H:%M:%S')
        
        return metadata
    
    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            self.current_image_path = file_path
            self.load_metadata_threaded()
    
    def load_metadata_threaded(self):
        self.progress.start()
        self.status_bar.config(text=f"Загрузка: {os.path.basename(self.current_image_path)}")
        
        thread = threading.Thread(target=self.load_metadata)
        thread.start()
    
    def load_metadata(self):
        try:
            self.load_thumbnail()
            metadata = self.read_image_metadata(self.current_image_path)
            self.root.after(0, self.display_metadata, metadata)
            
        except Exception as e:
            self.root.after(0, self.show_error, f"Ошибка загрузки: {str(e)}")
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.status_bar.config(text="Готов"))
    
    def load_thumbnail(self):
        try:
            img = Image.open(self.current_image_path)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            self.current_photo = ImageTk.PhotoImage(img)
            self.root.after(0, lambda: self.thumbnail_label.config(image=self.current_photo, text=""))
        except Exception as e:
            self.root.after(0, lambda: self.thumbnail_label.config(text=f"Ошибка загрузки превью:\n{str(e)}"))
    
    def display_metadata(self, metadata):
        self.info_text.delete(1.0, tk.END)
        self.exif_text.delete(1.0, tk.END)
        self.gps_text.delete(1.0, tk.END)
        self.all_text.delete(1.0, tk.END)
        
        # Основная информация
        if 'file_info' in metadata:
            info = metadata['file_info']
            info_str = f"""
Файл: {info.get('file_name', 'Н/Д')}
Размер файла: {info.get('file_size', 'Н/Д')}
Формат: {info.get('format', 'Н/Д')}
Размеры: {info.get('size', 'Н/Д')}
Режим цвета: {info.get('mode', 'Н/Д')}
Цветовые каналы: {', '.join(info.get('color_bands', []))}
Последнее изменение: {info.get('last_modified', 'Н/Д')}
"""
            self.info_text.insert(1.0, info_str)
        
        # EXIF данные
        if 'exif' in metadata:
            exif_str = ""
            important_tags = ['DateTime', 'Make', 'Model', 'ExposureTime', 'FNumber', 
                            'ISOSpeedRatings', 'FocalLength', 'Software', 'Copyright', 
                            'Artist', 'LensModel', 'WhiteBalance', 'Flash']
            
            for tag in important_tags:
                if tag in metadata['exif']:
                    exif_str += f"{tag}: {metadata['exif'][tag]}\n"
            
            exif_str += "\n--- Другие EXIF теги ---\n"
            for tag, value in metadata['exif'].items():
                if tag not in important_tags:
                    if 'MakerNote' in tag or 'makernote' in tag.lower():
                        continue 
                    exif_str += f"{tag}: {value}\n"
            
            self.exif_text.insert(1.0, exif_str)
        else:
            self.exif_text.insert(1.0, "EXIF данные отсутствуют")
        
        # GPS данные
        if 'gps' in metadata:
            gps = metadata['gps']
            self.current_gps = gps
            
            gps_str = f"Широта: {gps.get('latitude', 'Н/Д')}°\n"
            gps_str += f"Долгота: {gps.get('longitude', 'Н/Д')}°\n\n"
            gps_str += f"Яндекс.Карты: https://maps.yandex.ru/?ll={gps.get('longitude', '0')},{gps.get('latitude', '0')}&z=17\n\n"
            gps_str += "--- RAW GPS данные ---\n"
            
            if 'raw' in gps:
                for key, value in gps['raw'].items():
                    gps_str += f"{key}: {value}\n"
            
            self.gps_text.insert(1.0, gps_str)
            self.map_button.config(state=tk.NORMAL)
            self.copy_gps_button.config(state=tk.NORMAL)
        else:
            self.current_gps = None
            self.gps_text.insert(1.0, "GPS данные отсутствуют")
            self.map_button.config(state=tk.DISABLED)
            self.copy_gps_button.config(state=tk.DISABLED)
        
        # Все данные в JSON
        all_data_str = json.dumps(metadata, indent=2, ensure_ascii=False, default=str)
        self.all_text.insert(1.0, all_data_str)
    
    def save_metadata(self):
        if not self.current_image_path:
            messagebox.showwarning("Предупреждение", "Сначала откройте изображение")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить метаданные",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
            initialfile=f"{os.path.splitext(os.path.basename(self.current_image_path))[0]}_metadata.json"
        )
        
        if file_path:
            try:
                metadata = self.read_image_metadata(self.current_image_path)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
                
                messagebox.showinfo("Успех", f"Метаданные сохранены в:\n{file_path}")
                self.status_bar.config(text=f"Сохранено: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def refresh_metadata(self):
        if self.current_image_path:
            self.load_metadata_threaded()
        else:
            messagebox.showinfo("Информация", "Нет открытого изображения")
    
    def show_error(self, error_message):
        messagebox.showerror("Ошибка", error_message)
        self.status_bar.config(text="Ошибка загрузки")
    
    def show_about(self):
        about_text = """
Анализатор метаданных изображений
Версия 1.0

Просмотр EXIF, GPS и других метаданных
Поддерживаемые форматы: JPEG, PNG, BMP, TIFF, WEBP

Горячие клавиши:
Ctrl+O - открыть изображение
Ctrl+C - копировать текст из активной вкладки
"""
        messagebox.showinfo("О программе", about_text)

def main():
    root = tk.Tk()
    app = MetadataViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
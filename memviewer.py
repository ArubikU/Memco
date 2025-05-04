import os
import json
import pickle
import base64
import hashlib
import datetime
from typing import Dict, List, Any, Optional
from cryptography.fernet import Fernet, InvalidToken

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import messagebox
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.widgets import Meter
from ttkbootstrap.toast import ToastNotification
from tkinter import filedialog

try:
    from memco import MemCore, MemQLParser
except ImportError:
    pass

class MemViewer(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")  # Puedes cambiar el tema aquí
        self.title("MemViewer - Visualizador de archivos .mem")
        self.geometry("1000x700")

        self.mem_folder = None
        self.history_folder = None
        self.memories = []
        self.encryption_key = None

        self._create_ui()

    def _create_ui(self):
        container = tb.Frame(self, padding=10)
        container.pack(fill=BOTH, expand=True)

        # Top Bar
        top = tb.Frame(container)
        top.pack(fill=X, pady=5)

        tb.Label(top, text="Carpeta raíz (.memfolder):").pack(side=LEFT, padx=(0, 5))
        self.folder_var = tb.StringVar()
        tb.Entry(top, textvariable=self.folder_var, width=50).pack(side=LEFT, padx=(0, 5))
        tb.Button(top, text="Examinar", bootstyle=PRIMARY, command=self._browse_folder).pack(side=LEFT)
        tb.Button(top, text="Cargar", bootstyle=SUCCESS, command=self._load_memories).pack(side=LEFT, padx=(5, 0))

        # Key Frame
        key_frame = tb.Frame(container)
        key_frame.pack(fill=X, pady=5)

        tb.Label(key_frame, text="Clave de desencriptación:").pack(side=LEFT, padx=(0, 5))
        self.key_var = tb.StringVar()
        self.key_entry = tb.Entry(key_frame, textvariable=self.key_var, width=40, show="*")
        self.key_entry.pack(side=LEFT, padx=(0, 5))

        self.show_key_var = tb.BooleanVar()
        self.show_key_var.trace_add("write", lambda *_: self._toggle_key_visibility())
        tb.Checkbutton(key_frame, text="Mostrar clave", variable=self.show_key_var).pack(side=LEFT)
        tb.Button(key_frame, text="Aplicar clave", bootstyle=INFO, command=self._apply_encryption_key).pack(side=LEFT, padx=(5, 0))

        # Search and Query
        search_frame = tb.Frame(container)
        search_frame.pack(fill=X, pady=5)

        tb.Label(search_frame, text="Buscar:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tb.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_memories())
        tb.Entry(search_frame, textvariable=self.search_var, width=35).pack(side=LEFT, padx=(0, 10))

        tb.Label(search_frame, text="Consulta MemQL:").pack(side=LEFT, padx=(0, 5))
        self.memql_var = tb.StringVar()
        tb.Entry(search_frame, textvariable=self.memql_var, width=50).pack(side=LEFT, padx=(0, 5))
        tb.Button(search_frame, text="Ejecutar", bootstyle=WARNING, command=self._execute_memql).pack(side=LEFT)



        # Bottom Bar
        bottom = tb.Frame(container)
        bottom.pack(fill=X, pady=(10, 0))

        tb.Button(bottom, text="Exportar seleccionado", bootstyle=SECONDARY, command=self._export_selected).pack(side=LEFT)
        tb.Button(bottom, text="Exportar todos", bootstyle=SECONDARY, command=self._export_all).pack(side=LEFT, padx=(5, 0))
        tb.Button(bottom, text="Desencriptar seleccionado", bootstyle=SECONDARY, command=self._decrypt_selected).pack(side=LEFT, padx=(5, 0))
        tb.Button(bottom, text="Exportar historial", bootstyle=SECONDARY, command=self._export_history).pack(side=LEFT, padx=(5, 0))
        
        # Main Notebook
        self.notebook = tb.Notebook(container)
        self.notebook.pack(fill=BOTH, expand=True, pady=10)

        # Memories Tab
        memories_tab = tb.Frame(self.notebook)
        self.notebook.add(memories_tab, text="Memco")

        paned = tb.PanedWindow(memories_tab, orient=HORIZONTAL)
        paned.pack(fill=BOTH, expand=True)

        # Tree (Left)
        left = tb.Frame(paned)
        paned.add(left)

        tb.Label(left, text="Memorias:").pack(anchor=W)
        self.tree = tb.Treeview(left, columns=("id", "content", "encrypted"), show="headings", height=15)
        for col, name, width in [("id", "ID", 100), ("content", "Contenido", 250), ("encrypted", "Encriptado", 100)]:
            self.tree.heading(col, text=name)
            self.tree.column(col, width=width)
        self.tree.pack(fill=BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_memory_selected)

        scrollbar = tb.Scrollbar(left, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Detail + History (Right)
        right = tb.Frame(paned)
        paned.add(right)

        self.details_notebook = tb.Notebook(right)
        self.details_notebook.pack(fill=BOTH, expand=True)

        # Details Text
        details_frame = tb.Frame(self.details_notebook)
        self.details_notebook.add(details_frame, text="Detalles")
        self.details_text = ScrolledText(details_frame, wrap="word")
        self.details_text.pack(fill=BOTH, expand=True)\
        
        # History View
        history_frame = tb.Frame(self.details_notebook)
        self.details_notebook.add(history_frame, text="Historial")

        self.history_tree = tb.Treeview(history_frame, columns=("timestamp", "action"), show="headings")
        self.history_tree.heading("timestamp", text="Fecha/Hora")
        self.history_tree.heading("action", text="Acción")
        self.history_tree.pack(fill=X)
        self.history_tree.bind("<<TreeviewSelect>>", self._on_history_selected)

        tb.Label(history_frame, text="Detalles del historial:").pack(anchor=W, pady=(10, 0))
        self.history_details_text = ScrolledText(history_frame, height=15, wrap="word")
        self.history_details_text.pack(fill=BOTH, expand=True, pady=(5, 0))


    
    def _toggle_key_visibility(self, *args):
        """Toggle visibility of the encryption key."""
        if self.show_key_var.get():
            self.key_entry.config(show="")
        else:
            self.key_entry.config(show="*")
    
    def _setup_encryption(self, key: str) -> Optional[Fernet]:
        """Set up encryption with the provided key."""
        if not key:
            return None
        
        # Generate a 32-byte key from the provided key
        hashed_key = hashlib.sha256(key.encode()).digest()
        encoded_key = base64.urlsafe_b64encode(hashed_key)
        return Fernet(encoded_key)
    
    def _apply_encryption_key(self):
        """Apply the encryption key and try to decrypt encrypted memories."""
        key = self.key_var.get()
        if not key:
            messagebox.showwarning("Advertencia", "Por favor ingrese una clave de desencriptación")
            return
        
        try:
            self.encryption_key = self._setup_encryption(key)
            messagebox.showinfo("Información", "Clave de desencriptación aplicada. Seleccione una memoria encriptada para desencriptarla.")
            
            # Refresh the view if memories are loaded
            if self.memories:
                self._filter_memories()
        except Exception as e:
            messagebox.showerror("Error", f"Clave de desencriptación inválida: {e}")
            self.encryption_key = None
    
    def _decrypt_data(self, data):
        """Decrypt any data using the encryption key."""
        if not self.encryption_key:
            return data
        
        if isinstance(data, str):
            try:
                return self.encryption_key.decrypt(data.encode()).decode()
            except:
                # If decryption fails, return the original data
                return data
        elif isinstance(data, list):
            return [self._decrypt_data(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._decrypt_data(value) for key, value in data.items()}
        else:
            return data
    
    def _browse_folder(self):
        """Browse for a .memfolder folder."""
        folder = filedialog.askdirectory(title="Seleccionar carpeta raíz (.memfolder)")
        if folder:
            self.folder_var.set(folder)
    
    def _load_memories(self):
        """Load memories from the selected folder."""
        root_folder = self.folder_var.get()
        if not root_folder:
            messagebox.showerror("Error", "Por favor seleccione una carpeta raíz (.memfolder)")
            return
        
        if not os.path.exists(root_folder):
            messagebox.showerror("Error", "La carpeta seleccionada no existe")
            return
        
        # Check for .memtable and .memhistory folders
        memtable_folder = os.path.join(root_folder, ".memtable")
        memhistory_folder = os.path.join(root_folder, ".memhistory")
        
        if not os.path.exists(memtable_folder):
            messagebox.showerror("Error", "No se encontró la carpeta .memtable en la ruta especificada")
            return
        
        self.mem_folder = memtable_folder
        self.history_folder = memhistory_folder if os.path.exists(memhistory_folder) else None
        
        self.memories = []
        
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load memories
        for filename in os.listdir(memtable_folder):
            if filename.endswith('.mem'):
                try:
                    with open(os.path.join(memtable_folder, filename), 'rb') as f:
                        memory = pickle.load(f)
                        self.memories.append(memory)
                        
                        # Add to treeview
                        content_preview = memory.get("content", "")
                        if memory.get("encrypted", False):
                            content_preview = "[Contenido encriptado]"
                        else:
                            content_preview = content_preview[:50] + "..." if len(content_preview) > 50 else content_preview
                        
                        encrypted_status = "Sí" if memory.get("encrypted", False) else "No"
                        self.tree.insert("", tb.END, values=(memory.get("id", ""), content_preview, encrypted_status))
                except Exception as e:
                    print(f"Error loading memory file {filename}: {e}")
        
        messagebox.showinfo("Información", f"Se cargaron {len(self.memories)} memorias")
    
    def _filter_memories(self):
        """Filter memories based on search text."""
        search_text = self.search_var.get().lower()
        
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Filter and add memories
        for memory in self.memories:
            # Skip encrypted content in search if no key is available
            if memory.get("encrypted", False) and not self.encryption_key:
                content_searchable = ""
            else:
                content_searchable = memory.get("content", "").lower()
            
            if (search_text in memory.get("id", "").lower() or 
                search_text in content_searchable or 
                any(search_text in tag.lower() for tag in memory.get("tags", []))):
                
                content_preview = memory.get("content", "")
                if memory.get("encrypted", False):
                    content_preview = "[Contenido encriptado]"
                else:
                    content_preview = content_preview[:50] + "..." if len(content_preview) > 50 else content_preview
                
                encrypted_status = "Sí" if memory.get("encrypted", False) else "No"
                self.tree.insert("", tb.END, values=(memory.get("id", ""), content_preview, encrypted_status))
    
    def _execute_memql(self):
        """Execute a MemQL query."""
        query = self.memql_var.get()
        if not query:
            messagebox.showwarning("Advertencia", "Por favor ingrese una consulta MemQL")
            return
        
        if not self.mem_folder:
            messagebox.showerror("Error", "Por favor cargue una carpeta de memoria primero")
            return
        
        try:
            # Create a temporary MemCore instance to execute the query
            from memco import MemCore, MemQLParser
            
            memcore = MemCore(
                root_path=os.path.dirname(self.mem_folder),
                encryption_key=self.encryption_key
            )
            
            # Execute query
            memories = memcore.memql_query(query)
            
            if not memories:
                messagebox.showinfo("Información", "No se encontraron memorias que coincidan con la consulta")
                return
            
            # Clear treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Add results to treeview
            for memory in memories:
                content_preview = memory.content
                if len(content_preview) > 50:
                    content_preview = content_preview[:50] + "..."
                
                encrypted_status = "No"  # MemQL results are already decrypted if key was provided
                
                self.tree.insert("", tb.END, values=(memory.id, content_preview, encrypted_status))
            
            messagebox.showinfo("Éxito", f"Se encontraron {len(memories)} memorias")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al ejecutar la consulta: {str(e)}")
    
    def _load_memory_history(self, memory_id: str):
        """Load history for a specific memory."""
        if not self.history_folder:
            return []
        
        memory_history_folder = os.path.join(self.history_folder, memory_id)
        if not os.path.exists(memory_history_folder):
            return []
        
        history_entries = []
        
        for filename in sorted(os.listdir(memory_history_folder)):
            if filename.endswith('.memh'):
                try:
                    file_path = os.path.join(memory_history_folder, filename)
                    timestamp_str, action = filename.split('_', 1)
                    action = action.replace('.memh', '')
                    
                    # Format timestamp for display
                    try:
                        timestamp_dt = datetime.datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                        formatted_timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        formatted_timestamp = timestamp_str
                    
                    with open(file_path, 'rb') as f:
                        data = pickle.load(f)
                    
                    history_entries.append({
                        "timestamp": formatted_timestamp,
                        "raw_timestamp": timestamp_str,
                        "action": action,
                        "data": data,
                        "file_path": file_path
                    })
                except Exception as e:
                    print(f"Error loading history file {filename}: {e}")
        
        # Sort by timestamp (newest first)
        history_entries.sort(key=lambda x: x["raw_timestamp"], reverse=True)
        return history_entries
    
    def _decrypt_selected(self):
        """Decrypt the selected memory."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Por favor seleccione una memoria para desencriptar")
            return
        
        if not self.encryption_key:
            messagebox.showerror("Error", "Por favor ingrese y aplique una clave de desencriptación primero")
            return
        
        # Get selected memory ID
        memory_id = self.tree.item(selected_items[0], "values")[0]
        
        # Find memory in list
        memory = None
        memory_index = -1
        for i, mem in enumerate(self.memories):
            if mem.get("id") == memory_id:
                memory = mem
                memory_index = i
                break
        
        if not memory:
            return
        
        # Check if memory is encrypted
        if not memory.get("encrypted", False):
            messagebox.showinfo("Información", "Esta memoria no está encriptada")
            return
        
        # Try to decrypt
        try:
            # Decrypt all fields
            memory["content"] = self._decrypt_data(memory["content"])
            memory["tags"] = self._decrypt_data(memory["tags"])
            memory["source"] = self._decrypt_data(memory["source"])
            memory["metadata"] = self._decrypt_data(memory["metadata"])
            memory["encrypted"] = False
        
            # Update memory in list
            self.memories[memory_index] = memory
        
            # Update treeview
            content_preview = memory["content"][:50] + "..." if len(memory["content"]) > 50 else memory["content"]
            self.tree.item(selected_items[0], values=(memory.get("id", ""), content_preview, "No"))
        
            # Update details view
            self._on_memory_selected(None)
        
            messagebox.showinfo("Éxito", "Memoria desencriptada correctamente")
        except InvalidToken:
            messagebox.showerror("Error", "No se pudo desencriptar la memoria. La clave es incorrecta.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al desencriptar la memoria: {e}")
    
    def _on_memory_selected(self, event):
        """Handle memory selection."""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # Get selected memory ID
        memory_id = self.tree.item(selected_items[0], "values")[0]
        
        # Find memory in list
        memory = None
        for mem in self.memories:
            if mem.get("id") == memory_id:
                memory = mem
                break
        
        if not memory:
            return
        
        # Display memory details
        self.details_text.delete(1.0, tb.END)
        
        # Format memory details
        details = f"ID: {memory.get('id', '')}\n\n"
        
        # Handle encrypted content
        if memory.get("encrypted", False):
            details += "Contenido: [ENCRIPTADO]\n"
            details += "Tags: [ENCRIPTADOS]\n"
            details += "Fuente: [ENCRIPTADA]\n"
            details += "Metadatos: [ENCRIPTADOS]\n"
            details += "\nPara ver el contenido completo, ingrese la clave de desencriptación y haga clic en 'Desencriptar seleccionado'\n\n"
        else:
            details += f"Contenido:\n{memory.get('content', '')}\n\n"
        
            # Format tags
            tags = memory.get('tags', [])
            if isinstance(tags, list) and tags:
                details += f"Etiquetas: {', '.join(tags)}\n\n"
            else:
                details += "Etiquetas: [Ninguna]\n\n"
        
            details += f"Importancia: {memory.get('importance', 0)}\n\n"
            details += f"Creado: {memory.get('created_at', '')}\n\n"
            details += f"Actualizado: {memory.get('updated_at', '')}\n\n"
            details += f"Fuente: {memory.get('source', '')}\n\n"
            details += f"Encriptado: {'Sí' if memory.get('encrypted', False) else 'No'}\n\n"
        
            # Add metadata
            details += "Metadatos:\n"
            for key, value in memory.get("metadata", {}).items():
                details += f"  {key}: {value}\n"
    
        self.details_text.insert(tb.END, details)
        
        # Load and display history
        self._load_and_display_history(memory_id)
    
    def _load_and_display_history(self, memory_id: str):
        """Load and display history for a memory."""
        # Clear history treeview
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Clear history details
        self.history_details_text.delete(1.0, tb.END)
        
        # Load history
        history_entries = self._load_memory_history(memory_id)
        
        if not history_entries:
            self.history_details_text.insert(tb.END, "No hay historial disponible para esta memoria.")
            return
        
        # Add history entries to treeview
        for entry in history_entries:
            self.history_tree.insert("", tb.END, values=(entry["timestamp"], entry["action"]), 
                                    tags=(entry["raw_timestamp"], entry["action"]))
    
    def _on_history_selected(self, event):
        """Handle history selection."""
        selected_items = self.history_tree.selection()
        if not selected_items:
            return
    
        # Get selected history timestamp and action
        timestamp, action = self.history_tree.item(selected_items[0], "values")
    
        # Get selected memory ID
        memory_selected = self.tree.selection()
        if not memory_selected:
            return
    
        memory_id = self.tree.item(memory_selected[0], "values")[0]
    
        # Find history entry
        history_entries = self._load_memory_history(memory_id)
        selected_entry = None
    
        for entry in history_entries:
            if entry["timestamp"] == timestamp and entry["action"] == action:
                selected_entry = entry
                break
    
        if not selected_entry:
            return
    
        # Display history details
        self.history_details_text.delete(1.0, tb.END)
    
        # Format history details
        details = f"Acción: {selected_entry['action']}\n"
        details += f"Fecha/Hora: {selected_entry['timestamp']}\n\n"
    
        # Get memory data from history
        memory_data = selected_entry["data"]
    
        # Handle encrypted data
        if memory_data.get("encrypted", False) and self.encryption_key:
            try:
                # Try to decrypt all fields
                content = self._decrypt_data(memory_data.get("content", ""))
                tags = self._decrypt_data(memory_data.get("tags", []))
                source = self._decrypt_data(memory_data.get("source", ""))
                metadata = self._decrypt_data(memory_data.get("metadata", {}))
            
                details += f"Contenido (desencriptado):\n{content}\n\n"
            
                # Format tags
                if isinstance(tags, list) and tags:
                    details += f"Etiquetas (desencriptadas): {', '.join(tags)}\n\n"
                else:
                    details += "Etiquetas: [Ninguna]\n\n"
                
                details += f"Importancia: {memory_data.get('importance', 0)}\n\n"
                details += f"Creado: {memory_data.get('created_at', '')}\n\n"
                details += f"Actualizado: {memory_data.get('updated_at', '')}\n\n"
                details += f"Fuente (desencriptada): {source}\n\n"
            
                # Add metadata
                details += "Metadatos (desencriptados):\n"
                if isinstance(metadata, dict):
                    for key, value in metadata.items():
                        details += f"  {key}: {value}\n"
                else:
                    details += "  [No se pudieron desencriptar los metadatos]\n"
                
            except:
                details += "Contenido: [ENCRIPTADO - No se pudo desencriptar]\n"
                details += "Etiquetas: [ENCRIPTADAS - No se pudieron desencriptar]\n"
                details += "Fuente: [ENCRIPTADA - No se pudo desencriptar]\n"
                details += "Metadatos: [ENCRIPTADOS - No se pudieron desencriptar]\n\n"
        elif memory_data.get("encrypted", False):
            details += "Contenido: [ENCRIPTADO]\n"
            details += "Etiquetas: [ENCRIPTADAS]\n"
            details += "Fuente: [ENCRIPTADA]\n"
            details += "Metadatos: [ENCRIPTADOS]\n\n"
        else:
            details += f"Contenido:\n{memory_data.get('content', '')}\n\n"
        
            # Format tags
            tags = memory_data.get('tags', [])
            if isinstance(tags, list) and tags:
                details += f"Etiquetas: {', '.join(tags)}\n\n"
            else:
                details += "Etiquetas: [Ninguna]\n\n"
            
            details += f"Importancia: {memory_data.get('importance', 0)}\n\n"
            details += f"Creado: {memory_data.get('created_at', '')}\n\n"
            details += f"Actualizado: {memory_data.get('updated_at', '')}\n\n"
            details += f"Fuente: {memory_data.get('source', '')}\n\n"
        
            # Add metadata
            details += "Metadatos:\n"
            for key, value in memory_data.get("metadata", {}).items():
                details += f"  {key}: {value}\n"
    
        self.history_details_text.insert(tb.END, details)
    
    def _export_selected(self):
        """Export selected memory to JSON."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Por favor seleccione una memoria para exportar")
            return
        
        # Get selected memory ID
        memory_id = self.tree.item(selected_items[0], "values")[0]
        
        # Find memory in list
        memory = None
        for mem in self.memories:
            if mem.get("id") == memory_id:
                memory = mem
                break
        
        if not memory:
            return
        
        # Ask for output file
        output_file = filedialog.asksaveasfilename(
            title="Guardar memoria como JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not output_file:
            return
        
        # Export memory
        try:
            with open(output_file, 'w') as f:
                json.dump(memory, f, indent=2)
            messagebox.showinfo("Éxito", f"Memoria exportada a {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar memoria: {e}")
    
    def _export_all(self):
        """Export all memories to JSON."""
        if not self.memories:
            messagebox.showerror("Error", "No hay memorias para exportar")
            return
        
        # Ask for output file
        output_file = filedialog.asksaveasfilename(
            title="Guardar todas las memorias como JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not output_file:
            return
        
        # Export memories
        try:
            with open(output_file, 'w') as f:
                json.dump(self.memories, f, indent=2)
            messagebox.showinfo("Éxito", f"{len(self.memories)} memorias exportadas a {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar memorias: {e}")
    
    def _export_history(self):
        """Export history of selected memory to JSON."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Por favor seleccione una memoria para exportar su historial")
            return
        
        # Get selected memory ID
        memory_id = self.tree.item(selected_items[0], "values")[0]
        
        # Load history
        history_entries = self._load_memory_history(memory_id)
        
        if not history_entries:
            messagebox.showinfo("Información", "No hay historial disponible para esta memoria")
            return
        
        # Ask for output file
        output_file = filedialog.asksaveasfilename(
            title="Guardar historial como JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not output_file:
            return
        
        # Export history
        try:
            # Convert to serializable format
            serializable_history = []
            for entry in history_entries:
                serializable_entry = {
                    "timestamp": entry["timestamp"],
                    "action": entry["action"],
                    "data": entry["data"]
                }
                serializable_history.append(serializable_entry)
                
            with open(output_file, 'w') as f:
                json.dump(serializable_history, f, indent=2)
            messagebox.showinfo("Éxito", f"Historial exportado a {output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar historial: {e}")


if __name__ == "__main__":
    app = MemViewer()
    app.mainloop()

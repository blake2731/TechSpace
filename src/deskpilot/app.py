from __future__ import annotations
import json, os, subprocess, sys, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
APP_TITLE = "DeskPilot"

def human_size(size):
    value=float(size)
    for unit in ["B","KB","MB","GB","TB"]:
        if value < 1024 or unit == "TB": return f"{value:.1f} {unit}"
        value /= 1024

def open_path(path):
    if os.name == "nt": os.startfile(path)
    elif sys.platform == "darwin": subprocess.Popen(["open",str(path)])
    else: subprocess.Popen(["xdg-open",str(path)])

class DeskPilot(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP_TITLE); self.geometry("1050x720"); self.minsize(900,600)
        self.selected_folder=tk.StringVar(value=str(Path.home()/"Downloads")); self.status=tk.StringVar(value="Ready"); self.organize_plan=[]; self.build()
    def build(self):
        outer=ttk.Frame(self,padding=14); outer.pack(fill="both",expand=True)
        h=ttk.Frame(outer); h.pack(fill="x"); ttk.Label(h,text="DeskPilot",font=("Segoe UI",22,"bold")).pack(side="left"); ttk.Label(h,text="Local PC cleanup and file control").pack(side="left",padx=12)
        c=ttk.Frame(outer,padding=(0,12,0,10)); c.pack(fill="x"); ttk.Entry(c,textvariable=self.selected_folder).pack(side="left",fill="x",expand=True); ttk.Button(c,text="Choose Folder",command=self.choose).pack(side="left",padx=8); ttk.Button(c,text="Open Folder",command=self.open_folder).pack(side="left")
        n=ttk.Notebook(outer); n.pack(fill="both",expand=True)
        self.tabs=[ttk.Frame(n,padding=12) for _ in range(5)]
        for tab,name in zip(self.tabs,["Smart Organize","Duplicates","Storage Review","Quick Search","Workspaces"]): n.add(tab,text=name)
        self.build_organize(); self.build_duplicates(); self.build_storage(); self.build_search(); self.build_workspaces(); ttk.Label(outer,textvariable=self.status).pack(anchor="w",pady=(8,0))
    def folder(self):
        p=Path(self.selected_folder.get()).expanduser()
        if not p.is_dir(): messagebox.showerror(APP_TITLE,"Choose a valid folder first."); return None
        return p
    def choose(self):
        p=filedialog.askdirectory(initialdir=self.selected_folder.get())
        if p: self.selected_folder.set(p)
    def open_folder(self):
        p=self.folder()
        if p: open_path(p)
    def tree(self,parent,columns):
        f=ttk.Frame(parent); f.pack(fill="both",expand=True); t=ttk.Treeview(f,columns=list(columns),show="headings")
        for col,width in columns.items(): t.heading(col,text=col); t.column(col,width=width,anchor="w")
        s=ttk.Scrollbar(f,orient="vertical",command=t.yview); t.configure(yscrollcommand=s.set); t.pack(side="left",fill="both",expand=True); s.pack(side="right",fill="y"); return t
    def build_organize(self):
        c=ttk.Frame(self.tabs[0]); c.pack(fill="x",pady=(0,10)); ttk.Button(c,text="Preview Organization",command=self.preview).pack(side="left"); ttk.Button(c,text="Apply Preview",command=self.apply).pack(side="left",padx=8); ttk.Button(c,text="Undo Last Organize",command=self.undo).pack(side="left"); ttk.Label(c,text="Nothing is deleted. Preview first, then move.").pack(side="left",padx=12); self.org=self.tree(self.tabs[0],{"Category":120,"File":280,"Destination":480})
    def preview(self):
        p=self.folder()
        if not p:return
        self.org.delete(*self.org.get_children()); self.organize_plan=core.build_organize_plan(p)
        for x in self.organize_plan:self.org.insert("","end",values=(x.category,x.source.name,str(x.destination)))
        self.status.set(f"Previewed {len(self.organize_plan)} file moves")
    def apply(self):
        if not self.organize_plan: messagebox.showinfo(APP_TITLE,"Run Preview Organization first."); return
        if not messagebox.askyesno(APP_TITLE,f"Move {len(self.organize_plan)} files according to this preview?"):return
        u=core.apply_organize_plan(self.organize_plan); count=len(self.organize_plan); self.organize_plan=[]; self.org.delete(*self.org.get_children()); self.status.set(f"Moved {count} files. Undo record: {u}")
    def undo(self):
        u=core.latest_undo_file()
        if not u: messagebox.showinfo(APP_TITLE,"There is no organize operation to undo."); return
        count,problems=core.undo_file_moves(u); messagebox.showinfo(APP_TITLE,f"Restored {count} files." if not problems else f"Restored {count} files. Some items could not be restored."); self.status.set(f"Undo restored {count} files")
    def build_duplicates(self):
        c=ttk.Frame(self.tabs[1]); c.pack(fill="x",pady=(0,10)); ttk.Button(c,text="Scan Exact Duplicates",command=self.dupes).pack(side="left"); ttk.Label(c,text="Reports only. Never deletes.").pack(side="left",padx=12); self.dup=self.tree(self.tabs[1],{"Group":70,"Size":100,"File":650})
    def dupes(self):
        p=self.folder()
        if not p:return
        self.status.set("Scanning duplicates..."); self.update_idletasks(); groups=core.find_duplicates(p); self.dup.delete(*self.dup.get_children()); wasted=0
        for i,g in enumerate(groups,1):
            size=g[0].stat().st_size; wasted += size*(len(g)-1)
            for path in g:self.dup.insert("","end",values=(i,human_size(size),str(path)))
        self.status.set(f"Found {len(groups)} duplicate groups. Potential duplicate space: {human_size(wasted)}")
    def build_storage(self):
        c=ttk.Frame(self.tabs[2]); c.pack(fill="x",pady=(0,10)); self.mb=tk.StringVar(value="100"); self.days=tk.StringVar(value="90"); ttk.Label(c,text="Minimum MB").pack(side="left"); ttk.Entry(c,width=8,textvariable=self.mb).pack(side="left",padx=5); ttk.Label(c,text="Older than days").pack(side="left",padx=(10,0)); ttk.Entry(c,width=8,textvariable=self.days).pack(side="left",padx=5); ttk.Button(c,text="Find Large Stale Files",command=self.storage).pack(side="left",padx=8); self.stor=self.tree(self.tabs[2],{"Size":110,"Modified":150,"File":650})
    def storage(self):
        p=self.folder()
        if not p:return
        try:r=core.large_stale_files(p,max(1,int(self.mb.get())),max(0,int(self.days.get())))
        except ValueError:messagebox.showerror(APP_TITLE,"Use whole numbers.");return
        self.stor.delete(*self.stor.get_children())
        for path,size,modified in r:self.stor.insert("","end",values=(human_size(size),modified.strftime("%Y-%m-%d"),str(path)))
        self.status.set(f"Found {len(r)} review candidates totaling {human_size(sum(x[1] for x in r))}")
    def build_search(self):
        c=ttk.Frame(self.tabs[3]); c.pack(fill="x",pady=(0,10)); self.q=tk.StringVar(); e=ttk.Entry(c,textvariable=self.q); e.pack(side="left",fill="x",expand=True); e.bind("<Return>",lambda _:self.search()); ttk.Button(c,text="Search Filenames",command=self.search).pack(side="left",padx=8); ttk.Button(c,text="Open Selected",command=self.open_result).pack(side="left"); self.results=self.tree(self.tabs[3],{"Name":280,"Folder":600})
    def search(self):
        p=self.folder()
        if not p:return
        r=core.quick_search(p,self.q.get()); self.results.delete(*self.results.get_children())
        for x in r:self.results.insert("","end",values=(x.name,str(x.parent)))
        self.status.set(f"Found {len(r)} matches")
    def open_result(self):
        s=self.results.selection()
        if s:
            v=self.results.item(s[0],"values"); p=Path(v[1])/v[0]
            if p.exists():open_path(p)
    def workspace_file(self):return core.app_data_dir()/"workspaces.json"
    def load_ws(self):
        try:return json.loads(self.workspace_file().read_text(encoding="utf-8"))
        except:return []
    def save_ws(self,x):self.workspace_file().write_text(json.dumps(x,indent=2),encoding="utf-8")
    def build_workspaces(self):
        c=ttk.Frame(self.tabs[4]); c.pack(fill="x",pady=(0,10)); ttk.Button(c,text="Add Current Folder",command=self.add_ws).pack(side="left"); ttk.Button(c,text="Open Selected",command=self.open_ws).pack(side="left",padx=8); ttk.Button(c,text="Remove Selected",command=self.remove_ws).pack(side="left"); self.ws=self.tree(self.tabs[4],{"Name":220,"Folder":650}); self.refresh_ws()
    def refresh_ws(self):
        self.ws.delete(*self.ws.get_children())
        for x in self.load_ws():self.ws.insert("","end",values=(x["name"],x["path"]))
    def add_ws(self):
        p=self.folder()
        if not p:return
        x=self.load_ws()
        if not any(i["path"]==str(p) for i in x):x.append({"name":p.name or str(p),"path":str(p)});self.save_ws(x);self.refresh_ws()
    def open_ws(self):
        s=self.ws.selection()
        if s:
            p=Path(self.ws.item(s[0],"values")[1])
            if p.exists():open_path(p)
    def remove_ws(self):
        s=self.ws.selection()
        if s:
            target=self.ws.item(s[0],"values")[1];self.save_ws([x for x in self.load_ws() if x["path"]!=target]);self.refresh_ws()
if __name__ == "__main__": DeskPilot().mainloop()

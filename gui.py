import wx
import requests
import mimetypes
import json
from requests_toolbelt.multipart.encoder import MultipartEncoderMonitor
from pathlib import Path
from threading import Thread
from pubsub import pub
from post_editor import Post
import sys
import os

def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


class LoginDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.SetSize(300, 240)
        self.SetIcon(wx.Icon(getResourcePath("favicon.ico")))

        vb = wx.BoxSizer(wx.VERTICAL)
        self.emailOrToken = wx.RadioBox(self, id=wx.ID_ANY, label="Login Type", choices=['Email', 'Token'], style=wx.RA_SPECIFY_COLS)
        self.emailOrToken.Bind(wx.EVT_RADIOBOX, self.changeLoginType)
        vb.Add(self.emailOrToken, flag=wx.EXPAND | wx.ALL, border=10)

        hb = wx.BoxSizer(wx.HORIZONTAL)
        self.emailText = wx.TextCtrl(self)
        self.emailText.SetHint('Email...')
        self.passwordText = wx.TextCtrl(self)
        self.passwordText.SetHint('Password...')
        hb.Add(self.emailText, 1, flag=wx.EXPAND | wx.ALL, border=10)
        hb.Add(self.passwordText, 1, flag=wx.EXPAND | wx.ALL, border=10)

        vb.Add(hb, flag=wx.EXPAND | wx.ALL, border=10)

        hb2 = wx.BoxSizer(wx.HORIZONTAL)
        bOk = wx.Button(self, wx.ID_ANY, label='Login', size=wx.DefaultSize)
        bOk.Bind(wx.EVT_BUTTON, self.LoginClick)
        bCn = wx.Button(self, wx.ID_CANCEL, label='Cancel', size=wx.DefaultSize)
        hb2.Add(bOk, 1, flag=wx.EXPAND | wx.ALL, border=10)
        hb2.Add(bCn, 1, flag=wx.EXPAND | wx.ALL, border=10)

        vb.Add(hb2, flag=wx.EXPAND | wx.ALL, border=10)

        self.SetSizer(vb)
        self.Centre(wx.BOTH)

    def LoginClick(self, event):
        if self.emailOrToken.GetSelection() and len(self.emailText.Value) > 60:
            r = requests.get("https://dtf.ru/auth/check?mode=raw", data={"mode": "raw"}, cookies={'osnova-remember': self.emailText.Value}).json()
            if r['rc'] == 200:
                with open('settings.json', 'w') as f:
                    f.write(json.dumps({'osnova-remember': self.emailText.Value}))
                self.Parent.post = Post(cookies_file='settings.json')
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox('Неправильные данные.', 'Info', wx.OK_DEFAULT, parent=self)
                self.emailText.Clear()
        elif not self.emailOrToken.GetSelection() and self.emailText.Value and self.passwordText.Value:
            r = requests.post("https://dtf.ru/auth/simple/login", data={"values[login]": self.emailText.Value, "values[password]": self.passwordText.Value, "mode": "raw"}, headers={"x-this-is-csrf": "THIS IS SPARTA!"})
            r_json = r.json()
            print(r_json)
            if r_json.get('rc', 400) == 200:
                with open('settings.json', 'w') as f:
                    f.write(json.dumps({'osnova-remember': r.cookies.get_dict().get('osnova-remember')}))
                self.Parent.post = Post(cookies_file='settings.json')
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox('Неправильные данные.', 'Info', wx.OK_DEFAULT, parent=self)
                self.emailText.Clear()
                self.passwordText.Clear()
        else:
            wx.MessageBox('Неправильные данные.', 'Info', wx.OK_DEFAULT, parent=self)

    def changeLoginType(self, event):
        if self.emailOrToken.GetSelection():
            self.emailText.SetHint('Token...')
            self.emailText.Clear()
            self.passwordText.Hide()
            self.Layout()
        else:
            self.emailText.SetHint('Email...')
            self.emailText.Clear()
            self.passwordText.Clear()
            self.passwordText.Show()
            self.Layout()

class DownloadThread(Thread):
    """Downloading thread"""
    #----------------------------------------------------------------------
    def __init__(self, uploadSize, uploadFiles):
        """Constructor"""
        Thread.__init__(self)
        self.uploadSize = uploadSize
        self.uploadFiles = uploadFiles
        self.limit = 10
        self.start()
    
    def my_callback(self, monitor):
        wx.CallAfter(pub.sendMessage, f"update_upload", count=8192) 

    #----------------------------------------------------------------------
    def run(self):
        """
        Run the worker thread
        """
        # wx.MilliSleep(50)
        # for f in self.uploadFiles
        # mimetypes.guess_type(path_file_to_upload)[1]
        upl_imgs = list()
        my_list_chunks = [self.uploadFiles[i * self.limit:(i + 1) * self.limit] for i in range((len(self.uploadFiles) + self.limit - 1) // self.limit)]
        for img_slice in my_list_chunks:
            m = MultipartEncoderMonitor.from_fields(
                fields={
                    f'file_{i}': ('filename', open(fPath, 'rb'), mimetypes.guess_type(str(fPath))[1]) for i, fPath in enumerate(img_slice)
                }, callback=self.my_callback
            )
            images = requests.post('https://dtf.ru/andropov/upload', data=m, headers={'Content-Type': m.content_type, "x-this-is-csrf": "THIS IS SPARTA!"}).json()
            print(images)
            upl_imgs.extend(images['result'])
            # wx.CallAfter(pub.sendMessage, f"update_upload", count=self.uploadSize)
        wx.CallAfter(pub.sendMessage, f"update_upload", count=self.uploadSize)
        wx.CallAfter(pub.sendMessage, f"upload_complete", img_list=zip(map(lambda x: x.name.split('.')[0], self.uploadFiles), upl_imgs))

#---------------------------------------------------------------------------

def getResourcePath(filename):
    try:
        basePath = sys._MEIPASS
    except Exception:
        basePath = ''
    path = os.path.join(basePath, filename)
    print(path)
    return path

#---------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, pos = wx.DefaultPosition, size = wx.Size(290, 140), style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX|wx.TAB_TRAVERSAL)
        self.SetIcon(wx.Icon(getResourcePath("favicon.ico")))
        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        self.panel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        panelSizer = wx.BoxSizer( wx.VERTICAL )

        self.browseButton = wx.Button( self.panel, wx.ID_ANY, u"Choose Folder", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.browseButton.Bind(wx.EVT_BUTTON, self.ChooseButton)
        panelSizer.Add(self.browseButton, 1, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL|wx.SHAPED, border=5)

        bSizer = wx.BoxSizer( wx.HORIZONTAL )

        self.recursiveCheck = wx.CheckBox(self.panel, wx.ID_ANY, u"Recursive", wx.DefaultPosition, wx.DefaultSize, 0)
        self.recursiveCheck.Bind(wx.EVT_CHECKBOX, self.RecursiveChange)
        bSizer.Add(self.recursiveCheck, 1, wx.ALL|wx.EXPAND, 5)

        self.uploadButton = wx.Button(self.panel, wx.ID_ANY, u"Upload", wx.DefaultPosition, wx.DefaultSize, 0)
        self.uploadButton.Bind(wx.EVT_BUTTON, self.OnButton)
        bSizer.Add(self.uploadButton, 1, wx.ALL|wx.EXPAND, 5)

        panelSizer.Add(bSizer, 1, wx.EXPAND, 0)

        panelSizer.Fit(self.panel)

        self.panel.SetSizer(panelSizer)
        self.Layout()
        self.statusBar = self.CreateStatusBar(1, wx.STB_SIZEGRIP, wx.ID_ANY)
        self.statusBar.SetStatusText('Waiting...')

        self.Centre(wx.BOTH)

        self.max = 100
        self.uploadDir = None
        self.recursive = False
        self.uploadSize = 0
        self.uploaded = 0
        self.fileList = list()

        self.post = None

        self.TryToLogin()

        while not self.post:
            with LoginDialog(self, title='Login', style= wx.CAPTION | wx.CLOSE_BOX) as dlg:
                res = dlg.ShowModal()
                if res == wx.ID_CANCEL:
                    self.Close()
                    self.Destroy()
                    break
                elif res == wx.ID_OK:
                    self.Show()

    def TryToLogin(self):
        if Path('settings.json').is_file():
            with open('settings.json', 'r') as f:
                try:
                    env_j = json.load(f)
                    self.post = Post(cookies_file='settings.json')
                    if self.post.check_auth():
                        self.Show()
                    else:
                        wx.MessageBox('Неправильные данные.', 'Info', wx.OK_DEFAULT, parent=self)
                        self.post = None
                except json.decoder.JSONDecodeError:
                    wx.MessageBox('Файл поврежден.', 'Info', wx.OK_DEFAULT, parent=self)
                    self.post = None

    def RecursiveChange(self, event):
        self.recursive = self.recursiveCheck.IsChecked()
        self.FolderFilesCount()

    def FolderFilesCount(self):
        if self.uploadDir:
            self.fileList.clear()
            self.uploadSize = 0
            for extension in ('*.jfif', '*.jpeg', '*.jpg', '*.png', '*.webp'):
                if self.recursive:
                    self.fileList.extend(Path(self.uploadDir).rglob(extension))
                else:
                    self.fileList.extend(Path(self.uploadDir).glob(extension))
            for f in self.fileList:
                self.uploadSize += f.stat().st_size
            self.statusBar.SetStatusText(f'Found {len(self.fileList)} files. {convert_bytes(self.uploadSize)}')

    def ChooseButton(self, event):
        selector = wx.DirSelector("Choose a folder")
        folder_path = selector.strip()
        if folder_path:
            print(folder_path)
            self.uploadDir = folder_path
            self.FolderFilesCount()
        else:
            self.uploadDir = None
            self.statusBar.SetStatusText('Waiting...')

    def OnButton(self, event):
        self.uploadSize += 8192 * len(self.fileList)
        self.uploaded = 0
        if not self.uploadDir:
            wx.MessageBox('Пожалуйста, выберите папку.', 'Info', wx.OK_DEFAULT, parent=self)
            return

        self.dlg = wx.ProgressDialog("Загружаю...",
                               "Подождите окончания загрузки",
                               maximum = self.uploadSize,
                               parent=self,
                               style = 0
                                | wx.PD_APP_MODAL
                                #| wx.PD_CAN_ABORT
                                #| wx.PD_CAN_SKIP
                                #| wx.PD_ELAPSED_TIME
                                | wx.PD_ESTIMATED_TIME
                                | wx.PD_REMAINING_TIME
                                #| wx.PD_AUTO_HIDE
                                )

        pub.subscribe(self.updateProgress, f"update_upload")
        pub.subscribe(self.uploadComplete, f"upload_complete")

        DownloadThread(self.uploadSize, self.fileList)

    def uploadComplete(self, img_list):
        self.post.subsite_id = self.post.user_id
        self.post.add_media_list(img_list, cover_count=2)
        self.post.add_text_block('#wxPythonProstagma', anchor='wxPythonProstagma', cover=False)
        self.post.save_draft()

   
    def updateProgress(self, count):
        """"""
        self.uploaded += count
        if self.uploaded >= self.uploadSize:
            print('DIE')
            (keepGoing, skip) = self.dlg.Update(self.uploadSize)
            print('DIE')
            self.dlg.Destroy()
            self.uploadDir = None
            self.statusBar.SetStatusText('Waiting...')
        else:
            (keepGoing, skip) = self.dlg.Update(self.uploaded)
        print(keepGoing, skip, count)
        

#---------------------------------------------------------------------------


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame(None, title='DTF uploader v1.0')
    # frame.Show()
    app.MainLoop()

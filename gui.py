import wx
import requests
import mimetypes
from requests_toolbelt.multipart.encoder import MultipartEncoderMonitor
from pathlib import Path
from threading import Thread
from pubsub import pub
from post_editor import Post

def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

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

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super().__init__(parent, title=title, pos = wx.DefaultPosition, size = wx.Size(290, 140), style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX|wx.TAB_TRAVERSAL)
        self.SetIcon(wx.Icon("favicon.ico"))
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
        test_post = Post('test', 74342)
        r = test_post.session.get("https://dtf.ru/auth/check?mode=raw", data={"mode": "raw"}).json()
        test_post.subsite_id = r['data']['id']
        test_post.add_media_list(img_list, cover_count=2)
        test_post.add_text_block('#wxPythonProstagma', anchor='wxPythonProstagma', cover=False)
        test_post.save_draft()

   
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
    frame = MyFrame(None, 'DTF uploader v1.0')
    frame.Show()
    app.MainLoop()

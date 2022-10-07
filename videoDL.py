from __future__ import unicode_literals
import re,gc,os,sys,time,argparse
from yt_dlp.utils import DateRange
import yt_dlp,threading,subprocess
class MyLogger(object):
    def __init__(self):
        self.downloading=False
    def debug(self, msg):
        global title
        title["curItem"]=vd1.ydlOpts["playliststart"]
        title["Total"]=vd1.playlistTotal
        os.system('title "%s"'%(";  ".join(k + ": " + str(v) for k,v in title.items())))
        if re.findall("Download aborted",msg):return
        cmdWidth=os.get_terminal_size().columns
        if re.findall(r"\[download\] 100% of .*in.*",msg,re.I):
            self.downloading=False
            print("\r"+msg," "*(cmdWidth-len(msg)-10))
            return
        elif re.findall(r"\[download\] *[\d.]{1,5}% of",msg,re.I):
            self.downloading=True
            print("\r"+msg," "*(cmdWidth-len(msg)-10),end="")
            return
        elif re.findall(r"\[download\] Destination:",msg,re.I):
            self.downloading=True
            print(msg)
            return
        elif re.findall("\[aria2c\] Downloaded",msg,re.I):
            print(msg," "*(cmdWidth-len(msg)-10))
        else:
            if re.findall(r"title matched reject pattern|title did not match pattern|upload date is not in range|skip\.\.\.",msg):
                vd1.resetStart()
            if re.findall(r"upload date is not in range",msg) and vd1.dateskip:
                self.printMsg(msg)
                print("skip other parts of this playlist!!!")
                raise Exception("dateskip")
            if vd1.playlistTotal==1 and re.findall(r"Downloading (\d{1,3}) videos",msg):
                vd1.playlistTotal=int(re.findall(r"Downloading (\d{1,3}) videos",msg)[0])+vd1.ydlOpts["playliststart"]-1
            if re.findall(r"\[download\] Downloading video .*(\d{1,4}).* of .*(\d{1,4}).*",msg,re.I):
                msg="[download] Downloading video %d of %d"%(vd1.ydlOpts["playliststart"],vd1.playlistTotal)
            self.printMsg(msg)
    def warning(self, msg):
        if re.findall(r"Video unavailable",msg):vd1.resetStart()
        if re.findall("unable to extract view count|nsig extraction failed|Unable to download webpage|yt-dlp -U|No video formats found|Requested format is not available",msg,re.I):return
        if "warning" in msg:msg=re.sub(r"warning",r"[\033[33mwarning\033[0m] ",msg,flags=re.I)
        else:msg="[\033[33mwarning\033[0m] "+msg
        self.printMsg(msg)
    def error(self, msg):
        file=re.findall(r"Postprocessing: file:(.*): Invalid data found when processing input",msg,re.DOTALL)
        if file and os.path.exist(file[0]):os.remove(file[0])
        if re.findall(r"HTTP Error 404: Not Found|Unable to open fragment|This live event will begin|Unable to extract .*iframe URL.*|Unable to extract .*encoded.* url|Unsupported URL|This video has been removed|Video unavailable|upload date is not in range|TypeError: the JSON object must be str, not 'NoneType'|said: This video has been disabled|TypeError: the JSON object must be str, not 'NoneType'|YouTube said: Unable to extract video data|This video has been removed|Unable to extract JS player URL",msg,re.I):
            vd1.resetStart()
        if re.findall("ERROR:",msg):
            msg=re.sub(".*?ERROR:",r"[\033[31mERROR\033[0m]",msg,flags=re.DOTALL)
        self.printMsg(msg)
        time.sleep(4)
    def printMsg(self,msg):
        if len(msg) >= 2:
            msg=msg[0]+re.sub("\n[^\-]"," ",msg[1:-1])+msg[-1]
        if self.downloading:print("\n"+msg)
        else:print(msg)
        self.downloading=False

class MyCustomPP(yt_dlp.postprocessor.common.PostProcessor):
    def run(self, info):
        vd1.resetStart()
        # self.to_screen('-------- '*6)
        if vd1.playlistTotal!=1:
            print('-------- '*6)
        return [], info

class VideoDownload():
    def __init__(self,proxy="127.0.0.1:10909",root=".",searchMPath="."):
        self.root=root
        self.searchMPath=searchMPath
        self.dateskip=False
        self.ydlOptsTemple = {
            "age_limit":30,
            "socket_timeout":"20",
            "proxy":proxy,
            # "proxy":"socks5://127.0.0.1:8080"
            'format':"bestvideo+bestaudio/best",
            "format_sort":["lang","res","vbr","codec","fps","channels"],
            # 'format':"308+251",
            # 'format':"bestvideo+bestaudio/best[ext=mp4]/best",
            # "ignoreerrors":True,
            # "matchtitle":"【MMD/60fps】",#支持正则
            # "rejecttitle":"",
            # "daterange":DateRange("20221111",None),
            "playliststart":1,
            "noplaylist":False,
            # "merge_output_format":"mkv",
            # "verbose":True,
            "nocheckcertificate":True,
            "cookiesfrombrowser":('chrome', ),
            'external_downloader':'aria2c.exe',
            'external_downloader_args':["-x","16","-k","1M","--file-allocation=none","--log-level=warn","--check-certificate=false","--console-log-level=warn","--summary-interval=0","--download-result=hide"],
            # "ffmpeg_location":'ffmpeg.exe',
            # "outtmpl":root.strip("/")+"/%(uploader)s/%(title)s-%(id)s.%(ext)s",
            'logger': MyLogger(),
            "match_filter":self.matchFilterFunc(),
            'progress_hooks': [self.myHook],
            "no_warnings":True,
            # "writethumbnail":True,
            'quiet': True,            # 这个参数为真则不输出提示信息
            "ignore_no_formats_error":True,
            # 'keepvideo': True,     # 默认视频转换成音频后删掉视频文件，设置为True后不删除视频，测试时反复运行，视频不必每次都下载
            # 'postprocessors': [
            #             {
            #              'key': 'FFmpegExtractAudio',     # 指定用FFmpeg从视频中提取音频
            #              'preferredcodec': 'mp3',         # 指定目标音频格式
            #             },
            #                    ],
            #        }
        }

    def initParams(self,params):
        self.ydlOpts=self.ydlOptsTemple.copy()
        self.ydlOpts["playliststart"]=1
        self.playlistTotal=1
        tmpydlOpts=str(self.ydlOpts.items())
        if params and params[0]:
            params=" "+params[0].lower()
            # 过滤
            if re.findall(r' f [\"\']([^\"]*)[\"\'] [\"\']([^\"]*)[\"\']',params):
                p1,p2=re.findall(r' f [\"\']([^\"]*)[\"\'] [\"\']([^\"]*)[\"\']',params)[0]
                self.ydlOpts["rejecttitle"]=p1 if p1 else None
                self.ydlOpts["matchtitle"]=p2 if p2 else None
            # 下载列表中的项目
            if re.findall(r' i [\"\']?([^ ]*)[\"\']?',params):
                p1=re.findall(r' i [\"\']?([^ ]*)[\"\']?',params)[0]
                items=[]
                for param in p1.split(","):
                    if "-" in param:
                        s,e=param.split("-")
                        if all((s.isnumeric(),e.isnumeric())) and len(p1.split(","))>1:
                            for item in range(int(s),int(e)+1):items.append(item)
                        elif len(p1.split(","))==1:
                            self.ydlOpts["playliststart"]=int(s) if s else 1
                            self.ydlOpts["playlistend"]=int(e) if e else -1
                    else:
                        if param.isnumeric():
                            items.append(int(param))
                if items:
                    items.sort()
                    self.ydlOpts["playlist_items"]=",".join([str(item) for item in items])
            # 不下载列表
            if re.findall(r" n\b",params):
                self.ydlOpts["noplaylist"]=True
            # 限制下载日期
            if re.findall(r' d ((?:-\d{8}|\d{8}-\d{8}|\d{8}|\d{8}-))(?:$|[^\d\-])',params):
                self.dateskip=False
                p1=re.findall(r' d(?:s | )((?:-\d{8}|\d{8}-\d{8}|\d{8}|\d{8}-))(?:$|[^\d\-])',params)[0].split('-',1)
                if not p1[1:]:
                    self.ydlOpts["daterange"]=DateRange(p1[0] if p1[0] else None,p1[0])
                else:
                    self.ydlOpts["daterange"]=DateRange(p1[0] if p1[0] else None,p1[1] if p1[1:] and p1[1] else None)
                if re.findall(r' ds ((?:-\d{8}|\d{8}-\d{8}|\d{8}|\d{8}-))(?:$|[^\d\-])',params):
                    self.dateskip=True
            # 设置代理
            if re.findall(r" p (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,6})| p (no)\b",params):
                p1,p2=re.findall(r" p (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,6})| p (no)\b",params)[0]
                self.ydlOpts["proxy"]=p1 if p1 else None

            if tmpydlOpts==str(self.ydlOpts.items()):
                print("无效参数,跳过")
                return

    def resetStart(self):
        self.ydlOpts["playliststart"]+=1
        if "playlist_items" in self.ydlOpts:
            self.ydlOpts["playlist_items"]=re.sub("^\d*,","",self.ydlOpts["playlist_items"])

    def myHook(self,d):
        if d['status'] == 'finished':
            pass

    def matchFilterFunc(self):
        def _match_func(infoDict):
            if infoDict.get("is_live",False):
                return "%s is live, skip..."%infoDict["uploader"] +"\n"+ '-------- '*6
            if infoDict["uploader"] in ("Sorrow Hill","MMD Girls Studio"):
                return "this uploader is %s, and skip..."%infoDict["uploader"] +"\n"+ '-------- '*6
            for path in self.searchMPath:
                for ext in ("webm","mkv",infoDict["ext"]):
                    file=os.path.join(path,infoDict["webpage_url_domain"],
                        infoDict["uploader"].replace("|","｜").replace("/","⧸").replace('"','＂'),
                        infoDict["title"].replace("|","｜").replace("/","⧸").replace('"','＂')+"-"+infoDict["id"]+"."+ext)
                    if os.path.exists(file):
                        return "%s has already been downloaded and merged, skip..."%file +"\n"+ '-------- '*6
            return None
        return _match_func

    def download(self,url):
        # if re.findall("youtube",url,re.I):
        #     self.ydlOpts.setdefault("cookiefile","cookies.txt")
        while True:
            try:
                ytdl=yt_dlp
                if re.findall("iwara",url,re.I):self.ydlOpts["format_sort"]=[]
                self.ydlOpts["outtmpl"]=self.root.strip("/")+"/%(webpage_url_domain)s/%(uploader)s/%(title)s-%(id)s.%(ext)s"
                with ytdl.YoutubeDL(self.ydlOpts) as ydl:
                    ydl.add_post_processor(MyCustomPP())
                    ydl.download([url])
                print("")
                break
            except Exception as ex:
                if "ytdl" in globals():
                    ydl.cache.remove()
                    del ydl
                    gc.collect()
                if self.playlistTotal==1:
                    if re.findall("HTTP Error 404: Not Found|Unable to open fragment|Unable to extract .*iframe URL.*|Video unavailable|This video has been removed|Unsupported URL",str(ex.args)):
                        break
                if re.findall("dateskip",str(ex.args)):
                    break


if __name__=="__main__":    
    playListFile="playlist.txt"
    savePath=r"h:\youtube-dl"
    searchMPath=(r"H:\youtube-dl\OK",savePath,r"D:\youtube-dl")
    proxy="127.0.0.1:10909"
    # proxy=None
    lineNums=[]
    title={}
    if len(sys.argv)==2:
        for num in sys.argv[1].split(","):
            num=num.strip("\n").strip('"').strip(",").strip(" ")
            if not num:continue
            if "-" in num:
                s,e=num.split("-")
                if e=="":
                    lineNums.append(int(s))
                    lineNums.append("e")
                    continue
                if s=="":
                    lineNums.append(int(e))
                    lineNums.append("s")
                if s.isnumeric() and e.isnumeric():
                    for i in range(int(s),int(e)+1):
                        lineNums.append(i)
            else:
                lineNums.append(int(num))
        title["allLines"]="[ "+sys.argv[1]+ " ]"
    elif len(sys.argv)>2:
        for argv in sys.argv[1:]:
            argv=argv.strip('"').strip(" ")
            if argv:
                os.system('start cmd /k "chcp 65001&python %s %s"'%(sys.argv[0], argv))
    else:
        title["allLines"]="[ 1-n ]"
    os.system("chcp 65001 >nul")
    vd1 = VideoDownload(proxy=proxy,root=savePath,searchMPath=searchMPath)
    try:
        for lineNum,linkInfo in enumerate(open(playListFile,mode="r",encoding="utf-8"),1):
            linkInfo=linkInfo.strip()
            if not linkInfo.startswith("http"):continue
            if len(sys.argv)==1 or lineNum in lineNums or "s" in lineNums and lineNums[lineNums.index("s")-1] >= lineNum or "e" in lineNums and lineNums[lineNums.index("e")-1] <= lineNum:
                linkInfo=linkInfo.split(" ",1)
                print("######## "*6,"\n"+linkInfo[0],"\n")
                title["curLine"]=lineNum
                try:
                    vd1.initParams(linkInfo[1:])
                    vd1.download(linkInfo[0])
                except Exception as ex:
                    print(ex)
                except KeyboardInterrupt:
                    print("用户强制结束......")
                    break
        if len(sys.argv)==2:
            print(title["allLines"],"----> 完成")
    except UnicodeDecodeError:pass



# result = ydl.extract_info(   
#                videoPage,          # 视频链接
#                download=False,     # 不下载只是抽取信息 
# )
# if 'entries' in result:                # 为真说明是播放列表或一系列视频
#     downloadVideos = result['entries']  # downloadVideos获得视频列表
#     print('提取了如下视频信息：')
#     for video in downloadVideos:       # 循环变量video遍历视频列表
#         print('=================================================')
#         print("标题：{}\n扩展名：{}\nid：{}\n网址：{}".format(video['title'], video['ext'], video['id'], video['webpage_url']))
#         # 输出指定视频信息
# else:                         # 说明是一个视频
#     downloadVideo = result
#     print('====================================================')
#     print('一枝独秀：{}.{}'.format(downloadVideo['title'], downloadVideo['ext']))      # 输出这个视频的视频信息



# class VideoDownload2():
#     def __init__(self,proxy="127.0.0.1:10909",root="."):
#         self.lock=threading.Lock()
#         self.downloading=False
#         self.root=root
#         self.ydlOptsTemple = {
#             "socket-timeout":"20",
#             "playlist-start":1,
#             "age-limit":"20",
#             # "buffer-size":"1024",
#             # "retries":"10",
#             # "fragment-retries":10,
#             "format":"bestvideo+bestaudio/best",
#             # 'format':"bestvideo+bestaudio/best[ext=mp4]/best",
#             "merge-output-format":"mkv",
#             "external-downloader":"aria2c.exe",
#             "external-downloader-args":'aria2c:"-x 16 -k 1M --file-allocation=none --log-level=warn --check-certificate=false --file-allocation=none --check-certificate=false --console-log-level=warn --summary-interval=0 --download-result=hide"',
#             "output":root.strip("/")+"/%(webpage_url_domain)s/%(uploader)s/%(title)s-%(id)s.%(ext)s",
#             "cookies-from-browser":"chrome" ,
#             "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36",
#             # "add-header":"",
#             # "ffmpeg-location":"",
#             "exec":"echo {} >nul",
#             # "exec-before-download":"",
#             "proxy":proxy,
#             "console-title":"",
#             # "verbose":"",
#             # "encoding":"utf-8",
#             "no-warnings":"",
#             "progress":"",
#         }

#         # "abort-on-unavailable-fragment"
#         # "skip-unavailable-fragments"
#         # "no-warnings"
#         # "no-progress"
#         # "newline"
#         # "print-traffic"

#     def initParams(self,params):
#         # if re.findall("youtube",url,re.I):
#         #     self.ydlOpts.setdefault("cookiefile","cookies.txt")
#         # if re.findall("vimeo",url,re.I):
#         #     self.ydlOpts.setdefault("cookiefile","vimeoCookie.txt")
#         # if re.findall(r"youtube|iwara|",url,re.I):
#         #     ydlOpts.setdefault("proxy","127.0.0.1:10909")
#         self.ydlOpts=self.ydlOptsTemple.copy()
#         self.ydlOpts["playlist-start"]=1
#         self.playlistTotal=1
#         tmpydlOpts=str(self.ydlOpts.items())
#         if params and params[0]:
#             params=" "+params[0].lower()
#             if re.findall(r' f [\"\']([^\"]*)[\"\'] [\"\']([^\"]*)[\"\']',params):
#                 p1,p2=re.findall(r' f [\"\']([^\"]*)[\"\'] [\"\']([^\"]*)[\"\']',params)[0]
#                 self.ydlOpts["reject-title"]=p1 if p1 else None
#                 self.ydlOpts["match-title"]=p2 if p2 else None
#             if re.findall(r' i [\"\']?([^ ]*)[\"\']?',params):
#                 p1=re.findall(r' i [\"\']?([^ ]*)[\"\']?',params)[0]
#                 items=[]
#                 for param in p1.split(","):
#                     if "-" in param:
#                         s,e=param.split("-")
#                         if all((s.isnumeric(),e.isnumeric())) and len(p1.split(","))>1:
#                             for item in range(int(s),int(e)+1):items.append(item)
#                         elif len(p1.split(","))==1:
#                             self.ydlOpts["playlist-start"]=int(s) if s else 1
#                             self.ydlOpts["playlist-end"]=int(e) if e else -1
#                     else:
#                         if param.isnumeric():
#                             items.append(int(param))
#                 if items:
#                     items.sort()
#                     self.ydlOpts["playlist-items"]=",".join([str(item) for item in items])
#             if re.findall(r" n ",params):
#                 self.ydlOpts["no-playlist"]=""
#             if re.findall(r' d ((?:-\d{8}|\d{8}-\d{8}|\d{8}|\d{8}-))(?:$|[^\d\-])',params):
#                 p1=re.findall(r' d ((?:-\d{8}|\d{8}-\d{8}|\d{8}|\d{8}-))(?:$|[^\d\-])',params)[0].split('-',1)
#                 if not p1[1:]:
#                     self.ydlOpts["datebefore"]=p1[0]
#                 else:
#                     if p1[1]:
#                         self.ydlOpts["datebefore"]=p1[1]
#                 if p1[0]:
#                     self.ydlOpts["dateafter"]=p1[0]
#             if tmpydlOpts==str(self.ydlOpts.items()):
#                 print("无效参数,跳过")
#                 return

#     def resetStart(self):
#         self.ydlOpts["playlist-start"]+=1
#         if "playlist-items" in self.ydlOpts:
#             self.ydlOpts["playlist-items"]=re.sub("^\d*,","",self.ydlOpts["playlist-items"])

#     def download(self,url):
#         while True:
#             cmd="yt-dlp.exe"
#             params=""
#             for k,v in self.ydlOpts.items():
#                 if str(v).isnumeric() or k == "external-downloader-args" or str(v)=="":
#                     params+=" --" + k + " " + str(v)
#                 else:
#                     params+=" --" + k + " " + '"'+ str(v) + '"'
#             self.errMsg=""
#             self.popen=subprocess.Popen('%s %s "%s"'%(cmd, params, url),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
#             infoTh=threading.Thread(target=self.msgProcess,args=(self.popen.stdout.readline,"info"),daemon=True)
#             errTh=threading.Thread(target=self.msgProcess,args=(self.popen.stderr.readline,"error"),daemon=True)
#             infoTh.start()
#             errTh.start()
#             rCode=self.popen.wait()
#             if rCode==0:
#                 break
#             else:
#                 if self.playlistTotal==1:
#                     if re.findall("Unable to extract iframe URL|Video unavailable|This video has been removed|Unsupported URL",self.errMsg):
#                         break

#     def msgProcess(self,readline,msgtype):
#         while True:
#             try:
#                 msg=readline().decode('cp936')
#                 # for msg in iter(readline,""):
#                 if len(msg)==0:break
#                 msg=msg.strip("\n")
#                 if not msg:continue
#                 if not re.findall("\w",msg):continue
#                 self.setConsoleTitle()
#             except:pass
#             if re.findall(r"\[download\] 100% of .*in.*|\[download\] 100% of .*B$|\[aria2c\] Downloaded",msg,re.I):
#                 self.downloading=False
#                 print("\r"+msg,"  "*20)
#                 continue
#             elif re.findall(r"\[download\] {1,3}[\d\.]{1,5}% of|\[#\w{6} .*\]",msg,re.I):
#                 self.downloading=True
#                 print("\r"+msg,"  "*20,end="")
#                 continue
#             else:
#                 if re.findall(r"This live event will begin|upload date is not in range|Unsupported URL|title matched reject pattern|title did not match pattern|This video has been removed|Video unavailable|upload date is not in range|said: This video has been disabled|TypeError: the JSON object must be str, not 'NoneType'|YouTube said: Unable to extract video data|This video has been removed|Unable to extract JS player URL|Unable to extract iframe URL",msg):
#                     self.resetStart()
#                 if self.playlistTotal==1 and re.findall(r"Downloading (\d{1,3}) videos",msg):
#                     self.playlistTotal=int(re.findall(r"Downloading (\d{1,3}) videos",msg)[0])+self.ydlOpts["playlist-start"]-1
#                 if re.findall(r"\[download\] Downloading video .*(\d{1,4}).* of .*(\d{1,4}).*",msg,re.I):
#                     msg="[download] Downloading video %d of %d"%(self.ydlOpts["playlist-start"],self.playlistTotal)
#                 if re.findall("unable to extract view count|nsig extraction failed|Download aborted",msg,re.I):continue
#                 if msgtype == "error":
#                     self.errMsg=msg
#                     if re.findall("ERROR:",msg):
#                         msg=re.sub(".*?ERROR:",r"[\033[31mERROR\033[0m]",msg,flags=re.DOTALL)
#                     if re.findall("WARNING:",msg):
#                         msg=re.sub(r"warning:",r"[\033[33mwarning\033[0m] ",msg,flags=re.I)
#                     # else:msg="[\033[33mwarning\033[0m] "+msg
#                     if re.findall("Interrupted by user",msg):
#                         msg=""
#                         self.printMsg(msg)
#                         self.popen.terminate()
#                         sys.exit(0)
#                 self.printMsg(msg)
#                 if re.findall("\[Exec\] Executing command",msg):
#                     self.resetStart()
#                     print("------ "*6)

#     def setConsoleTitle(self):
#         global title
#         title["curItem"]=self.ydlOpts["playlist-start"]
#         title["Total"]=self.playlistTotal
#         os.system('title "%s"'%(";  ".join(k + ": " + str(v) for k,v in title.items())))

#     def printMsg(self,msg):
#         # with self.lock:
#         if len(msg) >= 1:
#             msg=msg[0]+re.sub("\n"," ",msg[1:])
#         if self.downloading:print("\n"+msg)
#         else:print(msg)
#         self.downloading=False
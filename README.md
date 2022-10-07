# DLVideo
用于下载网站视频，youtube，对yt-dlp进行封装
需配合aria2c、chrome、ffmpeg使用

需要的库：
    pip install yt-dlp

参数：（自行修改脚本文件）
    savePath=r"h:\youtube-dl"
    searchMPath=(r"H:\youtube-dl\OK",savePath,r"D:\youtube-dl")
    proxy="127.0.0.1:10909"

命令执行：
    python videlDL.py 1,3,4 5,6 18-29
    即 打开一个窗口对playlist.txt的第1,3,4行的链接逐个下载；打开第二个窗口对第5,6行进行下载；打开第三个窗口对18到29进行下载



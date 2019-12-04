# Chipper
Chipper is a software (with a GUI) for semi-automated 
segmentation and analysis of birdsongs or other acoustic signals.

### Documentation

Full documentation is available as a [Chipper Manual](https://github.com/CreanzaLab/chipper/blob/master/docs/chipper_manual.md) on 
GitHub. For associated publication see *Searfoss, Pino, Creanza 2019 (Under
 Review)*.

### Download Chipper

1. [Download](https://github.com/CreanzaLab/chipper/releases) the correct version of Chipper for your operating system.
2. Unzip the folder, extracting all files.
3. *Windows:* Navigate into the start_chipper folder and double click the 
Application file (.exe) named start_chipper, which may have a bird as an 
icon. The first time you try to open the file, you may receive the message 
"Windows Defender SmartScreen prevented an 
unrecognized app from starting. Running this app might put your PC at risk."
 Click "More info" and then select "Run anyway". You will now see a terminal
  window open.<br/>  

    *Mac:* Navigate into the start_chipper folder and double click the Unix 
    executable file named start_chipper. The first time you 
    try to open the file, you may receive the message "start_chipper can't 
    be opened because it is from an unidentified developer". If so, right 
    click on the file and select "Open". Click "Open" again on the popup to 
    confirm. You will now see a terminal window open.
    
    *Linux:* Open the terminal and type 
    "/path/to/start_chipper/start_chipper" without quotes and replacing 
    "/path/to" with the full file location. Hit enter.
4. The Chipper landing page will soon open. Note, this can take some time to
  load the first time. If it does not open, close the terminal and try opening 
  the start_chipper file again. For best performance, we recommend 
  using Chipper in full-screen mode, especially if you are working on a low 
  resolution display. You are ready to go!


### Install from source

This is recommended for developers.

 1.  Install Anaconda
 
>Our recommended approach is to use Anaconda, which is a distribution of 
>Python containing most of the numeric and scientific software needed to get 
>started. If you are a Mac or Linux user, have used Python before and are 
>comfortable using pip to install software, you may want to skip this step 
>and use your existing Python installation.

 2.  From within a terminal or command prompt window we will install most 
 packages with conda

    $ conda create -n chipper_env python=3.7
    $ condapip install pypiwin32 kivy.deps.sdl2 kivy.deps.glew
    $ kivy.deps.gstreamer kivy.deps.glew_dev kivy.deps.sdl2_dev
    $ kivy.deps.gstreamer_dev

 3.  Additional steps for Windows users:

    $ pip install pypiwin32 kivy.deps.sdl2 kivy.deps.glew kivy.deps.gstreamer kivy.deps.glew_dev kivy.deps.sdl2_dev kivy.deps.gstreamer_dev

 4.  Install kivy packages

    $ garden install --kivy graph
    $ garden install --kivy filebrowser
    $ garden install --kivy matplotlib
    $ garden install --kivy progressspinner
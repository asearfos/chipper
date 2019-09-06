# Chipper
Chipper is a software (with a GUI) for semi-automated 
segmentation and analysis of birdsongs or other acoustic signals.

### Documentation

Full documentation is available as a [Chipper Manual](https://github.com/CreanzaLab/chipper/blob/master/docs/chipper_manual.md) on 
GitHub. For associated publication see *Searfoss, Pino, Creanza 2019 (Under
 Review)*.

### Download Chipper

1. [Download](https://github.com/CreanzaLab/chipper/releases) the correct version of Chipper for your operating system.
2. Unzip the folder.
3. Navigate to and double click the executable named chipper.exe, which may 
have
a bird as an icon. 
4. You will now see a terminal window open, and soon after, the
Chipper landing page will load. You are ready to go!

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
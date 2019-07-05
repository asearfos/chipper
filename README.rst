Documentation
-------------

The full Chipper manual is available online at ___.


Install from source
===================

1. Install Anaconda

   Our recommended approach is to use Anaconda_, which is a
   distribution of Python containing most of the numeric and scientific
   software needed to get started. If you are a Mac or Linux user, have
   used Python before and are comfortable using ``pip`` to install
   software, you may want to skip this step and use your existing Python
   installation.


2. From within a terminal or command prompt window

   We will install most packages with conda::

      $ conda create -n chipper_env python=3.7
      $ conda activate chipper_env
      $ git clone https://github.com/asearfos/chipper
      $ cd chipper
      $ pip install -r requirements.txt

2.a Additional steps for Windows users::

    pip install  pypiwin32 kivy.deps.sdl2 kivy.deps.glew kivy.deps.gstreamer kivy.deps.glew_dev kivy.deps.sdl2_dev kivy.deps.gstreamer_dev

3. Install kivy packages ::

    garden install --kivy graph
    garden install --kivy filebrowser
    garden install --kivy matplotlib
    garden install --kivy progressspinner


Download chipper
================


**Install Chipper**

Download the version of Chipper for your operating system. Unzip the folder.
Navigate to and double click the executable named chipper.exe which may have
a bird as an icon. You will now see a terminal window open and soon after the
Chipper landing page. You are ready to go!


.. _Anaconda: https://www.anaconda.com/distribution/#download-section
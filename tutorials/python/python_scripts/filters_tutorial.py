#!/usr/bin/env python
# coding: utf-8

# ![puma logo](https://github.com/nasa/puma/raw/main/doc/source/puma_logo.png)

# # Image Filters

# The objective of this notebook is to familiarize new users with the main datastructures that stand at the basis of the
# PuMA project, and outline the functions to compute material properties (please refer to these papers
# ([1](https://www.sciencedirect.com/science/article/pii/S2352711018300281),
# [2](https://www.sciencedirect.com/science/article/pii/S235271102100090X)) for more details on the software).

# ## Installation setup and imports

# The first code block will execute the necessary installation and package import.
# 
# If you are running this jupyter notebook locally on your machine, assuming you have already installed the software,
# then the installation step will be skipped

# In[ ]:


# for interactive slicer
get_ipython().run_line_magic('matplotlib', 'widget')
import pumapy as puma
import os

if 'BINDER_SERVICE_HOST' in os.environ:  # ONLINE JUPYTER ON BINDER
    from pyvirtualdisplay import Display
    display = Display(visible=0, size=(600, 400))
    display.start()  # necessary for pyvista interactive plots
    notebook = True

else:  # LOCAL JUPYTER NOTEBOOK
    notebook = False  # when running locally, actually open pyvista window


# ## Tutorial
# 
# In this tutorial we show the use of the image filters implemented in pumapy. Let's start by importing an image:

# In[ ]:


ws = puma.import_3Dtiff(puma.path_to_example_file("100_fiberform.tif"), 1.3e-6)


# In succession, we can now run run the different image filters and show their output:
# 
# 3D Median filter (edge preserving):

# In[ ]:


ws_median = ws.copy()

# the size refers to the side of the cubical kernel to be applied
puma.filter_median(ws_median, size=10)

puma.compare_slices(ws, ws_median, 'z', index=1)


# 3D Gaussian filter:

# In[ ]:


ws_gaussian = ws.copy()

puma.filter_gaussian(ws_gaussian, sigma=2, apply_on_orientation=False)

puma.compare_slices(ws, ws_gaussian, 'z', index=1)


# 3D Exact euclidean distance transform:

# In[ ]:


ws_edt = ws.copy()

puma.filter_edt(ws_edt, cutoff=(90, 255))

puma.compare_slices(ws, ws_edt, 'z', index=1)


# 3D Mean filter:

# In[ ]:


ws_mean = ws.copy()

# the size refers to the side of the cubical kernel to be applied
puma.filter_mean(ws_mean, size=10)

puma.compare_slices(ws, ws_mean, 'z', index=1)


# 3D morphological erosion filter:

# In[ ]:


ws_erode = ws.copy()

# the size refers to the side of the spherical kernel to be applied
puma.filter_erode(ws_erode, cutoff=(90, 255), size=3)

ws_binary = ws.copy()
ws_binary.binarize_range((90, 255))

puma.compare_slices(ws_binary, ws_erode, 'z', index=1)


# 3D morphological dilation filter:

# In[ ]:


ws_dilate = ws.copy()

# the size refers to the side of the spherical kernel to be applied
puma.filter_dilate(ws_dilate, cutoff=(90, 255), size=3)

ws_binary = ws.copy()
ws_binary.binarize_range((90, 255))

puma.compare_slices(ws_binary, ws_dilate, 'z', index=1)


# 3D morphological opening filter (i.e. dilation first and then erosion):

# In[ ]:


ws_opening = ws.copy()

# the size refers to the side of the spherical kernel to be applied
puma.filter_opening(ws_opening, cutoff=(90, 255), size=3)

ws_binary = ws.copy()
ws_binary.binarize_range((90, 255))

puma.compare_slices(ws_binary, ws_opening, 'z', index=1)


# 3D morphological closing filter (i.e. erosion first and then dilation)

# In[ ]:


ws_closing = ws.copy()

# the size refers to the side of the spherical kernel to be applied
puma.filter_closing(ws_closing, cutoff=(90, 255), size=3)

ws_binary = ws.copy()
ws_binary.binarize_range((90, 255))

puma.compare_slices(ws_binary, ws_closing, 'z', index=1)


# In[ ]:





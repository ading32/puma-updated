#!/usr/bin/env python
# coding: utf-8

# ![puma logo](https://github.com/nasa/puma/raw/main/doc/source/puma_logo.png)

# # Porespace Identification

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
# When dealing with porous materials, it is often useful to distinguish between closed and open porosity.
# This is particularly relevant when particle or ray casting simulations need to be performed. In these cases,
# closed porosity throughout a domain becomes a problem, because particles get trapped inside these pockets,
# inevitably altering the output of a simulation. For this reason, a method to identify and fill the closed porosity
# was implemented in both C++ PuMA and pumapy.
# Let's first create a 50% dense sample full of hollowed out spheres and visualize it:

# In[ ]:


ws = puma.generate_random_spheres((200, 200, 200), diameter=20, porosity=0.5, allow_intersect=True, segmented=False)

# void is 0, solid is 255, but the material does not jump from 0-255, it gradually does so
# we therefore use this gradient to select the shell of each sphere
ws.binarize_range((1, 254))

puma.render_volume(ws, cutoff=(1, 1), solid_color=(255,255,255), notebook=notebook)


# Now we can run the pore filling algorithm, which runs a connected component analysis. The fill_closed_pores function
# needs to be given the solid range (in this case only 1 since we have already binarized the workspace) and the ID value
# to fill the closed porosity throughout the workspace (in this case we set 2).

# In[ ]:


filled_ws, pores = puma.fill_closed_pores(ws, (1, 1), 2, return_pores=True)


# When the return_pores flag is True, then it returns both the already filled workspace and a Numpy array of pores with
# IDs: solid == 0, largest pore (likely open porosity) == 1, smaller pores (likely closed porosity) == 2 - N. We can
# visualize both these outputs as:

# In[ ]:


puma.render_volume(pores[:pores.shape[0]//2], cutoff=(1, 10), solid_color=None, notebook=notebook, cmap='jet')


# In[ ]:


puma.render_volume(filled_ws, notebook=notebook, cmap='jet')


# Note that the identify_porespace function performs the same operation as the fill_closed_pores, except that it does not
# fill the closed pores throughout the workspace, it only returns the labelled pores identified.

import javabridge
import xml.etree.ElementTree as ET
import bioformats
import re

default_locations=[['Loop','cycle time'],['Loop','Stage loop','Z-Stack','relative step width']]
default_tag=[['node','attribute'],['node','node','node','attribute']]

# ---- Main function that extracts the relevant metadata from a vsi file
def extract_metadata(filepath,cycle_vm=True,meta_number=None,stage_loop=True,z_stack=False,endpoint=False,cycle_time=True):
    if cycle_vm:
        javabridge.start_vm(class_path=bioformats.JARS)
    biof=extract_meta_bioformats(filepath)
    if meta_number is not None:
        filepath=change_file_num(filepath,meta_number)
    if endpoint ==True:
        cycle_time=False
    metadata=extract_meta_manual(filepath,metadata=biof,stage_loop=stage_loop,z_stack=z_stack,
                                 cycle_time=cycle_time)
    if cycle_vm:
        javabridge.kill_vm()
    return metadata

def change_file_num(string,meta_number):
    new_string = re.sub('\d(\D*)$',str(meta_number),string)
    new_string=new_string+'.vsi'
    return new_string

def split(word):
    return [char for char in word]

# ---- Function that gets the attainable information using bioformats
def extract_meta_bioformats(filepath, metadata=dict()):
    omexmlstr = bioformats.get_omexml_metadata(filepath)
    o = bioformats.OMEXML(omexmlstr)
    x = o.image().Pixels
    metadata['size_Z'] = x.SizeZ
    metadata['size_T'] = x.SizeT
    metadata['scale'] = x.PhysicalSizeX
    return metadata

# ---- Function that manually reads through oex metadata file and gets other relevant information
#      paths through the xml file to final metadata value

def extract_meta_manual(file_path,locations=default_locations,tag=default_tag,metadata=dict(),stage_loop=True,z_stack=False,cycle_time=True):
    file_path=file_path.replace('vsi','oex')
    
    if stage_loop==False and z_stack==False and cycle_time==True:
        locations=[['Loop','cycle time']]
        tag=[['node','attribute']]
    elif stage_loop==False and z_stack==True and cycle_time==True:
        locations=[['Loop','cycle time'],
                           ['Loop','Z-Stack','relative step width']]
        tag=[['node','attribute'],['node','node','attribute']]
    elif stage_loop==True and z_stack==False and cycle_time==True:
        locations=[['Loop','cycle time']]
        tag=[['node','attribute']]
    elif stage_loop==True and z_stack==True and cycle_time==False:
        locations=[['Stage loop','Z-Stack','relative step width']]
        tag=[['node','node','attribute']]

    tree=ET.parse(file_path)
    root=tree.getroot()
    # get into net
    for subroot in root:
        if subroot.tag=='net':
            root=subroot
            break
    # iterate through the different values we want to get
    for i in range(len(locations)):
        loop_root=root
        path=locations[i][:]
        path_tag=tag[i][:]
        # naviate through the directed paths of the xml file
        for j in range(len(path)):
            loop_root=query_branches(loop_root,path_tag[j],path[j])
            # if at the end of the path get the metadata value we want and append it to a dictionary
            if j==len(path)-1:
                if  loop_root!='not_found':
                    for l in loop_root:
                        metadata[path[j]]=l.get('val')
    return metadata
# ---- Function to look in a directory of the xml and find the subdirectory you're querying. Used for the manual
#      metedata extraction
def query_branches(loop,tag,attrib):
    found=False
    # search through subdirectories of directory
    for k in loop:
        # if the tag and attribute match of subdir match return the subdir
        if k.tag == tag and k.attrib['name']==attrib:
            new_loop=k
            found=True
            break
    if found:
        return new_loop
    else:
        return 'not_found'
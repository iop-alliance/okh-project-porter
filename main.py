from email.policy import default
import os.path

import PySimpleGUI as sg

from filegetter import get_files_from_file, get_files_from_url 

def get_output_path():
    """
    Get the top-level folder path
    :return: Path to list of files using the user settings for this file.  Returns folder of this file if not found
    :rtype: str
    """
    output_path = sg.user_settings_get_entry('-output folder-', os.path.dirname(__file__))

    return output_path


file_layout = [
    [sg.T('OKH Manifest File')],
    [sg.In(sg.user_settings_get_entry('-manifest file-', []), key='-MANIFEST-FILE-'), sg.FileBrowse()],
    [sg.T('Output folder (must be empty)')], 
    [sg.In(sg.user_settings_get_entry('-output folder-', ''), k='-OUTPUTFOLDER-M-'), sg.FolderBrowse()],
    [sg.Button(' Get the Project! ', key='-GET-FROM-MANIFEST-')]
]

url_layout = [
    [sg.Text('Enter the url of an OKH Manifest file:')],
    [sg.Input(key='-URL-')],
    [sg.T('Output folder (must be empty)')], 
    [sg.In(sg.user_settings_get_entry('-output folder-', ''), k='-OUTPUTFOLDER-U-'), sg.FolderBrowse()],
    [sg.Button(' Get the Project! ', key='-GET-FROM-URL-')]
]

tab_group = [
  [sg.TabGroup(
    [[
      sg.Tab("From File", file_layout),
      sg.Tab("From URL", url_layout),
    ]],
    tab_location="centretop"
  )]]

layout = [  tab_group,
            [sg.Button('Exit', key='-EXIT-')] ]

# Create the Window
window = sg.Window('OKH Project Porter', layout, font=("Arial", 16))

while True:
  event, values = window.read()
  print(event, values)
  if event in (sg.WIN_CLOSED, '-EXIT-'):
    break
  elif event == '-GET-FROM-URL-':
    if os.path.isdir(values['-OUTPUTFOLDER-U-']) and len(os.listdir(values['-OUTPUTFOLDER-U-']) ) != 0:
        sg.popup('Warning!', 'Chosen output path is not empty.', 'Please choose an empty Folder.')    
    else:
        get_files_from_url(values['-URL-'], values['-OUTPUTFOLDER-U-'])
        sg.popup('Completed!')
  elif event == '-GET-FROM-MANIFEST-':
    if os.path.isdir(values['-OUTPUTFOLDER-M-']) and len(os.listdir(values['-OUTPUTFOLDER-M-']) ) != 0:
        sg.popup('Warning!', 'Chosen output path is not empty.', 'Please choose an empty Folder.')    
    else:
        get_files_from_file(values['-MANIFEST-FILE-'], values['-OUTPUTFOLDER-M-'])
        sg.popup('Completed!')

window.close()

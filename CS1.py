# Import packages
from psychopy import core, event, gui, visual, parallel, prefs
import time
import math
import random
import csv
import os
import cv2

ports_live = True # Set to None if parallel ports not plugged for coding/debugging other parts of exp

### Experiment details/parameters
# parallel port triggers
port_address = 0x3ff8
pain_trig = 2 #levels and order need to be organised through CHEPS system
eda_trig = 1 #pin 1 to mark trial information on LabChart
tens_trig = {"TENS": 128, "control": 0} #Pin 8 in relay box just for the clicking sound

## within experiment parameters
experimentcode = "CS1"
P_info = {"PID": "",
        "SONA" : ""}
info_order = ["PID"]

#text + stimuli
cue_colours = ([-1,0.10588,-1],[-1,-1,1]) # 2 colours taken from Kirsten EEG
cue_colour_names = ('green','blue')
cue_positions = [(300,0),(-300,0)]
cue_width = 200

rating_scale_pos = (0,-350)
rating_text_pos = (0,-250) 
text_height = 30 

#trials
pain_response_duration = float("inf")
response_hold_duration = 1 # How long the rating screen is left on the response (only used for Pain ratings)
TENS_pulse_int = 0.1 # interval length for TENS on/off signals (e.g. 0.1 = 0.2s per pulse)
port_buffer_duration = 1 #needs about at least 0.5s buffer for port signal to reset 

iti = 6
familiarisation_iti = 3
trial_countdown_time = 10

#social modelling
video_painratings_mean = {"TENS" : 81, "control": 31}
video_painratings_spread = {"TENS" : 5, "control" : 5}
video_painratings_buffer = 5

video_stim_introtime = 10
video_stim_iti = 6
model_rest_time = 8

video_stim_models_list = ['m1','m2','m3','m4']
video_blocks_list = ["b1","b2","b3","b4"]
video_intro_name = "intro"

video_stim_size = (300,225)
video_stim_gap = 50
video_model_pos = (0,300)

webcam_stim_pos = (0,-300)
webcam_stim_size = (400,300)
webcam_text_pos = (0, 300)

#calculate iti_jitter
# iti_jitter = [x * 1000 for x in iti_range]

# Participant info input
while True:
    try:
        P_info["PID"] = input("Enter participant ID: ")
        if not P_info["PID"]:
            print("Participant ID cannot be empty.")
            continue
        
        P_info["SONA"] = input("Enter SONA pool ID: ")

        # block_order = [int(block) for block in input("Enter block order: ").split()]
   
        data_filename = P_info["PID"] + "_responses.csv"
        script_directory = os.path.dirname(os.path.abspath(__file__))  #Set the working directory to the folder the Python code is opened from
        
        #set a path to a "data" folder to save data in
        data_folder = os.path.join(script_directory, "data")
        
        #set a path to the "stimuli" folder for SM videos
        
        stim_folder = os.path.join(script_directory, "stimuli")
        
        # if data folder doesn"t exist, create one
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
            
        #set file name within "data" folder
        data_filepath = os.path.join(data_folder,data_filename)
        
        if os.path.exists(data_filepath):
            print(f"Data for participant {P_info['PID']} already exists. Choose a different participant ID.") ### to avoid re-writing existing data
        
        
        # Group == 1 == single (4 trials)
        # Group == 2 == multiple (4 + 4 + 4 + 4 trials)
        
        # cb == 1 == TENS = GREEN, control = BLUE
        # cb == 2 == TENS = BLUE, control = GREEN
            
        else:
            PID = int(P_info["PID"])
            modelling_groups_list = ["single", "multiple"]

            # Assign variables using the lookup tables
            group = PID % 2
            groupname = modelling_groups_list[group]

            # Determine counterbalance (1 or 2)
            cb = PID // 2 % 2

            break  # Exit the loop if the participant ID is valid
        
    except KeyboardInterrupt:
        print("Participant info input canceled.")
        break  # Exit the loop if the participant info input is canceled

# get date and time of experiment start
datetime = time.strftime("%Y-%m-%d_%H.%M.%S")

#set stimulus colours according to cb 
stim_colours = {
  "TENS" : cue_colours[cb],
  "control": cue_colours[1-cb] 
}

stim_colour_names = {
    "TENS" : cue_colour_names[cb],
    "control": cue_colour_names[1-cb]
}

stim_positions = {
    "TENS" : cue_positions[cb],
    "control" : cue_positions[1-cb]
}

if ports_live == True:
    pport = parallel.ParallelPort(address=port_address) #Get from device Manager
    pport.setData(0)
    
elif ports_live == None:
    pport = None #Get from device Manager

# set up screen
win = visual.Window(
    size=(1920, 1080), fullscr= True, screen=0,
    allowGUI=False, allowStencil=False,
    monitor="testMonitor", color=[0, 0, 0], colorSpace="rgb1",
    blendMode="avg", useFBO=True,
    units="pix")

# fixation stimulus
fix_stim = visual.TextStim(win,
                            text = "x",
                            color = "white",
                            height = 50,
                            font = "Roboto Mono Medium")

#define waiting function so experiment doesn't freeze as it does with wait()
def wait(time):
    countdown_timer = core.CountdownTimer(time)
    while countdown_timer.getTime() > 0:
        termination_check()
        
#create instruction trials
def instruction_trial(instructions,
                      holdtime=0,
                      key = "space",
                      buttontext = "\n\nPress spacebar to continue"): 
    termination_check()
    
    visual.TextStim(win,
                    text = instructions,
                    height = text_height,
                    color = "white",
                    pos = (0,0),
                    wrapWidth= 960
                    ).draw()
    win.flip()
    
    if key != None:
        wait(holdtime)
        visual.TextStim(win,
                        text = instructions,
                        height = text_height,
                        color = "white",
                        pos = (0,0),
                        wrapWidth= 960
                        ).draw()
        
        visual.TextStim(win,
                        text = buttontext,
                        height = text_height,
                        color = "white",
                        pos = (0,-400)
                        ).draw()
        event.waitKeys(keyList=key)
    else: 
        wait(holdtime)
        
    win.flip()
    
    wait(2)
    
# Create functions
    # Save responses to a CSV file
def save_data(data):
    for trial in trial_order:
        trial['datetime'] = datetime
        trial['experimentcode'] = experimentcode
        trial["PID"] = P_info["PID"]
        trial["SONA"] = P_info["SONA"]
        trial["group"] = group
        trial["groupname"] = groupname
        trial["cb"] = cb
        trial["tens_colour"] = stim_colour_names["TENS"]
        trial["control_colour"] = stim_colour_names["control"]

    # Extract column names from the keys in the first trial dictionary
    colnames = list(trial_order[0].keys())

    # Open the CSV file for writing
    with open(data_filepath, mode="w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=colnames)
        
        # Write the header row
        writer.writeheader()
        
        # Write each trial"s data to the CSV file
        for trial in data:
            writer.writerow(trial)
    
def exit_screen(instructions):
    win.flip()
    visual.TextStim(win,
            text = instructions,
            height = text_height,
            color = "white",
            pos = (0,0)).draw()
    win.flip()
    event.waitKeys()
    win.close()
    
def termination_check(): #insert throughout experiment so participants can end at any point.
    keys_pressed = event.getKeys(keyList=["escape"])  # Check for "escape" key during countdown
    if "escape" in keys_pressed:
        if ports_live:
            pport.setData(0) # Set all pins to 0 to shut off context, TENS, shock etc.
        # Save participant information

        save_data(trial_order)
        exit_screen(instructions_text["termination"])
        core.quit()


# Define trials
trial_order = []

# familiarisation trials
num_familiarisation = 10

for i in range(1, num_familiarisation + 1):
    trial = {
        "phase": "familiarisation",
        "blocknum": None,
        "stimulus": None,
        "outcome": None,
        "trialname": "familiarisation_" + str(i),
        "trialtype": "familiarisation",
        "model" : None,
        "block" : None,
        "model_video_name" : None,
        "exp_response": None,
        "pain_response": None,
        "iti" : None
    } 

    trial_order.append(trial)
    
#define conditioning trials
num_blocks_conditioning = 4 #multiple group sees 4 blocks
num_trials_per_block = 4 # each block has 2 pairs of TENS and no-TENS trials

model_stim_blocks = { #pre-determined stimulus order for each model 
    "m1": {
        "b1": ['TENS','control','TENS','control'],
        "b2": ['TENS','control','control','TENS'],
        "b3": ['control','TENS','control','TENS'],
        "b4": ['control','TENS','TENS','control']
    },
    "m2": {
        "b1": ['control','TENS','control','TENS'],
        "b2": ['control','TENS','TENS','control'],
        "b3": ['TENS','control','TENS','control'],
        "b4": ['TENS','control','TENS','control']
    },
    "m3": {
        "b1": ['control','TENS','control','TENS'],
        "b2": ['control','TENS','TENS','control'],
        "b3": ['TENS','control','control','TENS'],
        "b4": ['TENS','control','control','TENS']
    },
    "m4": {
        "b1": ['control','TENS','control','TENS'],
        "b2": ['TENS','control','TENS','control'],
        "b3": ['TENS','control','TENS','control'],
        "b4": ['TENS','control','control','TENS']
    }
}

model_stim_outcomes = {
    "TENS": "high",
    "control": "low",
    }

random.shuffle(video_stim_models_list)
random.shuffle(video_blocks_list)

if groupname == "single":
    video_stim_models_order = [video_stim_models_list[0]]*num_blocks_conditioning
else: 
    video_stim_models_order = video_stim_models_list

video_blocks_order = video_blocks_list

### create list of trials based on trial_block order, iterating through stimulus + outcome blocks in parallel
for block in range(1,num_blocks_conditioning+1):
    model = video_stim_models_order[block-1]
    blockname = video_blocks_order[block-1]
    for trialnum in range(num_trials_per_block):
        stimulus = model_stim_blocks[model][blockname][trialnum]
        outcome = model_stim_outcomes[stimulus]
        trial = {
            "phase": "conditioning",
            "blocknum": block,
            "stimulus": stimulus,
            "outcome": outcome,
            "trialname": f"{stimulus}_{outcome}",
            "trialtype": "socialmodel",
            "model" : model,
            "block" : block,
            "model_video_name" : f"{model}_{blockname}",
            "exp_response": None,
            "pain_response": None,
            "iti" : None
        }
        trial_order.append(trial)
        
#define extinction trials
num_blocks_extinction = 2 #2 blocks of uninterrupted 16 trials (8 pairs of TENS and control)
num_pairs_extinction = 8
extinction_stim_pair = ['TENS','control']

#create extinction trials, all outcomes same regardless of condition (low heat)
for block in range(num_blocks_conditioning+1,num_blocks_conditioning+num_blocks_extinction+1):
    extinction_block = []
    for pair in range(num_pairs_extinction):
        shuffled_pair = extinction_stim_pair
        random.shuffle(shuffled_pair)
        extinction_block.extend(shuffled_pair)
    
    for trialnum in range(len(extinction_stim_pair)*num_pairs_extinction):
        stimulus = extinction_block[trialnum]
        trial = {
            "phase": "extinction",
            "blocknum": block,
            "stimulus": stimulus,
            "outcome": "low",
            "trialname": str(stimulus) + "_" + str(outcome),
            "trialtype": "experience",
            "model" : None,
            "block" : block,
            "model_video_name" : None,
            "exp_response": None,
            "pain_response": None,
            "iti": None
        }
        trial_order.append(trial)
        
# # Assign trial numbers
for trialnum, trial in enumerate(trial_order, start=1):
    trial["trialnum"] = trialnum
    
save_data(trial_order)
    
# # text stimuli
instructions_text = {
    "welcome": "Welcome to the experiment! Please read the following instructions carefully.", 
    
    "familiarisation_1": ("Firstly, you will be familiarised with the thermal stimuli. This familiarisation procedure is necessary to ensure that participants are able to tolerate "
    "the heat pain delivered in this experiment. The thermal stimulus is delivered through the thermode attached to your forearm, which delivers heat pain by selectively stimulating pain fibres.\n\n"
    "As the density of pain fibres can vary between individuals, the pain experienced and the efficacy of TENS for participants who will receive TENS stimulation can also vary. "
    "As such, this familiarisation procedure will demonstrate the range of how painful the thermal stimulus could be for any participant."),
    
    "familiarisation_2": ("In the familiarisation procedure, you will experience the thermal stimuli at a range of intensities. The machine will start at a low intensity, and incrementally increase each level. "
    "After receiving each thermal stimulus, please give a pain rating for that level of heat by clicking and dragging your mouse on a scale from 1 to 10 where 1 is not painful and 10 is very painful. "
    "The familiarisation procedure will take you through 10 increasing levels of heat intensities. \n\n Although the higher levels of heat intensities may be more uncomfortable or painful, please note that "
    "the maximum level of heat is safe and unlikely to cause you any actual harm. If, however, you find the thermal stimuli intolerable at any stage, please let the experimenter know and we will terminate the experiment immediately. "
    "This procedure will proceed at your pace, so feel free to take your time to rest between heat levels."),
        
    "familiarisation_finish": "Thank you for completing the familiarisation protocol. we will now proceed to the next phase of the experiment",
    
    "baseline_waiting": "Collecting baseline readings, please stay still",

    "experiment_webcam_waiting" : ("Waiting for connection..."),
    
    "experiment_webcam_ready" : ("Connection found !\n\n"
                                             "Press SPACEBAR to go live"),
    
    "experiment_webcam_finish" : ("Observation phase completed!\n\n"
                                              "Connection ended."),
    
    "blockrest" : "This is a rest interval. Please wait for the experimenter to adjust the thermode BEFORE pressing SPACEBAR.", 

    "modelrest": "This is a rest interval. Please wait for the other participant to continue the experiment.",
    
    "blockresume" : "Feel free to take as much as rest as necessary before starting the next block.",
    
    "end" : "This concludes the experiment. Please ask the experimenter to help remove the devices.",
    
    "termination" : "The experiment has been terminated. Please ask the experimenter to help remove the devices.",

    "TENS_example" : "In this experiment you may be asked to observe another participant receiving TENS. Although TENS has an audible cue, we will also present a" + stim_colour_names["TENS"] + " square on the screen to indicate when it is active. No-TENS trials will be indicated by a " + stim_colour_names["control"] + " square.",
    
    "TENS_introduction" : "This experiment aims to investigate the effects of Transcutaneous Electrical Nerve Stimulation (TENS) on heat pain sensitivity. "
    "TENS is designed to increase pain sensitivity by enhancing the conductivity of pain signals being sent to your brain. Clinically this is used to enhance pain sensitivity in medical conditions where pain sensitivity is dampened. "
    "In the absence of medical conditions, TENS significantly amplifies pain signals, meaning stimulations will be more painful when the TENS device is active. Although the TENS itself is not painful, you will feel a small sensation when it is turned on. \n\n"
    "In this study you and another participant will receive a series of heat pain stimulations, and some heat pain stimulations will also be accompanied with TENS stimulation.",
    
    "conditioning" : "We will now begin the main phase of the experiment. You will observe another participant receive a series of thermal stimuli with and without TENS. Your task is to predict how painful the other participant finds the thermal stimulus."
    "This rating scale ranges from NOT PAINFUL to VERY PAINFUL. \n\n" +
    "All thermal stimuli will be signaled by a 10 second countdown. The heat will be delivered at the end of the countdown when an X appears. The TENS will now also be active on some trials. "
    "To make clear whether the TENS is on or not, TENS will be indicated by a " + stim_colour_names["TENS"] + " square on the screen, whereas no-TENS trials will be indicated by a " + stim_colour_names["control"] + " square. "
    "As the other participant waits for the thermal stimulus during the countdown, you will be asked to rate how painful you expect their heat to be. After each trial you will find out what pain rating they actually responded with. \n\n"
    "Please wait for the experimenter to set up the stream with the other participant BEFORE pressing SPACEBAR.",
    
    "extinction" : "You will now receive a series of thermal stimuli and rate the intensity of each thermal stimulus. "
    "Similarly to the other participant, the thermal stimuli will be signaled by a 10 second countdown and the heat will be delivered at the end of the countdown when an X appears. The TENS will now also be active on some trials. "
    "To make clear whether the TENS is on or not, TENS will be indicated by a " + stim_colour_names["TENS"] + " square on the screen, whereas no-TENS trials will be indicated by a " + stim_colour_names["control"] + " square. "
    "During the countdown, you will also be asked to rate how painful you expect the heat to be. After each trial there will also be a brief interval to allow you to rest between thermal stimuli. "
    "You will also receive a brief rest between blocks of trials where the experimenter will move the thermode to another location on your arm. \n\n"
    "Please wait for the experimenter now to prepare the thermal stimuli BEFORE pressing SPACEBAR."
    
}

response_instructions = {
    "pain": "How painful was the heat?",
    "expectancy": "How painful do you expect the thermal stimulus to be?",
    "SM": "The demonstrator made the following response on this trial",
    "familiarisation": "When you are ready to receive the thermal stimulus, press the SPACEBAR to activate the thermal stimulus. "
    }

trial_text = {
     None : visual.TextStim(win,
            text=None,
            height = text_height,
            pos = rating_text_pos
            ),
     "pain": visual.TextStim(win,
            text=response_instructions["pain"],
            height = text_height,
            pos = rating_text_pos
            ),
     "expectancy": visual.TextStim(win,
            text=response_instructions["expectancy"],
            height = text_height,
            pos = rating_text_pos
            ),
     "baseline": visual.TextStim(win,
            text=instructions_text["baseline_waiting"],
            height=text_height,
            pos = (0,250)
            ),
     "SMrating": visual.TextStim(win, 
            color="white", 
            height = text_height,
            pos = rating_text_pos,
            text= response_instructions["SM"]
            )
}

# #Test questions
rating_stim = { "familiarisation": visual.Slider(win,
                                    pos = rating_scale_pos,
                                    ticks=[0,50,100],
                                    labels=(1,5,10),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30),
               "pain": visual.Slider(win,
                                    pos = rating_scale_pos,
                                    ticks=[0,100],
                                    labels=("Not painful","Very painful"),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30),
                "expectancy": visual.Slider(win,
                                    pos = rating_scale_pos,
                                    ticks=[0,100],
                                    labels=("Not painful","Very painful"),
                                    granularity=0.1,
                                    size=(600,60),
                                    style=["rating"],
                                    autoLog = False,
                                    labelHeight = 30)}


rating_stim["familiarisation"].marker.size = (30,30)
rating_stim["familiarisation"].marker.color = "yellow"
rating_stim["familiarisation"].validArea.size = (660,100)

rating_stim["pain"].marker.size = (30,30)
rating_stim["pain"].marker.color = "yellow"
rating_stim["pain"].validArea.size = (660,100)

rating_stim["expectancy"].marker.size = (30,30)
rating_stim["expectancy"].marker.color = "yellow"
rating_stim["expectancy"].validArea.size = (660,100)

pain_rating = rating_stim["pain"]
exp_rating = rating_stim["expectancy"]
fam_rating = rating_stim["familiarisation"]
                                
# pre-draw countdown stimuli (numbers 10-1)
countdown_text = {}
for i in range(0,11):
    countdown_text[str(i)] = visual.TextStim(win, 
                            color="white", 
                            height = 50,
                            text=str(i))

# visual cues for TENS/control trials
cue_stims = {"TENS" : visual.Rect(win,
                        lineColor = stim_colours["TENS"],
                        fillColor = stim_colours["TENS"],
                        width = cue_width,
                        height = cue_width,
                        pos = stim_positions["TENS"],
                        autoLog = False),
             "control" : visual.Rect(win,
                        lineColor = stim_colours["control"],
                        fillColor = stim_colours["control"],
                        width = cue_width,
                        height = cue_width,
                        pos = stim_positions["control"],
                        autoLog = False)
             }

#set video stimuli according to group:
video_stim_width = video_stim_size[0]
video_stim_offset = video_stim_width + video_stim_gap

if groupname == "multiple": 
    video_stim_x_pos = [(-1.5*video_stim_offset),
                        (-0.5*video_stim_offset),
                        (0.5*video_stim_offset),
                        (1.5*video_stim_offset)]
    video_stim_pos = [(x, 300) for x in video_stim_x_pos]
    video_stim_models = video_stim_models_order

elif groupname == "single": 
    video_stim_pos = [video_model_pos]
    video_stim_models = [video_stim_models_order[0]]


#load videos
intro_videos = { 
    f"{model}_intro": visual.MovieStim(
        win,
        filename=os.path.join(stim_folder, f"{model}_intro.mp4"),
        size=video_stim_size,
        pos=video_stim_pos[i],  # Assign correct position
        volume=1.0,
        autoStart=False,
        loop=False
    )
    for i, model in enumerate(video_stim_models)
}

model_videos = {
    f"{model}_{block}": visual.MovieStim(
        win,
        filename=os.path.join(stim_folder, f"{model}_{block}.mp4"),
        size=video_stim_size,
        pos=video_model_pos,  # Assign correct position
        volume=1.0,
        autoStart=False,
        loop=False
    )
    for model in video_stim_models
    for block in video_blocks_order
}

#turn on webcam
webcam_feed = cv2.VideoCapture(0)

# Define button_text dictionaries
#### Make trial functions
def show_fam_trial(current_trial):
    termination_check()
    # Wait for participant to ready up for shock
    visual.TextStim(win,
        text=response_instructions["familiarisation"],
        height = 35,
        pos = (0,0),
        wrapWidth= 800
        ).draw()
    win.flip()
    event.waitKeys(keyList = ["space"])
    
    # show fixation stimulus + deliver shock
    if pport != None:
        pport.setData(0)

    fix_stim.draw()
    win.flip()
    
    if pport != None:
        pport.setData(pain_trig+eda_trig)
        wait(port_buffer_duration)
        pport.setData(0)
    
    # Get pain rating
    while fam_rating.getRating() is None: # while mouse unclicked
        termination_check()
        trial_text["pain"].draw()
        fam_rating.draw()
        win.flip()
         
    pain_response_end_time = core.getTime() + response_hold_duration # amount of time for participants to adjust slider after making a response
    
    while core.getTime() < pain_response_end_time:
        termination_check()
        trial_text["pain"].draw()
        fam_rating.draw()
        win.flip()

    current_trial["pain_response"] = fam_rating.getRating()
    fam_rating.reset()
    
    win.flip()
    wait(familiarisation_iti)
    
def show_trial(current_trial,
               trialtype,
               video = None):

    global iti
   
    if pport != None:
        pport.setData(0)
    
    if trialtype == "socialmodel":
        trial_iti = video_stim_iti  
          
    else: 
        trial_iti = iti
        
    # Set the initial countdown time to 10 seconds
    countdown_timer = core.CountdownTimer(trial_countdown_time)
        
# social modelling conditioning trials
    if trialtype == "socialmodel":
        video_stim = model_videos[video]
        video_stim.play()
        while countdown_timer.getTime() > 8:
            termination_check()
            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            video_stim.draw()
            win.flip()
            
        while countdown_timer.getTime() < 8 and countdown_timer.getTime() > 7: #turn on TENS at 8 seconds
            termination_check()
            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            cue_stims[current_trial["stimulus"]].draw()
            video_stim.draw()
            win.flip()

        while countdown_timer.getTime() < 7 and countdown_timer.getTime() > 0: #ask for expectancy at 7 seconds
            termination_check()
            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            video_stim.draw()
            cue_stims[current_trial["stimulus"]].draw()
            
            # Ask for expectancy rating
            trial_text["expectancy"].draw()
            exp_rating.draw()
            video_stim.draw()
            win.flip()    

        if pport!= None:
            pport.setData(eda_trig) 

        current_trial["exp_response"] = exp_rating.getRating() #saves the expectancy response for that trial
        exp_rating.reset() #resets the expectancy slider for subsequent trials
        
        buffer_timer = core.CountdownTimer(video_painratings_buffer + port_buffer_duration)   
                       
        while buffer_timer.getTime() > 0:
            video_stim.draw()
            win.flip() 

        if pport!= None:
            pport.setData(0) 

        # present social model's pain rating 
        pain_rating_sm = random.normalvariate(
                video_painratings_mean[current_trial["stimulus"]],
                video_painratings_spread[current_trial["stimulus"]])
        
        pain_rating.rating = pain_rating_sm
        pain_rating.readOnly = True
        
        iti_timer = core.CountdownTimer(trial_iti)
        
        while iti_timer.getTime() > 0:
            video_stim.draw()
            trial_text["SMrating"].draw()
            pain_rating.draw()
            win.flip()
                
        current_trial["pain_response"] = pain_rating.getRating()
        pain_rating.reset()

        current_trial["iti"] = trial_iti
        video_stim.pause()
            
    #if it's a conditioning/extinction trial, do regular 10 second countdown with stimuli + pain stimulus etc.  
      
    elif trialtype == "experience": 
        while countdown_timer.getTime() > 8:
            termination_check()
            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            win.flip()
        
            TENS_timer = countdown_timer.getTime() + TENS_pulse_int

        while countdown_timer.getTime() < 8 and countdown_timer.getTime() > 7: #turn on TENS at 8 seconds
            termination_check()
            
            if pport != None:
                if current_trial["stimulus"] != None:
                    # turn on TENS pulses if TENS trial, at an on/off interval speed of TENS_pulse_int, marking TENS onset with EDA trig
                    if countdown_timer.getTime() < TENS_timer - TENS_pulse_int:
                        pport.setData(tens_trig[current_trial["stimulus"]])
                    if countdown_timer.getTime() < TENS_timer - TENS_pulse_int*2:
                        pport.setData(0)
                        TENS_timer = countdown_timer.getTime() 

            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            cue_stims[current_trial["stimulus"]].draw()
            win.flip()

        
        TENS_timer = countdown_timer.getTime() + TENS_pulse_int

        while countdown_timer.getTime() < 7 and countdown_timer.getTime() > 0: #ask for expectancy at 7 seconds
            termination_check()
            if pport != None:                      
                if current_trial["stimulus"] != None:
                    # turn on TENS pulses if TENS trial, at an on/off interval speed of TENS_pulse_int, marking TENS onset with EDA trig
                    if countdown_timer.getTime() < TENS_timer - TENS_pulse_int:
                        pport.setData(tens_trig[current_trial["stimulus"]])
                    if countdown_timer.getTime() < TENS_timer - TENS_pulse_int*2:
                        pport.setData(0)
                        TENS_timer = countdown_timer.getTime() 

            countdown_text[str(int(math.ceil(countdown_timer.getTime())))].draw()
            cue_stims[current_trial["stimulus"]].draw()
            
            # Ask for expectancy rating
            trial_text["expectancy"].draw()
            exp_rating.draw()
            win.flip()    

        current_trial["exp_response"] = exp_rating.getRating() #saves the expectancy response for that trial
        exp_rating.reset() #resets the expectancy slider for subsequent trials
                
        # deliver shock
        if pport != None:
            pport.setData(0)
        fix_stim.draw()
        win.flip()
        
        if pport != None:
            pport.setData(pain_trig+eda_trig)
            wait(port_buffer_duration)
            pport.setData(0)

        # Get pain rating
        while pain_rating.getRating() is None: # while mouse unclicked
            pain_rating.readOnly = False
            termination_check()
            pain_rating.draw()
            trial_text["pain"].draw()
            win.flip()
                
                
        pain_response_end_time = core.getTime() + response_hold_duration # amount of time for participants to adjust slider after making a response
        
        while core.getTime() < pain_response_end_time:
            termination_check()
            trial_text["pain"].draw()
            pain_rating.draw()
            win.flip()
            
        current_trial["pain_response"] = pain_rating.getRating()
        pain_rating.reset()

        win.flip()
        wait(trial_iti)
        current_trial["iti"] = trial_iti
        
def webcam_waiting(waittime = 5):
    termination_check()
    global exp_finish
    
    if not webcam_feed.isOpened():
        print("Failed to open webcam.")
        exp_finish = True
        return
    

    waiting_text = visual.TextStim(win,
                        text=instructions_text['experiment_webcam_waiting'],
                        height = 35,
                        pos = webcam_text_pos,
                        wrapWidth= 800
                        )
    ready_text = visual.TextStim(win,
                        text=instructions_text['experiment_webcam_ready'],
                        height = 35,
                        pos = webcam_text_pos,
                        wrapWidth= 800
                        )
    waittimer = core.CountdownTimer(waittime)  
    
    while waittimer.getTime() > 0:
        termination_check()
        # capture each frame of webcam feed in RGB
        ret, webcam_frame = webcam_feed.read() 
        if not ret: #if there is no image returned from webcam_feed.read(), break loop and print error message
            print("failed to capture image")
            exp_finish = True
            break
        
        webcam_frame = cv2.flip(webcam_frame,-1) 
        webcam_frame = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
        ## Normalize the frame to be in the range -1 to 1
        webcam_frame = webcam_frame / 255.0
        webcam_stim = visual.ImageStim(win,
                                       image = webcam_frame,
                                       pos = webcam_stim_pos,
                                       size = webcam_stim_size    
                                       )
        webcam_stim.draw()
        waiting_text.draw()     
        win.flip()
    
    space_pressed = False
        
    while not space_pressed:
        termination_check()
        # capture each frame of webcam feed in RGB
        ret, webcam_frame = webcam_feed.read() 
        if not ret: #if there is no image returned from webcam_feed.read(), break loop and print error message
            print("failed to capture image")
            exp_finish = True
            break
        
        webcam_frame = cv2.flip(webcam_frame,-1) 
        webcam_frame = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
        ## Normalize the frame to be in the range -1 to 1
        webcam_frame = webcam_frame / 255.0
        webcam_stim = visual.ImageStim(win,
                                       image = webcam_frame,
                                       pos = webcam_stim_pos,
                                       size = webcam_stim_size    
                                       )
        webcam_stim.draw()
        ready_text.draw()     
        win.flip()
        # Check for key presses
        keys = event.getKeys()
        if 'space' in keys:
            space_pressed = True
            
def socialmodel_stream(playtime = 5,socialmodel_stim = intro_videos, webcam = True):
    global exp_finish

    sm_timer = core.CountdownTimer(playtime)

    while sm_timer.getTime() > 0: 
        termination_check() 
        #draw webcam stream
        if webcam:
            # capture each frame of webcam feed in RGB
            ret, webcam_frame = webcam_feed.read() 
            if not ret: #if there is no image returned from webcam_feed.read(), break loop and print error message
                print("failed to capture image")
                exp_finish = True
                break
            
            webcam_frame = cv2.flip(webcam_frame,-1) 
            webcam_frame = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
            ## Normalize the frame to be in the range -1 to 1
            webcam_frame = webcam_frame / 255.0
            webcam_stim = visual.ImageStim(win,
                                        image = webcam_frame,
                                        pos = webcam_stim_pos,
                                        size = webcam_stim_size    
                                        )
            webcam_stim.draw()
        
        #draw social model videos
        for video_stim in socialmodel_stim.values():
                video_stim.draw()
                video_stim.play()
                
        win.flip()
    
    # Stop all videos after the playtime
    for video in socialmodel_stim.values():
        video.stop()
    
    win.flip()

exp_finish = None        
lastblocknum = None

# Run experiment
while not exp_finish:
    termination_check()
    
    # ### introduce TENS and run familiarisation procedure
    instruction_trial(instructions_text["welcome"],3)
    instruction_trial(instructions_text["TENS_introduction"],6)
    instruction_trial(instructions_text["familiarisation_1"],10)
    instruction_trial(instructions_text["familiarisation_2"],10)
    
    for trial in trial_order:
        if trial["phase"] == "familiarisation":
            show_fam_trial(trial)
            
    instruction_trial(instructions_text["familiarisation_finish"],2)

    # # run conditioning and extinction phases
    instruction_trial(instructions_text["conditioning"])
        
    #run social modelling manipulation
    webcam_waiting()
    socialmodel_stream(playtime = video_stim_introtime,
                        socialmodel_stim=intro_videos,
                        webcam=True)

    currentblock = 1
    
    for trial in trial_order:
        if trial["phase"] == "conditioning":
            if trial["blocknum"] > currentblock:
                instruction_trial(instructions_text["modelrest"],
                                holdtime = model_rest_time,
                                key = None)
            show_trial(trial,
                trialtype="socialmodel",
                video=trial["model_video_name"])
            currentblock = trial["blocknum"]

    win.flip()
    instruction_trial(instructions_text["experiment_webcam_finish"],3)

    lastblocknum = None

    instruction_trial(instructions_text["extinction"],10)
    for trial in list(filter(lambda trial: trial['phase'] == "extinction", trial_order)):
        current_blocknum = trial['blocknum']
        if lastblocknum is not None and current_blocknum != lastblocknum:
            instruction_trial(instructions_text["blockrest"],10)
        show_trial(trial,"standard")
        lastblocknum = current_blocknum

    if pport != None:
        pport.setData(0)
        
    # save trial data
    save_data(trial_order)
    exit_screen(instructions_text["end"])
    
    exp_finish = True
    
win.close()
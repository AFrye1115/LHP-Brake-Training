# LHP-Brake-Training
A tool to help drivers perfect their braking to achieve faster lap times and reduce wasted time on track

## Required Programs

Mu - https://github.com/patrickmoore/Mu/releases/tag/1.9.5.0

## How To Use

### Drive A Reference Lap

Turn on Telemetry Logging in iRacing and set a lap that you would like to save as the reference lap for all drivers to aim for concerning their braking traces.

### Have Mu convert the IBT File to CSV

Use the Mu program to convert the raw telemetry file to a CSV which will be used to save the reference lap in the format our LHP software needs.

<img src="Images/Screenshot (34).png">

<img src="Images/Screenshot (35).png">

### Use file_dialog.py to save the raw CSV to a reference lap

Run the file named file_dialog.py and select the CSV that was just created.

<img src="Images/Screenshot (36).png">

This will open a lap selector which will allow you to see the brake trace on an x-y graph and a track map. In the top left you can select which lap you would like to assess as well as the lap time associated with the lap. Once you have selected the lap you would like to save, hit the Save button and save the reference in a folder reserved for your reference laps.

<img src="Images/Screenshot (37).png">

<img src="Images/Screenshot (38).png">

### Run GUI.py and select the car and track combo you would like to run

When you are ready to have a driver run some laps and work on their braking, run the file named gui.py and select the Car and Track Combo you are running. Additionally, select the percentage tolerance that a driver can be off of the reference in order for their braking to be acceptable.

## Preferred File Configuration

